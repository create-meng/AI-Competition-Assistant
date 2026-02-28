"""
数据库连接管理 - SQLite + 内存缓存
任务状态使用内存缓存，确保实时可见
"""
import aiosqlite
import json
from typing import Optional, Any, Dict, List
from datetime import datetime
import os
import copy
from dotenv import load_dotenv

load_dotenv()

_db_path: str = ""
db: Optional["SQLiteDatabase"] = None

# ============================================================
# 内存缓存系统 - 简化版，确保实时同步
# ============================================================
_job_cache: Dict[int, Dict] = {}


def get_job_from_cache(job_id: int) -> Optional[Dict]:
    """从缓存获取任务（返回深拷贝）"""
    if job_id in _job_cache:
        return copy.deepcopy(_job_cache[job_id])
    return None


def set_job_to_cache(job_id: int, job_data: Dict):
    """设置任务到缓存"""
    _job_cache[job_id] = copy.deepcopy(job_data)


def update_job_step_in_cache(job_id: int, step_idx: int, status: str, detail: str = ""):
    """直接更新缓存中任务的步骤状态（专用方法，避免复杂的嵌套更新）"""
    if job_id not in _job_cache:
        return False
    
    job = _job_cache[job_id]
    if "steps" in job and isinstance(job["steps"], list):
        if 0 <= step_idx < len(job["steps"]):
            job["steps"][step_idx]["status"] = status
            job["steps"][step_idx]["detail"] = detail
            job["updated_at"] = datetime.utcnow().isoformat()
            return True
    return False


def update_job_status_in_cache(job_id: int, status: str, **kwargs):
    """直接更新缓存中任务的主状态"""
    if job_id not in _job_cache:
        return False
    
    job = _job_cache[job_id]
    job["status"] = status
    job["updated_at"] = datetime.utcnow().isoformat()
    
    for key, value in kwargs.items():
        job[key] = value
    
    return True


def clear_job_cache():
    """清空任务缓存"""
    _job_cache.clear()


