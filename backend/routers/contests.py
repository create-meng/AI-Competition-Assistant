"""
竞赛路由 - 竞赛管理、角色跳转
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, timezone
# from bson import ObjectId  # MongoDB 专用，SQLite 不需要

from models.contest import ContestCreate, ContestUpdate, ContestResponse, ContestListResponse
from utils.security import get_current_user
from utils.response import success, error
from database import get_database

router = APIRouter()


@router.post("/check-duplicate", response_model=dict)
async def check_duplicate_contest(
    name: str = Query(..., min_length=1, description="竞赛名称")
):
    """检查是否存在重名或相似名称的竞赛"""
    db = get_database()
    
    # 精确匹配
    exact_matches = []
    cursor = await db.contests.find({}, skip=0, limit=100)
    all_contests = await cursor.to_list(length=100)
    
    for contest in all_contests:
        contest_name = contest.get("name", "")
        # 精确匹配（忽略大小写和空格）
        if contest_name.strip().lower() == name.strip().lower():
            contest["id"] = str(contest.pop("_id"))
            exact_matches.append(contest)
        # 模糊匹配：包含关系或相似度
        elif _is_similar_name(name, contest_name):
            contest["id"] = str(contest.pop("_id"))
            contest["_match_type"] = "similar"
            exact_matches.append(contest)
    
    return success({
        "has_duplicate": len(exact_matches) > 0,
        "matches": exact_matches,
        "count": len(exact_matches)
    })


def _is_similar_name(name1: str, name2: str) -> bool:
    """判断两个竞赛名称是否相似"""
    import re
    
    n1 = name1.strip().lower()
    n2 = name2.strip().lower()
    
    # 完全相同
    if n1 == n2:
        return True
    
    # 去除所有标点符号和空格后比较
    def remove_punctuation(s):
        # 移除中英文标点、空格、破折号等
        return re.sub(r'[——\-\s·•．.,，、;；:：!！?？()（）【】\[\]《》<>""\'\'\"]+', '', s)
    
    n1_clean = remove_punctuation(n1)
    n2_clean = remove_punctuation(n2)
    
    # 去除标点后完全相同
    if n1_clean == n2_clean:
        return True
    
    # 包含关系（用清理后的版本）
    if n1_clean in n2_clean or n2_clean in n1_clean:
        return True
    
    # 原始包含关系
    if n1 in n2 or n2 in n1:
        return True
    
    # 去除年份和届数后比较（如"2024年xxx竞赛" vs "2025年xxx竞赛"，"第十六届" vs "第十五届"）
    def remove_year_and_edition(s):
        s = re.sub(r'\d{4}年?', '', s)  # 去除年份
        s = re.sub(r'第[一二三四五六七八九十百千]+届', '', s)  # 去除中文届数
        s = re.sub(r'第\d+届', '', s)  # 去除数字届数
        return s
    
    n1_no_year = remove_punctuation(remove_year_and_edition(n1))
    n2_no_year = remove_punctuation(remove_year_and_edition(n2))
    if n1_no_year and n2_no_year and n1_no_year == n2_no_year:
        return True
    
    # 计算相似度（Jaccard 相似度，基于字符）
    if len(n1_clean) > 5 and len(n2_clean) > 5:
        set1 = set(n1_clean)
        set2 = set(n2_clean)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        if union > 0 and intersection / union > 0.8:
            return True
    
    # 去除常见前缀后缀比较
    prefixes = ['第', '全国', '中国', '国际']
    suffixes = ['大赛', '竞赛', '比赛', '挑战赛']
    
    def normalize(s):
        for p in prefixes:
            if s.startswith(p):
                s = s[len(p):]
        for sf in suffixes:
            if s.endswith(sf):
                s = s[:-len(sf)]
        return s.strip()
    
    if normalize(n1) and normalize(n2) and normalize(n1) == normalize(n2):
        return True
    
    return False


@router.post("/merge", response_model=dict)
async def merge_contests(
    existing_id: str = Query(..., description="现有竞赛ID"),
    new_data: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """使用AI合并竞赛信息 - 返回预览结果"""
    import os
    from utils.ai_providers.factory import AIProviderFactory
    
    db = get_database()
    
    # 获取现有竞赛
    try:
        existing = await db.contests.find_one({"_id": int(existing_id)})
    except:
        return error("无效的竞赛ID", 400)
    
    if not existing:
        return error("竞赛不存在", 404)
    
    # 准备合并数据
    existing_data = dict(existing)
    existing_data.pop("_id", None)
    
    # 构建AI提示
    merge_prompt = f"""你是一个数据合并助手。请将以下两份竞赛信息合并为一份完整的信息。

