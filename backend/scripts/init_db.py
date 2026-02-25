"""
数据库初始化脚本 - SQLite 版本
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import os

load_dotenv()

async def init_database():
    """初始化数据库"""
    # 导入数据库模块
    from database import init_db, get_database
    
    db_path = os.getenv("SQLITE_DB_PATH", "data/app.db")
    print(f"🔄 正在初始化 SQLite 数据库: {db_path}")
    
    # 初始化数据库（创建表和索引）
    await init_db()
    
    db = get_database()
    if db is None:
        print("❌ 数据库初始化失败")
        return
    
    # 插入示例数据
    print("\n📊 插入示例数据...")
    
    # 检查是否已有数据
    contest_count = await db.contests.count_documents({})
    
    if contest_count == 0:
        # 插入示例竞赛
        sample_contests = [
            {
                "name": "全国大学生计算机设计大赛",
                "description": "教育部高等学校计算机类专业教学指导委员会主办",
                "category": "计算机",
                "entrant_url": "https://jsjds.blcu.edu.cn/",
                "teacher_url": "https://jsjds.blcu.edu.cn/",
                "default_url": "https://jsjds.blcu.edu.cn/",
                "deadline": "2025-06-30",
                "status": "ongoing",
                "requirements": '["普通高校全日制在读本专科学生", "团队2-5人", "指导教师不超过2人"]',
                "prize_info": "设一、二、三等奖",
                "contact_info": "邮箱: contact@example.com",
                "notes": "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "name": "中国大学生服务外包创新创业大赛",
                "description": "教育部、商务部主办",
                "category": "创业",
                "entrant_url": "http://www.fwwb.org.cn/",
                "teacher_url": "http://www.fwwb.org.cn/",
                "default_url": "http://www.fwwb.org.cn/",
                "deadline": "2025-05-31",
                "status": "upcoming",
                "requirements": '["全日制在校大学生", "团队3-6人"]',
                "prize_info": "一等奖10万元",
                "contact_info": "",
                "notes": "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        
        for contest in sample_contests:
            await db.contests.insert_one(contest)
        print(f"  ✅ 插入了 {len(sample_contests)} 个示例竞赛")
    else:
        print(f"  ℹ️  数据库已有 {contest_count} 个竞赛，跳过示例数据插入")
    
    print("\n✨ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_database())


# ============================================================
# MongoDB 原始代码（已注释，保留备用）
# ============================================================
# """
# 数据库初始化脚本 - MongoDB 版本
# """
# import asyncio
# from motor.motor_asyncio import AsyncIOMotorClient
# from datetime import datetime
# import sys
# from pathlib import Path
#
# sys.path.append(str(Path(__file__).parent.parent))
#
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
#
# async def init_database():
#     mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
#     db_name = os.getenv("MONGODB_DB_NAME", "ai_competition_assistant")
#     
#     client = AsyncIOMotorClient(mongodb_url)
#     db = client[db_name]
#     
#     # 创建索引
#     await db.users.create_index([("username", 1)], unique=True)
#     await db.users.create_index([("email", 1)], unique=True, sparse=True)
#     await db.contests.create_index([("name", 1)])
#     # ... 其他索引
#     
#     client.close()
#
# if __name__ == "__main__":
#     asyncio.run(init_database())