# ============================================================
# SQLite Collection 实现
# ============================================================
class SQLiteCollection:
    """模拟 MongoDB Collection 的 SQLite 实现"""
    
    def __init__(self, db_path: str, collection_name: str):
        self.db_path = db_path
        self.collection_name = collection_name
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """查找单个文档 - ai_jobs 优先从缓存读取"""
        # ai_jobs 表优先从缓存读取
        if self.collection_name == "ai_jobs" and "_id" in filter_dict:
            job_id = int(filter_dict["_id"])
            cached = get_job_from_cache(job_id)
            if cached:
                return cached
        
        # 从数据库读取
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = aiosqlite.Row
            
            conditions = []
            values = []
            for key, value in filter_dict.items():
                if key == "_id":
                    conditions.append("id = ?")
                    values.append(int(value))
                else:
                    conditions.append(f"{key} = ?")
                    values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT * FROM {self.collection_name} WHERE {where_clause} LIMIT 1"
            
            async with conn.execute(query, values) as cursor:
                row = await cursor.fetchone()
                if row:
                    result = self._row_to_dict(row)
                    # 缓存 ai_jobs
                    if self.collection_name == "ai_jobs":
                        set_job_to_cache(result["_id"], result)
                    return result
                return None
    
    async def find(self, filter_dict: Dict[str, Any] = None, sort: List = None, 
                   skip: int = 0, limit: int = 0, search: str = None, search_field: str = None) -> "AsyncCursor":
        """查找多个文档"""
        return AsyncCursor(self, filter_dict or {}, sort, skip, limit, search, search_field)
    
    async def insert_one(self, document: Dict[str, Any]) -> "InsertOneResult":
        """插入单个文档"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            doc = {k: v for k, v in document.items() if k != "_id"}
            
            columns = list(doc.keys())
            placeholders = ["?" for _ in columns]
            values = []
            for v in doc.values():
                if isinstance(v, datetime):
                    values.append(v.isoformat())
                elif isinstance(v, (dict, list)):
                    values.append(json.dumps(v, default=str))
                else:
                    values.append(v)
            
            query = f"INSERT INTO {self.collection_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            async with conn.execute(query, values) as cursor:
                await conn.commit()
                inserted_id = cursor.lastrowid
                
                # ai_jobs 同时写入缓存
                if self.collection_name == "ai_jobs":
                    cached_doc = dict(document)
                    cached_doc["_id"] = inserted_id
                    set_job_to_cache(inserted_id, cached_doc)
                
                return InsertOneResult(inserted_id)
    
    async def update_one(self, filter_dict: Dict[str, Any], update: Dict[str, Any]) -> "UpdateResult":
        """更新单个文档"""
        set_data = update.get("$set", update)
        
        has_nested = any("." in key for key in set_data.keys())
        
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            conn.row_factory = aiosqlite.Row
            
            conditions = []
            where_values = []
            for key, value in filter_dict.items():
                if key == "_id":
                    conditions.append("id = ?")
                    where_values.append(int(value))
                else:
                    conditions.append(f"{key} = ?")
                    where_values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            if has_nested:
                # 嵌套字段更新 - 需要先读取再更新
                query = f"SELECT * FROM {self.collection_name} WHERE {where_clause} LIMIT 1"
                async with conn.execute(query, where_values) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        return UpdateResult(0)
                    doc = self._row_to_dict(row)
                
                # 应用嵌套更新
                for key, value in set_data.items():
                    if "." in key:
                        parts = key.split(".")
                        target = doc
                        for part in parts[:-1]:
                            try:
                                idx = int(part)
                                target = target[idx]
                            except (ValueError, TypeError):
                                target = target.get(part, {})
                        final_key = parts[-1]
                        try:
                            idx = int(final_key)
                            target[idx] = value
                        except ValueError:
                            target[final_key] = value
                    else:
                        doc[key] = value
                
                # 确定需要更新的列
                columns_to_update = set()
                for key in set_data.keys():
                    columns_to_update.add(key.split(".")[0] if "." in key else key)
                
                set_clauses = []
                update_values = []
                for col in columns_to_update:
                    if col in doc and col != "_id":
                        set_clauses.append(f"{col} = ?")
                        val = doc[col]
                        if isinstance(val, datetime):
                            update_values.append(val.isoformat())
                        elif isinstance(val, (dict, list)):
                            update_values.append(json.dumps(val, default=str))
                        else:
                            update_values.append(val)
                
                if set_clauses:
                    update_query = f"UPDATE {self.collection_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
                    async with conn.execute(update_query, update_values + where_values) as cursor:
                        await conn.commit()
                        
                        # 同步更新缓存
                        if self.collection_name == "ai_jobs" and "_id" in filter_dict:
                            job_id = int(filter_dict["_id"])
                            set_job_to_cache(job_id, doc)
                        
                        return UpdateResult(cursor.rowcount)
                return UpdateResult(0)
            else:
                # 简单字段更新
                set_clauses = []
                values = []
                for key, value in set_data.items():
                    if key != "_id":
                        set_clauses.append(f"{key} = ?")
                        if isinstance(value, datetime):
                            values.append(value.isoformat())
                        elif isinstance(value, (dict, list)):
                            values.append(json.dumps(value, default=str))
                        else:
                            values.append(value)
                
                query = f"UPDATE {self.collection_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
                async with conn.execute(query, values + where_values) as cursor:
                    await conn.commit()
                    
                    # 同步更新缓存 - 需要重新读取完整数据
                    if self.collection_name == "ai_jobs" and "_id" in filter_dict:
                        job_id = int(filter_dict["_id"])
                        # 重新读取完整数据到缓存
                        select_query = f"SELECT * FROM {self.collection_name} WHERE id = ?"
                        async with conn.execute(select_query, [job_id]) as select_cursor:
                            row = await select_cursor.fetchone()
                            if row:
                                set_job_to_cache(job_id, self._row_to_dict(row))
                    
                    return UpdateResult(cursor.rowcount)
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> "DeleteResult":
        """删除单个文档"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            conditions = []
            values = []
            for key, value in filter_dict.items():
                if key == "_id":
                    conditions.append("id = ?")
                    values.append(int(value))
                else:
                    conditions.append(f"{key} = ?")
                    values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"DELETE FROM {self.collection_name} WHERE id = (SELECT id FROM {self.collection_name} WHERE {where_clause} LIMIT 1)"
            
            async with conn.execute(query, values) as cursor:
                await conn.commit()
                return DeleteResult(cursor.rowcount)
    
    async def count_documents(self, filter_dict: Dict[str, Any] = None, search: str = None, search_field: str = None) -> int:
        """统计文档数量"""
        async with aiosqlite.connect(self.db_path, timeout=30.0) as conn:
            conditions = []
            values = []
            for key, value in (filter_dict or {}).items():
                if key == "_id":
                    conditions.append("id = ?")
                    values.append(int(value))
                    continue

                if isinstance(value, dict):
                    if "$gte" in value:
                        conditions.append(f"{key} >= ?")
                        values.append(value["$gte"])
                    if "$lte" in value:
                        conditions.append(f"{key} <= ?")
                        values.append(value["$lte"])
                    if "$like" in value:
                        conditions.append(f"{key} LIKE ?")
                        values.append(f"%{value['$like']}%")
                    continue

                conditions.append(f"{key} = ?")
                values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            
            if search and search_field:
                conditions.append(f"{search_field} LIKE ?")
                values.append(f"%{search}%")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"SELECT COUNT(*) FROM {self.collection_name} WHERE {where_clause}"
            
            async with conn.execute(query, values) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典"""
        result = dict(row)
        if "id" in result:
            result["_id"] = result.pop("id")
        for key, value in result.items():
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, (dict, list)):
                        result[key] = parsed
                except (json.JSONDecodeError, TypeError):
                    pass
        return result


class AsyncCursor:
    """模拟 MongoDB 异步游标"""
    
    def __init__(self, collection: SQLiteCollection, filter_dict: Dict, 
                 sort: List = None, skip: int = 0, limit: int = 0,
                 search: str = None, search_field: str = None):
        self.collection = collection
        self.filter_dict = filter_dict
        self._sort = sort
        self._skip = skip
        self._limit = limit
        self._search = search
        self._search_field = search_field
    
    def sort(self, sort_list: List) -> "AsyncCursor":
        self._sort = sort_list
        return self
    
    def skip(self, n: int) -> "AsyncCursor":
        self._skip = n
        return self
    
    def limit(self, n: int) -> "AsyncCursor":
        self._limit = n
        return self
    
    async def to_list(self, length: int = None) -> List[Dict[str, Any]]:
        """转换为列表"""
        async with aiosqlite.connect(self.collection.db_path, timeout=30.0) as conn:
            conn.row_factory = aiosqlite.Row
            
            conditions = []
            values = []
            for key, value in self.filter_dict.items():
                if key == "_id":
                    conditions.append("id = ?")
                    values.append(int(value))
                    continue

                if isinstance(value, dict):
                    if "$gte" in value:
                        conditions.append(f"{key} >= ?")
                        values.append(value["$gte"])
                    if "$lte" in value:
                        conditions.append(f"{key} <= ?")
                        values.append(value["$lte"])
                    if "$like" in value:
                        conditions.append(f"{key} LIKE ?")
                        values.append(f"%{value['$like']}%")
                    continue

                conditions.append(f"{key} = ?")
                values.append(json.dumps(value) if isinstance(value, (dict, list)) else value)
            
            if self._search and self._search_field:
                conditions.append(f"{self._search_field} LIKE ?")
                values.append(f"%{self._search}%")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            order_clause = ""
            if self._sort:
                order_parts = []
                for field, direction in self._sort:
                    if field == "_id":
                        field = "id"
                    order_parts.append(f"{field} {'DESC' if direction == -1 else 'ASC'}")
                order_clause = f" ORDER BY {', '.join(order_parts)}"
            
            limit_clause = ""
            if self._limit or length:
                limit_clause = f" LIMIT {self._limit or length}"
            if self._skip:
                limit_clause += f" OFFSET {self._skip}"
            
            query = f"SELECT * FROM {self.collection.collection_name} WHERE {where_clause}{order_clause}{limit_clause}"
            
            async with conn.execute(query, values) as cursor:
                rows = await cursor.fetchall()
                return [self.collection._row_to_dict(row) for row in rows]


class InsertOneResult:
    def __init__(self, inserted_id: int):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, modified_count: int):
        self.modified_count = modified_count
        self.matched_count = modified_count


class DeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class SQLiteDatabase:
    """模拟 MongoDB Database 的 SQLite 实现"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._collections: Dict[str, SQLiteCollection] = {}
    
    def __getattr__(self, name: str) -> SQLiteCollection:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._collections:
            self._collections[name] = SQLiteCollection(self.db_path, name)
        return self._collections[name]