合并规则：
1. 优先保留更详细、更完整的信息
2. 如果两边都有值，选择更新、更准确的那个
3. 数组类型的字段（如requirements）应该合并去重
4. 日期字段优先选择更近的截止日期
5. URL字段优先选择有效的链接

现有竞赛信息：
{_format_contest_for_ai(existing_data)}

新提取的信息：
{_format_contest_for_ai(new_data or {})}

请返回合并后的JSON格式数据，只包含以下字段：
- name: 竞赛名称
- organizer: 主办方
- category: 类别
- default_url: 官网
- entrant_url: 参赛者入口
- teacher_url: 教师入口
- deadline: 截止日期（YYYY-MM-DD格式）
- requirements: 参赛要求（数组）
- contact_info: 联系方式
- prize_info: 奖项信息

只返回JSON，不要任何解释。
"""
    
    try:
        # 使用Google AI进行合并（较稳定）
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            # 回退到简单合并
            merged = _simple_merge(existing_data, new_data or {})
        else:
            provider = AIProviderFactory.create_provider(
                provider_type="google",
                api_key=api_key,
                model="gemini-2.0-flash-exp"
            )
            
            response = await provider.extract_from_text(merge_prompt, "")
            
            if response.success and response.data:
                merged = response.data
            else:
                # AI失败，回退到简单合并
                merged = _simple_merge(existing_data, new_data or {})
        
        # 返回预览结果，不直接保存
        return success({
            "merged_data": merged,
            "existing_id": existing_id,
            "existing_data": existing_data,
            "new_data": new_data
        }, "合并预览生成成功")
        
    except Exception as e:
        return error(f"合并失败: {str(e)}", 500)


@router.post("/merge/confirm", response_model=dict)
async def confirm_merge(
    existing_id: str = Query(..., description="现有竞赛ID"),
    merged_data: dict = None,
    current_user: dict = Depends(get_current_user)
):
    """确认并保存合并后的竞赛信息"""
    db = get_database()
    
    try:
        obj_id = int(existing_id)
    except:
        return error("无效的竞赛ID", 400)
    
    # 检查竞赛是否存在
    existing = await db.contests.find_one({"_id": obj_id})
    if not existing:
        return error("竞赛不存在", 404)
    
    # 更新竞赛
    merged_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # 移除不应该更新的字段
    for key in ['_id', 'id', 'created_at']:
        merged_data.pop(key, None)
    
    await db.contests.update_one(
        {"_id": obj_id},
        {"$set": merged_data}
    )
    
    updated = await db.contests.find_one({"_id": obj_id})
    updated["id"] = str(updated.pop("_id"))
    
    return success(updated, "竞赛信息合并保存成功")


def _format_contest_for_ai(data: dict) -> str:
    """格式化竞赛数据供AI阅读"""
    import json
    # 只保留关键字段
    keys = ['name', 'organizer', 'category', 'default_url', 'entrant_url', 
            'teacher_url', 'deadline', 'requirements', 'contact_info', 'prize_info']
    filtered = {k: data.get(k) for k in keys if data.get(k)}
    return json.dumps(filtered, ensure_ascii=False, indent=2)


def _simple_merge(existing: dict, new_data: dict) -> dict:
    """简单合并策略（不使用AI）"""
    result = dict(existing)
    
    for key, new_val in new_data.items():
        if key in ['_id', 'id', 'created_at', 'updated_at']:
            continue
            
        old_val = result.get(key)
        
        # 新值为空，保留旧值
        if not new_val:
            continue
        
        # 旧值为空，使用新值
        if not old_val:
            result[key] = new_val
            continue
        
        # 数组类型，合并去重
        if isinstance(old_val, list) and isinstance(new_val, list):
            merged_list = list(old_val)
            for item in new_val:
                if item not in merged_list:
                    merged_list.append(item)
            result[key] = merged_list
        # 字符串类型，选择更长的
        elif isinstance(old_val, str) and isinstance(new_val, str):
            if len(new_val) > len(old_val):
                result[key] = new_val
        else:
            # 其他情况，优先新值
            result[key] = new_val
    
    return result

@router.get("/", response_model=dict)
async def get_contests(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None
):
    """获取竞赛列表（支持分页、搜索、筛选）"""
    db = get_database()
    
    # 构建查询条件
    query = {}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    # 注意：search 使用 LIKE 查询，在下面单独处理
    
    # 查询数据
    cursor = await db.contests.find(query, skip=skip, limit=limit, search=search, search_field="name")
    contests = await cursor.to_list(length=limit)
    
    # 统计总数时也要考虑搜索条件
    if search:
        total = await db.contests.count_documents(query, search=search, search_field="name")
    else:
        total = await db.contests.count_documents(query)
    
    # 格式化响应
    for contest in contests:
        contest["id"] = str(contest.pop("_id"))
    
    return success({
        "items": contests,
        "total": total,
        "page": skip // limit + 1,
        "size": limit
    })

@router.get("/{contest_id}", response_model=dict)
async def get_contest(contest_id: str):
    """获取竞赛详情"""
    db = get_database()
    
    try:
        contest = await db.contests.find_one({"_id": int(contest_id)})
    except:
        return error("无效的竞赛ID", 400)
    
    if not contest:
        return error("竞赛不存在", 404)
    
    contest["id"] = str(contest.pop("_id"))
    
    return success(contest)

@router.post("/", response_model=dict)
async def create_contest(
    contest: ContestCreate,
    current_user: dict = Depends(get_current_user)
):
    """创建竞赛（需要登录）"""
    db = get_database()
    
    contest_dict = contest.dict()
    contest_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    contest_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    contest_dict["knowledge_graph_id"] = None
    contest_dict["documents"] = []
    
    result = await db.contests.insert_one(contest_dict)
    
    created_contest = await db.contests.find_one({"_id": result.inserted_id})
    created_contest["id"] = str(created_contest.pop("_id"))
    
    return success(created_contest, "竞赛创建成功")

@router.put("/{contest_id}", response_model=dict)
async def update_contest(
    contest_id: str,
    contest: ContestUpdate,
    current_user: dict = Depends(get_current_user)
):
    """更新竞赛"""
    db = get_database()
    
    try:
        obj_id = int(contest_id)
    except:
        return error("无效的竞赛ID", 400)
    
    # 只更新提供的字段
    update_data = {k: v for k, v in contest.dict(exclude_unset=True).items() if v is not None}
    
    if not update_data:
        return error("没有要更新的字段", 400)
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.contests.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        return error("竞赛不存在", 404)
    
    updated_contest = await db.contests.find_one({"_id": obj_id})
    updated_contest["id"] = str(updated_contest.pop("_id"))
    
    return success(updated_contest, "竞赛更新成功")

@router.delete("/{contest_id}", response_model=dict)
async def delete_contest(
    contest_id: str,
    current_user: dict = Depends(get_current_user)
):
    """删除竞赛"""
    db = get_database()
    
    try:
        obj_id = int(contest_id)
    except:
        return error("无效的竞赛ID", 400)
    
    result = await db.contests.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        return error("竞赛不存在", 404)
    
    return success(None, "竞赛删除成功")

@router.get("/{contest_id}/redirect", response_model=dict)
async def redirect_to_official(
    contest_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    核心功能：根据用户角色返回对应的竞赛官网入口URL
    """
    db = get_database()
    
    try:
        contest = await db.contests.find_one({"_id": int(contest_id)})
    except:
        return error("无效的竞赛ID", 400)
    
    if not contest:
        return error("竞赛不存在", 404)
    
    # 根据角色选择URL
    role = current_user["role"]
    
    if role == "entrant":
        url = contest.get("entrant_url") or contest.get("default_url")
    elif role == "teacher":
        url = contest.get("teacher_url") or contest.get("default_url")
    else:
        url = contest.get("default_url")
    
    if not url:
        return error("该竞赛暂未配置跳转链接", 404)
    
    return success({
        "url": url,
        "role": role,
        "contest_name": contest["name"]
    }, "获取跳转链接成功")