async def init_db():
    """初始化数据库连接"""
    global _db_path, db
    
    _db_path = os.getenv("SQLITE_DB_PATH", "data/app.db")
    os.makedirs(os.path.dirname(_db_path) if os.path.dirname(_db_path) else ".", exist_ok=True)
    
    try:
        await create_tables()
        db = SQLiteDatabase(_db_path)
        print(f"✅ SQLite 数据库连接成功: {_db_path}")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        db = None
        raise


async def create_tables():
    """创建数据库表"""
    async with aiosqlite.connect(_db_path) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                hashed_password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                school TEXT, real_name TEXT, profile TEXT,
                created_at TEXT, updated_at TEXT, last_login TEXT
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS contests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, organizer TEXT, description TEXT, category TEXT,
                deadline TEXT, status TEXT DEFAULT 'active',
                default_url TEXT, entrant_url TEXT, teacher_url TEXT,
                requirements TEXT, contact_info TEXT, prize_info TEXT, notes TEXT,
                source_url TEXT, source_doc_id INTEGER, extraction_id INTEGER,
                created_by INTEGER, created_at TEXT, updated_at TEXT,
                knowledge_graph_id TEXT, documents TEXT, stages TEXT
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER, filename TEXT, saved_filename TEXT,
                file_path TEXT, file_type TEXT, file_size INTEGER, file_hash TEXT,
                uploaded_by TEXT, uploaded_at TEXT,
                parse_status TEXT DEFAULT 'pending', parsed_text TEXT, parse_error TEXT
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT, source_doc_id INTEGER, source_type TEXT,
                extracted_json TEXT, model TEXT, provider TEXT, prompt_id TEXT,
                extraction_time TEXT, raw_response TEXT, confidence REAL,
                status TEXT, contest_id INTEGER
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, status TEXT DEFAULT 'pending',
                created_at TEXT, updated_at TEXT,
                steps TEXT, request TEXT, result TEXT, error TEXT, context TEXT
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contest_id INTEGER UNIQUE, graph_data TEXT,
                created_at TEXT, updated_at TEXT
            )
        """)
        
        await conn.commit()
        
        # 运行迁移以添加缺失的列
        await run_migrations(conn)
        
        print("✅ 数据库表创建完成")


async def run_migrations(conn):
    """运行数据库迁移，添加缺失的列"""
    # 获取contests表的现有列
    async with conn.execute("PRAGMA table_info(contests)") as cursor:
        columns = await cursor.fetchall()
        existing_columns = {col[1] for col in columns}
    
    # 需要添加的列
    migrations = [
        ("organizer", "TEXT"),
        ("knowledge_graph_id", "TEXT"),
        ("documents", "TEXT"),
        ("stages", "TEXT"),  # 竞赛阶段，JSON格式存储
    ]
    
    for col_name, col_type in migrations:
        if col_name not in existing_columns:
            try:
                await conn.execute(f"ALTER TABLE contests ADD COLUMN {col_name} {col_type}")
                print(f"✅ 已添加列: contests.{col_name}")
            except Exception as e:
                # 列可能已存在
                pass
    
    await conn.commit()


async def close_db():
    """关闭数据库连接"""
    global db
    db = None
    clear_job_cache()
    print("❌ 数据库连接已关闭")


def get_database() -> Optional[SQLiteDatabase]:
    """获取数据库实例"""
    return db
