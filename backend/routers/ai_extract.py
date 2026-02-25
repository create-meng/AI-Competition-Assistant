"""
AI智能提取模块API
"""
import time
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from typing import Optional
from datetime import datetime
from pathlib import Path
import json
import os
import asyncio
import re
from urllib.parse import urlparse

from models.extraction import AIExtractRequest, AIExtractResponse, ProvidersListResponse, ProviderInfo
from utils.ai_providers.factory import AIProviderFactory
from utils.ai_providers.base import AICapability
from utils.ai_providers.health_checker import health_checker
from utils.content_extractor import ContentExtractor
from utils.file_parser import get_file_type, parse_file
from utils.rate_limiter import check_rate_limit
from utils.cache import get_cache, generate_cache_key
from utils.logger import logger
from database import db, get_database

router = APIRouter(tags=["AI提取"]) 


def calculate_confidence(extracted_data: dict) -> float:
    """计算AI提取结果的置信度（更严格的有效性校验与加权）。

    规则：
    - URL 需为有效格式（支持自动补全协议）；
    - deadline 需匹配常见日期格式（YYYY-MM-DD / YYYY/MM/DD / YYYY.MM.DD / 中文日期）；
    - requirements 需为非空列表；
    - contact_info 若包含邮箱或手机号，得满分，否则给半分；
    - prize_info 作为弱字段，存在给少量分；
    - 若 notes 表示不确定/无法提取，则整体下调；
    - 不再给过高的基础分，最低为 0.05（有任意内容时）。
    """
    if not isinstance(extracted_data, dict):
        return 0.05

    def is_valid_url(value: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        # 使用新的规范化函数
        normalized = _normalize_url(value)
        return normalized is not None

    def is_valid_date(value: str) -> bool:
        if not isinstance(value, str) or not value.strip():
            return False
        s = value.strip()
        # 2025-10-06 / 2025/10/06 / 2025.10.06
        if re.match(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$", s):
            return True
        # 2025年10月6日
        if re.match(r"^\d{4}年\d{1,2}月\d{1,2}日$", s):
            return True
        return False

    def has_valid_contact(value: Optional[str]) -> float:
        if not isinstance(value, str):
            return 0.0
        text = value.strip().lower()
        email_ok = re.search(r"[\w\.-]+@[\w\.-]+\.[a-z]{2,}", text) is not None
        phone_ok = re.search(r"1[3-9]\d{9}", text) is not None
        if email_ok or phone_ok:
            return 1.0
        # 可能是 QQ/微信等联系方式，给半分
        if any(k in text for k in ["qq", "wechat", "微信", "联系"]):
            return 0.5
        return 0.0

    weights = {
        "entrant_url": 0.28,
        "teacher_url": 0.22,
        "deadline": 0.20,
        "requirements": 0.15,
        "contact_info": 0.10,
        "prize_info": 0.05,
    }

    score = 0.0
    total = sum(weights.values())

    # entrant_url
    v = extracted_data.get("entrant_url")
    if is_valid_url(v):
        score += weights["entrant_url"]

    # teacher_url
    v = extracted_data.get("teacher_url")
    if is_valid_url(v):
        score += weights["teacher_url"]

    # deadline
    v = extracted_data.get("deadline")
    if is_valid_date(v):
        score += weights["deadline"]

    # requirements
    v = extracted_data.get("requirements")
    if isinstance(v, list) and len([x for x in v if isinstance(x, str) and x.strip()]) > 0:
        score += weights["requirements"]

    # contact_info（按有效性给分）
    v = extracted_data.get("contact_info")
    score += weights["contact_info"] * has_valid_contact(v)

    # prize_info（弱字段存在即给分）
    if extracted_data.get("prize_info"):
        score += weights["prize_info"]

    # notes若有不确定性，整体扣减最多10%
    notes = str(extracted_data.get("notes", "")).lower()
    if any(k in notes for k in ["不确定", "可能", "无法", "不清楚", "空", "null", "n/a"]):
        score *= 0.9

    # 归一化并设置下限
    confidence = max(min(score / total, 1.0), 0.0)
    if confidence == 0.0 and any(extracted_data.values()):
        confidence = 0.05
    return confidence


def _is_http_url(value: Optional[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def _normalize_url(value: Optional[str]) -> Optional[str]:
    """规范化URL，自动补全协议"""
    if not isinstance(value, str) or not value.strip():
        return None
    
    url = value.strip()
    
    # 如果已经有协议，直接验证
    if url.startswith(('http://', 'https://')):
        return url if _is_http_url(url) else None
    
    # 如果没有协议，尝试补全
    if '.' in url and not url.startswith(('mailto:', 'tel:', 'ftp:')):
        # 优先使用 https
        https_url = f"https://{url}"
        if _is_http_url(https_url):
            return https_url
        
        # 如果 https 失败，尝试 http
        http_url = f"http://{url}"
        if _is_http_url(http_url):
            return http_url
    
    return None


def _normalize_date(value: Optional[str]) -> Optional[str]:
    """规范化日期格式，统一转换为 YYYY-MM-DD 格式
    
    支持的输入格式：
    - YYYY-MM-DD (直接返回)
    - YYYY/MM/DD
    - YYYY.MM.DD
    - YYYY年MM月DD日
    - YYYY年MM月 (补充为月末)
    - YYYY-MM (补充为月末)
    - 暂无/null/空值 (返回None)
    """
    if not isinstance(value, str) or not value.strip():
        return None
    
    s = value.strip()
    
    # 跳过无效值
    invalid_values = ['暂无', 'null', 'undefined', 'N/A', 'n/a', '无', '待定', '未定', '-']
    if s in invalid_values or s == '':
        return None
    
    # YYYY-MM-DD 格式，直接返回
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s
    
    # YYYY/MM/DD 格式
    match = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})$', s)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # YYYY.MM.DD 格式
    match = re.match(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', s)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # YYYY年MM月DD日 格式
    match = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日?$', s)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # YYYY年MM月 格式（补充为月末）
    match = re.match(r'^(\d{4})年(\d{1,2})月$', s)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        # 计算该月最后一天
        if month == 12:
            last_day = 31
        else:
            from datetime import date
            next_month = date(year, month + 1, 1)
            last_day = (next_month - date(year, month, 1)).days
        return f"{year}-{str(month).zfill(2)}-{str(last_day).zfill(2)}"
    
    # YYYY-MM 格式（补充为月末）
    match = re.match(r'^(\d{4})-(\d{1,2})$', s)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        if month == 12:
            last_day = 31
        else:
            from datetime import date
            next_month = date(year, month + 1, 1)
            last_day = (next_month - date(year, month, 1)).days
        return f"{year}-{str(month).zfill(2)}-{str(last_day).zfill(2)}"
    
    # 尝试通用解析
    try:
        from datetime import datetime as dt
        # 尝试多种格式
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%d/%m/%Y', '%m/%d/%Y']:
            try:
                parsed = dt.strptime(s, fmt)
                return parsed.strftime('%Y-%m-%d')
            except ValueError:
                continue
    except Exception:
        pass
    
    # 无法解析，返回原值（让前端处理）
    return s


def _normalize_contact_info(value: Optional[str]) -> Optional[str]:
    """规范化联系方式，智能分割成分号分隔的格式
    
    支持的分割模式：
    - 已有分隔符：; ； , ，
    - 换行符
    - 联系人标识：联系人、联系电话、邮箱、QQ、微信等
    - 电话号码边界
    - 邮箱边界
    """
    if not value or not isinstance(value, str):
        return value
    
    s = value.strip()
    if not s:
        return None
    
    # 如果已经是分号分隔的格式，直接清理返回
    if ';' in s or '；' in s:
        parts = re.split(r'[;；]', s)
        cleaned = [p.strip() for p in parts if p.strip()]
        return '; '.join(cleaned) if cleaned else None
    
    # 按换行分割
    if '\n' in s:
        parts = s.split('\n')
        cleaned = [p.strip() for p in parts if p.strip()]
        if len(cleaned) > 1:
            return '; '.join(cleaned)
    
    # 按逗号分割（但要小心不要分割数字中的逗号）
    if ',' in s or '，' in s:
        # 检查是否是简单的逗号分隔列表
        parts = re.split(r'[,，]', s)
        # 如果分割后每部分都有实质内容（不只是数字），则认为是有效分割
        valid_parts = []
        for p in parts:
            p = p.strip()
            if p and not re.match(r'^\d+$', p):  # 不是纯数字
                valid_parts.append(p)
        if len(valid_parts) > 1:
            return '; '.join(valid_parts)
    
    # 尝试按联系人标识分割
    # 匹配模式：联系人/联系电话/邮箱/QQ/微信/官方邮箱/大赛邮箱 等
    contact_patterns = [
        r'(联系人[：:]\s*\S+)',
        r'(联系电话[：:]\s*[\d\-\s]+)',
        r'(电话[：:]\s*[\d\-\s]+)',
        r'(邮箱[：:]\s*\S+@\S+)',
        r'(官方邮箱[：:]\s*\S+@\S+)',
        r'(大赛.*?邮箱[：:]\s*\S+@\S+)',
        r'(QQ[群]?[：:]\s*\d+)',
        r'(微信[：:]\s*\S+)',
    ]
    
    # 尝试提取各类联系方式
    extracted = []
    remaining = s
    
    # 提取电话号码（11位手机号或带区号的座机）
    phone_pattern = r'(\d{11}|\d{3,4}[-\s]?\d{7,8})'
    phones = re.findall(phone_pattern, s)
    
    # 提取邮箱
    email_pattern = r'([\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,})'
    emails = re.findall(email_pattern, s)
    
    # 提取QQ号/QQ群
    qq_pattern = r'QQ[群]?[：:\s]*(\d{5,12})'
    qqs = re.findall(qq_pattern, s, re.IGNORECASE)
    
    # 如果能提取到多种联系方式，尝试智能分割
    if len(phones) + len(emails) + len(qqs) > 1:
        # 按联系人名字+联系方式的模式分割
        # 例如：黄守明 18256267893, 赵露露 18756970137
        name_phone_pattern = r'([^\d\s,，;；]{2,5})\s*(\d{11})'
        name_phone_matches = re.findall(name_phone_pattern, s)
        
        if name_phone_matches:
            parts = []
            for name, phone in name_phone_matches:
                parts.append(f"{name.strip()} {phone}")
            
            # 添加邮箱
            for email in emails:
                # 检查邮箱前是否有标识
                email_with_label = re.search(rf'([\u4e00-\u9fa5]*邮箱[：:]\s*)?{re.escape(email)}', s)
                if email_with_label and email_with_label.group(1):
                    parts.append(f"{email_with_label.group(1).strip()}{email}")
                else:
                    parts.append(f"邮箱: {email}")
            
            # 添加QQ
            for qq in qqs:
                qq_with_label = re.search(rf'(QQ[群]?[：:]\s*){qq}', s, re.IGNORECASE)
                if qq_with_label:
                    parts.append(f"{qq_with_label.group(0)}")
                else:
                    parts.append(f"QQ: {qq}")
            
            if parts:
                return '; '.join(parts)
    
    # 如果无法智能分割，返回原值
    return s


def _normalize_extracted_urls(data: dict, source_url: Optional[str]) -> dict:
    """规范化与兜底 URL 字段：default_url / entrant_url / teacher_url

    规则：
    - 支持AI v3嵌套结构（contest.entrant_url等）和扁平结构
    - 自动补全协议（优先 https）；
    - 若三者之一有效，其余缺失则回填为该 URL；
    - 若三者均缺失而来源是 URL，则统一使用来源 URL；
    - 不从 contact_info 中推断官网，避免把联系方式当官网；
    - 在 notes 中追加说明兜底逻辑。
    - 返回展平后的数据结构，方便前端使用
    """
    data = dict(data or {})
    
    # 处理AI v3嵌套结构
    contest = data.get("contest", {}) if isinstance(data.get("contest"), dict) else {}
    dates = data.get("dates", {}) if isinstance(data.get("dates"), dict) else {}
    evaluation = data.get("evaluation", {}) if isinstance(data.get("evaluation"), dict) else {}
    contact = data.get("contact", {}) if isinstance(data.get("contact"), dict) else {}
    computed = data.get("computed", {}) if isinstance(data.get("computed"), dict) else {}

    # 从嵌套结构或扁平结构获取URL
    entrant_url = _normalize_url(contest.get("entrant_url") or data.get("entrant_url"))
    teacher_url = _normalize_url(contest.get("teacher_url") or data.get("teacher_url"))
    default_url = _normalize_url(contest.get("default_url") or data.get("default_url"))

    valid_urls = [u for u in [default_url, entrant_url, teacher_url] if u is not None]
    primary_url = valid_urls[0] if valid_urls else _normalize_url(source_url)

    # 回填逻辑
    notes_appends: list[str] = []
    if not (default_url and entrant_url and teacher_url):
        if primary_url:
            if not default_url:
                default_url = primary_url
            if not entrant_url:
                entrant_url = primary_url
            if not teacher_url:
                teacher_url = primary_url
            notes_appends.append(f"未分别提取到独立入口，已将默认官网/参赛入口/教师入口统一为: {primary_url}")
        else:
            notes_appends.append("未能识别任何有效的官方网站URL")

    # 获取联系方式并规范化
    raw_contact = contact.get("contact_info") or data.get("contact_info")
    contact_info = _normalize_contact_info(raw_contact)
    
    # 获取奖项信息
    prize_info = evaluation.get("prize_info") or data.get("prize_info")
    
    # 获取截止日期并规范化格式
    raw_deadline = dates.get("deadline") or data.get("deadline")
    deadline = _normalize_date(raw_deadline)
    
    # 获取竞赛名称和主办方
    name = contest.get("name") or data.get("name")
    organizer = contest.get("organizer") or data.get("organizer")
    
    # 处理参赛要求 - 合并嵌套结构中的各类要求
    requirements = []
    raw_requirements = data.get("requirements")
    
    if isinstance(raw_requirements, list):
        # 直接是数组格式（AI v4扁平格式）
        requirements = [r for r in raw_requirements if isinstance(r, str) and r.strip()]
    elif isinstance(raw_requirements, dict):
        # AI v3嵌套格式: requirements: { eligibility: [], technical: [], compliance: [] }
        if raw_requirements.get("eligibility"):
            requirements.extend([r for r in raw_requirements["eligibility"] if isinstance(r, str)])
        if raw_requirements.get("technical"):
            requirements.extend([r for r in raw_requirements["technical"] if isinstance(r, str)])
        if raw_requirements.get("compliance"):
            requirements.extend([r for r in raw_requirements["compliance"] if isinstance(r, str)])
    elif isinstance(raw_requirements, str) and raw_requirements.strip():
        # 字符串格式，按逗号分割
        requirements = [r.strip() for r in raw_requirements.split(',') if r.strip()]
    
    # 获取notes
    existing_notes = computed.get("notes") or data.get("notes") or ""
    if notes_appends:
        combined_notes = "；".join([x for x in [existing_notes] if x] + notes_appends)
    else:
        combined_notes = existing_notes

    # 返回展平后的数据结构，同时保留原始嵌套结构供参考
    result = {
        # 展平的字段（前端直接使用）
        "name": name,
        "organizer": organizer,
        "default_url": default_url,
        "entrant_url": entrant_url,
        "teacher_url": teacher_url,
        "deadline": deadline,
        "requirements": requirements,
        "contact_info": contact_info,
        "prize_info": prize_info,
        "notes": combined_notes,
        # v4新增字段（扁平结构直接获取，日期字段规范化）
        "category": contest.get("category") or data.get("category"),
        "publish_time": _normalize_date(dates.get("publish_time") or data.get("publish_time")),
        "start_date": _normalize_date(dates.get("start_date") or data.get("start_date")),
        "team_min": data.get("team_min") or (data.get("submission", {}) or {}).get("team_limits", {}).get("min_members"),
        "team_max": data.get("team_max") or (data.get("submission", {}) or {}).get("team_limits", {}).get("max_members"),
        # 保留原始嵌套结构（供高级用途）
        "contest": contest,
        "dates": dates,
        "submission": data.get("submission"),
        "evaluation": evaluation,
        "contact": contact,
        "computed": computed
    }
    
    return result


def load_prompt(prompt_name: str) -> str:
    """加载prompt模板"""
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.txt"
    
    if not prompt_file.exists():
        raise HTTPException(status_code=404, detail=f"Prompt模板不存在: {prompt_name}")
    
    return prompt_file.read_text(encoding='utf-8')


@router.get("/providers", response_model=ProvidersListResponse)
async def get_providers():
    """获取所有可用的AI提供商列表，包含健康状态"""
    try:
        # 获取基础提供商信息（已隐藏 suanli，仅保留 free_qwq）
        base_providers = AIProviderFactory.get_available_providers()
        
        # 检查所有提供商的健康状态，设置总体超时
        try:
            health_results = await asyncio.wait_for(
                health_checker.check_all_providers(),
                timeout=60.0  # 60秒总体超时，给更多时间
            )
        except asyncio.TimeoutError:
            # 如果健康检查超时，返回基础信息
            health_results = {}
        
        # 合并基础信息和健康状态
        enhanced_providers = []
        for provider in base_providers:
            provider_type = provider["type"]
            health = health_results.get(provider_type, {})
            
            enhanced_provider = {
                **provider,
                "status": health.get("status", "unknown"),
                "reason": health.get("reason", ""),
                "available_models": health.get("available_models", [provider.get("default_model", "")]),
                "last_check": health.get("last_check", ""),
                "response_time": health.get("response_time", 0)
            }
            
            enhanced_providers.append(enhanced_provider)
        
        provider_infos = [ProviderInfo(**p) for p in enhanced_providers]
        
        return ProvidersListResponse(
            data=provider_infos
        )
        
    except Exception as e:
        # 如果出现任何错误，返回基础提供商信息
        base_providers = AIProviderFactory.get_available_providers()
        provider_infos = [ProviderInfo(**p) for p in base_providers]
        
        return ProvidersListResponse(
            data=provider_infos
        )


@router.get("/providers/stream")
async def get_providers_stream():
    """
    流式获取AI提供商健康检查进度
    使用Server-Sent Events (SSE) 实时推送进度
    """
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate_progress():
        # 获取基础提供商信息
        base_providers = AIProviderFactory.get_available_providers()
        total_count = len(base_providers)
        
        # 创建进度跟踪
        progress_data = {
            "current": 0,
            "total": total_count,
            "available": 0,
            "providers": []
        }
        
        # 发送初始状态
        yield f"data: {json.dumps(progress_data)}\n\n"
        
        # 使用队列来收集进度更新
        import asyncio
        progress_queue = asyncio.Queue()
        
        # 定义进度回调函数
        def progress_callback(current, total, available):
            asyncio.create_task(progress_queue.put({
                "current": current,
                "total": total,
                "available": available
            }))
        
        # 启动健康检查任务
        health_task = asyncio.create_task(
            health_checker.check_all_providers(progress_callback=progress_callback)
        )
        
        # 处理进度更新
        while not health_task.done():
            try:
                # 等待进度更新或健康检查完成
                progress_update = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                progress_data.update(progress_update)
                yield f"data: {json.dumps(progress_data)}\n\n"
            except asyncio.TimeoutError:
                # 没有新的进度更新，继续等待
                continue
        
        # 等待健康检查完成
        try:
            health_results = await health_task
        except asyncio.TimeoutError:
            health_results = {}
        
        # 合并最终结果
        enhanced_providers = []
        for provider in base_providers:
            provider_type = provider["type"]
            health = health_results.get(provider_type, {})
            
            enhanced_provider = {
                **provider,
                "status": health.get("status", "unknown"),
                "reason": health.get("reason", ""),
                "available_models": health.get("available_models", [provider.get("default_model", "")]),
                "last_check": health.get("last_check", ""),
                "response_time": health.get("response_time", 0)
            }
            
            enhanced_providers.append(enhanced_provider)
        
        # 发送最终结果
        final_data = {
            "current": total_count,
            "total": total_count,
            "available": len([p for p in enhanced_providers if p["status"] == "available"]),
            "providers": enhanced_providers,
            "completed": True
        }
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )


@router.post("/extract")
async def extract_information(request: AIExtractRequest, http_request: Request):
    """
    AI智能提取信息
    
    根据来源类型（URL/文件/文本）使用AI提取关键信息
    """
    start_time = time.time()
    
    # 速率限制检查
    await check_rate_limit(http_request, "ai_extract")
    
    # 尝试从缓存获取结果
    cache = get_cache()
    cache_key = f"ai_extract:{generate_cache_key(request.source_url, request.file_id, request.source_text, request.provider, request.model)}"
    
    cached_result = await cache.get(cache_key)
    if cached_result:
        logger.cache_event("hit", cache_key, hit=True)
        cached_result["data"]["from_cache"] = True
        return cached_result
    
    try:
        # 获取API密钥（从环境变量或数据库）
        provider_key_map = {
            "cloudflare": "CLOUDFLARE_API_KEY",
            "google": "GOOGLE_API_KEY", 
            "doubao": "DOUBAO_API_KEY",
            "free_qwq": "FREE_QWQ_API_KEY",
            "suanli": "SUANLI_API_KEY",
            "cerebras": "CEREBRAS_API_KEY"
        }
        
        env_key = provider_key_map.get(request.provider)
        if not env_key:
            return {
                "status": "error",
                "code": 400,
                "message": f"不支持的AI提供商: {request.provider}",
                "data": None
            }
        
        api_key = os.getenv(env_key)
        # suanli 与 free_qwq 复用同一 API 时的密钥兜底
        if not api_key and request.provider == "suanli":
            api_key = os.getenv("FREE_QWQ_API_KEY") or os.getenv("FREE_QWQ_QPI_KEY")
        if not api_key and request.provider == "free_qwq":
            api_key = os.getenv("SUANLI_API_KEY") or os.getenv("FREE_QWQ_QPI_KEY")
        # 用户特别提供的 FREE_QWQ_QPI_KEY（拼写按用户给定）
        if not api_key and request.provider in ("free_qwq", "suanli"):
            api_key = os.getenv("FREE_QWQ_QPI_KEY")
        if not api_key:
            return {
                "status": "error",
                "code": 400,
                "message": f"未配置{request.provider}的API密钥",
                "data": None
            }
        
        # 创建AI提供商实例
        kwargs = {}
        if request.provider == "cloudflare":
            account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
            if not account_id:
                return {
                    "status": "error",
                    "code": 400,
                    "message": "未配置Cloudflare Account ID",
                    "data": None
                }
            kwargs["account_id"] = account_id
        
        provider = AIProviderFactory.create_provider(
            provider_type=request.provider,
            api_key=api_key,
            model=request.model,
            **kwargs
        )
        
        # 加载prompt模板，并将SOURCE_TYPE/BASE_URL/PUBLISH_META注入到提示词头部
        prompt_base = load_prompt(request.prompt_template)
        # 构造上下文前缀，便于不同提供商也能“看到”额外输入
        context_prefix = {
            "SOURCE_TYPE": request.source_type,
            "BASE_URL": None,
            "PUBLISH_META": None
        }
        # URL 场景作为 BASE_URL 传入
        if request.source_type == "url" and isinstance(request.source_content, str):
            context_prefix["BASE_URL"] = request.source_content
        # 文件/文本的 PUBLISH_META 暂缺，这里先保留空位（后续可从 documents/HTTP 头注入）
        prompt = (
            "[CONTEXT]\n" + json.dumps(context_prefix, ensure_ascii=False) + "\n[/CONTEXT]\n\n" + prompt_base
        )
        
        # 获取数据库连接（后续会多次使用）
        database = get_database()
        if database is None:
            return {
                "status": "error",
                "code": 500,
                "message": "数据库连接失败，请稍后重试",
                "data": None
            }
        
        # 混合来源：将 URL 抓取文本 + 文件解析文本 + 纯文本 合并后送入AI
        fetched_parts: list[str] = []
        source_url = None
        source_doc_id = None

        # 兼容：当 source_type 为 auto/mixed 时，同时读取新字段与旧字段
        input_url = request.source_url or (request.source_content if request.source_type in ("url", "auto", "mixed") else None)
        input_text = request.source_text or (request.source_content if request.source_type in ("text", "auto", "mixed") else None)

        # 1) URL → 深度抓取
        if input_url and str(input_url).strip():
            u = str(input_url).strip()
            if not (u.startswith("http://") or u.startswith("https://")):
                return {
                    "status": "error",
                    "code": 400,
                    "message": "URL必须以 http:// 或 https:// 开头",
                    "data": None
                }
            source_url = u
            deep = await ContentExtractor.extract_from_url_deep(u)
            if deep.get("success") and deep.get("content"):
                fetched_parts.append(deep["content"])
            else:
                shallow = await ContentExtractor.extract_from_url(u)
                if shallow.get("success") and shallow.get("content"):
                    fetched_parts.append(shallow["content"])

        # 2) 文件 → 本地解析
        if request.file_id:
            doc = await database.documents.find_one({"_id": int(request.file_id)})
            if not doc:
                return {
                    "status": "error",
                    "code": 404,
                    "message": "文件不存在",
                    "data": None
                }
            file_path = doc.get("file_path")
            file_type = get_file_type(file_path)
            try:
                # 使用文件解析器解析文件
                parse_result = parse_file(file_path, file_type)
                if not parse_result.get("success", False):
                    return {
                        "status": "error",
                        "code": 400,
                        "message": f"文件解析失败: {parse_result.get('error', '未知错误')}",
                        "data": None
                    }
                
                # 构造与原有代码兼容的结果格式
                fres = {
                    "success": True,
                    "content": parse_result.get("content", ""),
                    "file_path": file_path,
                    "method": "file_parser"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "code": 400,
                    "message": f"文件解析失败: {str(e)}",
                    "data": None
                }
            if fres.get("success") and fres.get("content"):
                fetched_parts.append(fres["content"])
                source_doc_id = request.file_id

        # 3) 文本 → 直接拼接
        if input_text and str(input_text).strip():
            fetched_parts.append(str(input_text).strip())

        # 合并
        merged_text = "\n\n".join([p for p in fetched_parts if isinstance(p, str) and p.strip()])
        if not merged_text.strip():
            return {
                "status": "error",
                "code": 400,
                "message": "未提供有效的URL/文件/文本内容",
                "data": None
            }

        response = await provider.extract_from_text(merged_text, prompt)
        
        # 检查AI响应
        if not response.success:
            # AI调用失败，返回错误信息
            return {
                "status": "error",
                "code": 400,
                "message": response.error,
                "data": {
                    "provider": response.provider,
                    "model": response.model,
                    "raw_response": response.raw_response,
                    "error": response.error
                }
            }
        
        # 二次兜底：结构与字段规范化
        if isinstance(response.data, dict):
            key_fields = [
                'entrant_url', 'teacher_url', 'deadline',
                'requirements', 'contact_info', 'prize_info'
            ]
            all_empty = True
            for k in key_fields:
                v = response.data.get(k)
                if (isinstance(v, list) and len(v) > 0) or (isinstance(v, str) and v.strip()) or (v not in [None, "", []]):
                    all_empty = False
                    break
            if all_empty:
                # 不报错，但将 notes 标明输入为空导致
                response.data.setdefault('notes', '输入为空或无法提取到有效文本')

            # URL 规范化与兜底（默认三入口相同）
            response.data = _normalize_extracted_urls(
                response.data,
                source_url if request.source_type == "url" else None
            )
        
        # 保存提取结果到数据库
        extraction_record = {
            "source_url": source_url,
            "source_doc_id": source_doc_id,
            "source_type": request.source_type,
            "extracted_json": response.data,
            "model": response.model,
            "provider": response.provider,
            "prompt_id": request.prompt_template,
            "extraction_time": datetime.utcnow().isoformat(),
            "raw_response": response.raw_response,
            "confidence": calculate_confidence(response.data) if isinstance(response.data, dict) else 0.5,
            "status": "success"
        }
        
        result = await database.ai_extractions.insert_one(extraction_record)
        extraction_id = str(result.inserted_id)
        
        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录日志
        logger.ai_extraction(
            provider=response.provider,
            model=response.model,
            source_type=request.source_type,
            success=True,
            duration_ms=duration_ms,
            confidence=extraction_record["confidence"]
        )
        
        # 返回成功响应（使用规范化后的数据）
        success_response = {
            "status": "success",
            "code": 200,
            "message": "提取成功",
            "data": {
                "extraction_id": extraction_id,
                "extracted_json": response.data,  # 这里已经是规范化后的数据
                "raw_response": response.raw_response,
                "provider": response.provider,
                "model": response.model,
                "confidence": extraction_record["confidence"],
                "source_url": source_url,
                "source_doc_id": source_doc_id,
                "source_type": request.source_type,
                "extraction_time": extraction_record["extraction_time"].isoformat(),
                "status": "success",
                "from_cache": False
            }
        }
        
        # 缓存结果（5分钟）
        await cache.set(cache_key, success_response, ttl=300)
        logger.cache_event("set", cache_key)
        
        return success_response
        
    except ValueError as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.ai_extraction(
            provider=request.provider,
            model=request.model or "unknown",
            source_type=request.source_type,
            success=False,
            duration_ms=duration_ms,
            error=str(e)
        )
        return {
            "status": "error",
            "code": 400,
            "message": str(e),
            "data": None
        }


@router.post("/extract/job")
async def start_extraction_job(request: AIExtractRequest, background_tasks: BackgroundTasks):
    """
    启动异步任务式AI提取，返回job_id，前端可轮询进度。
    进度步骤：fetch → parse → ai → save
    """
    import traceback
    print("=" * 50)
    print("🚀 [start_extraction_job] 收到请求")
    print(f"📦 请求数据: {request}")
    
    try:
        print("📡 正在获取数据库连接...")
        database = get_database()
        if database is None:
            print("❌ 数据库连接失败")
            return {
                "status": "error",
                "code": 500,
                "message": "数据库连接失败，请稍后重试",
                "data": None
            }
        print("✅ 数据库连接成功")

        # 初始化job记录
        print("📝 正在构建 job_doc...")
        job_doc = {
            "type": "ai_extraction",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "steps": [
                {"name": "fetch", "status": "pending", "detail": ""},
                {"name": "parse", "status": "pending", "detail": ""},
                {"name": "ai", "status": "pending", "detail": ""},
                {"name": "save", "status": "pending", "detail": ""}
            ],
            "request": request.model_dump()
        }
        print(f"📄 job_doc 构建完成: {job_doc}")
        
        print("💾 正在插入数据库...")
        result = await database.ai_jobs.insert_one(job_doc)
        job_id = str(result.inserted_id)
        print(f"✅ 插入成功, job_id: {job_id}")

        # 启动后台任务
        print("🔄 正在启动后台任务...")
        background_tasks.add_task(_run_extraction_job, job_id)
        print("✅ 后台任务已启动")

        response = {
            "status": "success",
            "code": 200,
            "message": "任务已启动",
            "data": {"job_id": job_id}
        }
        print(f"📤 返回响应: {response}")
        print("=" * 50)
        return response
    except Exception as e:
        print(f"❌ 异常发生: {type(e).__name__}: {str(e)}")
        print(f"📜 堆栈跟踪:\n{traceback.format_exc()}")
        print("=" * 50)
        return {
            "status": "error",
            "code": 500,
            "message": f"任务启动失败: {str(e)}",
            "data": None
        }


async def _run_extraction_job(job_id: str):
    """后台执行提取任务，分步更新进度。"""
    import traceback
    from database import update_job_step_in_cache, update_job_status_in_cache, get_job_from_cache, set_job_to_cache
    
    print(f"\n{'='*50}")
    print(f"🔄 [_run_extraction_job] 开始执行任务: {job_id}")
    
    database = get_database()
    if database is None:
        print("❌ 数据库连接失败")
        return
    
    job_id_int = int(job_id)

    async def _set_step(idx: int, status: str, detail: str = ""):
        """更新步骤状态 - 同时更新缓存和数据库"""
        # 1. 先更新内存缓存（立即生效）
        cache_updated = update_job_step_in_cache(job_id_int, idx, status, detail)
        print(f"📊 [_set_step] 步骤 {idx}: {status} - {detail} (缓存更新: {cache_updated})")
        
        # 2. 异步更新数据库（持久化）
        await database.ai_jobs.update_one(
            {"_id": job_id_int},
            {"$set": {f"steps.{idx}.status": status, f"steps.{idx}.detail": detail, "updated_at": datetime.utcnow().isoformat()}}
        )
    
    async def _set_job_status(status: str, **kwargs):
        """更新任务主状态 - 同时更新缓存和数据库"""
        # 1. 先更新内存缓存
        cache_updated = update_job_status_in_cache(job_id_int, status, **kwargs)
        print(f"📊 [_set_job_status] 状态: {status} (缓存更新: {cache_updated})")
        
        # 2. 异步更新数据库
        update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
        update_data.update(kwargs)
        await database.ai_jobs.update_one(
            {"_id": job_id_int},
            {"$set": update_data}
        )

    try:
        # 读取请求
        job = await database.ai_jobs.find_one({"_id": int(job_id)})
        if not job:
            print(f"❌ 找不到任务: {job_id}")
            return
        payload = job.get("request", {})
        print(f"📦 任务请求数据: {payload}")

        # 构造AI提供商
        provider_key_map = {
            "cloudflare": "CLOUDFLARE_API_KEY",
            "google": "GOOGLE_API_KEY",
            "doubao": "DOUBAO_API_KEY",
            "free_qwq": "FREE_QWQ_API_KEY",
            "suanli": "SUANLI_API_KEY",
            "cerebras": "CEREBRAS_API_KEY"
        }
        provider_type = str(payload.get("provider") or "").lower() or "google"
        env_key = provider_key_map.get(provider_type)
        api_key = os.getenv(env_key) if env_key else None
        if not api_key and provider_type == "suanli":
            api_key = os.getenv("FREE_QWQ_API_KEY") or os.getenv("FREE_QWQ_QPI_KEY")
        if not api_key and provider_type == "free_qwq":
            api_key = os.getenv("SUANLI_API_KEY") or os.getenv("FREE_QWQ_QPI_KEY")
        if not api_key and provider_type in ("free_qwq", "suanli"):
            api_key = os.getenv("FREE_QWQ_QPI_KEY")

        kwargs = {}
        if provider_type == "cloudflare":
            account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
            if account_id:
                kwargs["account_id"] = account_id

        provider = AIProviderFactory.create_provider(
            provider_type=provider_type,
            api_key=api_key,
            model=payload.get("model"),
            **kwargs
        )

        # 加载prompt
        prompt_base = load_prompt(payload.get("prompt_template", "unified_extraction_v4"))
        context_prefix = {
            "SOURCE_TYPE": "mixed",
            "BASE_URL": payload.get("source_url"),
            "PUBLISH_META": None
        }
        prompt = (
            "[CONTEXT]\n" + json.dumps(context_prefix, ensure_ascii=False) + "\n[/CONTEXT]\n\n" + prompt_base
        )

        # Step 0: 标记为运行中
        await _set_job_status("running")

        # Step 1: fetch（混合来源合并）
        await _set_step(0, "running", "正在抓取与汇总网页/文档/文本内容…")
        fetched_parts: list[str] = []
        source_url = None
        source_doc_id = None
        
        # 保存解析内容用于前端查看
        url_content = None
        file_content = None
        
        # 标记是否使用AI直接读取URL（跳过本地解析）
        use_ai_web_reading = False

        # 获取输入内容
        input_url = payload.get("source_url") or payload.get("source_content")
        input_text = payload.get("source_text") or (payload.get("source_content") if (not payload.get("source_url") and not payload.get("file_id")) else None)
        input_file_id = payload.get("file_id")

        # URL处理 - 优先让AI直接读取（如果支持）
        if input_url and str(input_url).strip():
            u = str(input_url).strip()
            source_url = u
            
            # 检查AI是否支持直接读取网页
            if provider.supports_capability(AICapability.WEB_READING):
                # AI支持网页阅读，直接让AI读取，不做本地解析
                await _set_step(0, "running", f"AI支持网页阅读，将直接让AI分析URL…")
                use_ai_web_reading = True
                print(f"🌐 AI支持网页阅读，跳过本地解析，直接让AI读取: {u}")
            else:
                # AI不支持网页阅读，使用本地解析
                await _set_step(0, "running", "AI不支持网页阅读，正在本地解析URL…")
                deep = await ContentExtractor.extract_from_url_deep(u)
                
                # 详细调试信息
                print(f"\n🔍 Deep提取结果调试:")
                print(f"  - success: {deep.get('success')}")
                print(f"  - method: {deep.get('method', 'N/A')}")
                print(f"  - content存在: {'content' in deep}")
                print(f"  - content长度: {len(deep.get('content', ''))}")
                print(f"  - error: {deep.get('error', 'N/A')}")
                print(f"  - 所有键: {list(deep.keys())}")
                
                if deep.get("success") and deep.get("content"):
                    url_content = deep["content"]
                    fetched_parts.append(url_content)
                    print(f"✅ Deep提取成功，内容已添加到fetched_parts")
                    await _set_step(0, "running", f"本地解析成功 ({deep.get('method', 'unknown')}方式，{len(url_content)}字符)")
                else:
                    print(f"⚠️ Deep提取失败或无内容，尝试shallow")
                    shallow = await ContentExtractor.extract_from_url(u)
                    
                    print(f"\n🔍 Shallow提取结果调试:")
                    print(f"  - success: {shallow.get('success')}")
                    print(f"  - method: {shallow.get('method', 'N/A')}")
                    print(f"  - content存在: {'content' in shallow}")
                    print(f"  - content长度: {len(shallow.get('content', ''))}")
                    print(f"  - error: {shallow.get('error', 'N/A')}")
                    
                    if shallow.get("success") and shallow.get("content"):
                        url_content = shallow["content"]
                        fetched_parts.append(url_content)
                        print(f"✅ Shallow提取成功，内容已添加到fetched_parts")
                        await _set_step(0, "running", f"本地解析成功 ({shallow.get('method', 'unknown')}方式，{len(url_content)}字符)")
                    else:
                        print(f"❌ 本地解析失败")
                        await _set_step(0, "running", "本地解析URL失败，将继续处理其他内容")
                
                # 检查URL抓取内容是否过少（小于200字符视为抓取失败）
                MIN_URL_CONTENT_LENGTH = 200
                if url_content and len(url_content) < MIN_URL_CONTENT_LENGTH:
                    print(f"⚠️ URL抓取内容过少: {len(url_content)}字符 < {MIN_URL_CONTENT_LENGTH}字符")
                    # 检查是否有其他输入源
                    has_other_input = bool(input_file_id) or bool(input_text and str(input_text).strip())
                    
                    if not has_other_input:
                        # 没有其他输入，停止任务并提示用户
                        error_msg = (
                            f"⚠️ 网页抓取失败\n\n"
                            f"抓取到的内容仅有 {len(url_content)} 字符，无法进行有效分析。\n\n"
                            f"可能原因：\n"
                            f"• 网站有反爬虫保护\n"
                            f"• 页面内容为动态加载（JavaScript渲染）\n"
                            f"• 需要登录才能查看完整内容\n\n"
                            f"解决方法：\n"
                            f"1. 在浏览器中打开该网址\n"
                            f"2. 使用 Ctrl+A 全选页面内容\n"
                            f"3. 使用 Ctrl+C 复制\n"
                            f"4. 将内容粘贴到上方「补充文本」输入框\n"
                            f"5. 重新提交提取任务"
                        )
                        await _set_step(0, "failed", error_msg)
                        await _set_job_status("failed", error=error_msg)
                        return
                    else:
                        # 有其他输入，继续但给出警告
                        await _set_step(0, "running", f"⚠️ URL抓取内容较少({len(url_content)}字符)，将结合其他输入继续处理")
                
                # 检查是否完全没有抓取到内容
                if not url_content:
                    has_other_input = bool(input_file_id) or bool(input_text and str(input_text).strip())
                    if not has_other_input:
                        error_msg = (
                            f"⚠️ 网页抓取失败\n\n"
                            f"无法从该网址获取任何内容。\n\n"
                            f"可能原因：\n"
                            f"• 网址无法访问或已失效\n"
                            f"• 网站有严格的反爬虫保护\n"
                            f"• 网络连接问题\n\n"
                            f"解决方法：\n"
                            f"1. 确认网址可以正常访问\n"
                            f"2. 在浏览器中打开该网址\n"
                            f"3. 使用 Ctrl+A 全选，Ctrl+C 复制\n"
                            f"4. 将内容粘贴到「补充文本」输入框\n"
                            f"5. 重新提交提取任务"
                        )
                        await _set_step(0, "failed", error_msg)
                        await _set_job_status("failed", error=error_msg)
                        return
        else:
            await _set_step(0, "running", "未提供URL，跳过URL解析")

        # 文件处理 - 优先让AI直接读取（如果支持）
        use_ai_file_upload = False
        file_path_for_ai = None
        
        if input_file_id:
            await _set_step(0, "running", "正在处理文件…")
            doc = await database.documents.find_one({"_id": int(input_file_id)})
            if not doc:
                await _set_step(0, "running", "正在进行文件解析…文件不存在")
                await _set_job_status("failed", error="文件不存在")
                return
            file_path = doc.get("file_path")
            ftype = get_file_type(file_path)
            source_doc_id = input_file_id
            
            # 检查AI是否支持文件直传（目前只有PDF支持）
            if provider.supports_capability(AICapability.FILE_UPLOAD) and ftype == "pdf":
                # AI支持文件直传，直接让AI读取文件
                await _set_step(0, "running", f"AI支持文件直传，将直接让AI分析文件…")
                use_ai_file_upload = True
                file_path_for_ai = file_path
                print(f"📄 AI支持文件直传，跳过本地解析，直接让AI读取: {file_path}")
            else:
                # AI不支持文件直传，使用本地解析
                await _set_step(0, "running", "正在本地解析文件…")
                parse_result = parse_file(file_path, ftype)
                if not parse_result.get("success", False):
                    await _set_step(0, "failed", f"文件解析失败: {parse_result.get('error', '未知错误')}")
                    return
                
                r = {
                    "success": True,
                    "content": parse_result.get("content", ""),
                    "file_path": file_path,
                    "method": "file_parser"
                }
                if r.get("success") and r.get("content"):
                    file_content = r["content"]
                    fetched_parts.append(file_content)
                    await _set_step(0, "running", f"本地解析成功 ({len(file_content)}字符)")
                else:
                    await _set_step(0, "running", "本地解析文件失败")

        # 文本
        if input_text and str(input_text).strip():
            fetched_parts.append(str(input_text).strip())

        merged_text = "\n\n".join([p for p in fetched_parts if isinstance(p, str) and p.strip()])
        
        # 调试merged_text
        print(f"\n🔍 Merged Text调试:")
        print(f"  - fetched_parts数量: {len(fetched_parts)}")
        print(f"  - fetched_parts类型: {[type(p).__name__ for p in fetched_parts]}")
        print(f"  - merged_text长度: {len(merged_text)}")
        print(f"  - merged_text预览: {merged_text[:200] if merged_text else 'EMPTY'}")
        print(f"  - use_ai_web_reading: {use_ai_web_reading}")
        print(f"  - use_ai_file_upload: {use_ai_file_upload}")
        
        # 如果使用AI直接读取URL或文件，不需要本地解析的内容
        if use_ai_web_reading:
            await _set_step(0, "completed", "将由AI直接分析网页")
        elif use_ai_file_upload:
            await _set_step(0, "completed", "将由AI直接分析文件")
        elif not merged_text.strip():
            print(f"❌ merged_text为空，检查是否可以降级")
            # 本地解析失败，检查是否可以让AI直接读取
            if input_url and provider.supports_capability(AICapability.WEB_READING):
                # 当前提供商支持网页阅读，直接使用
                await _set_step(0, "completed", "本地解析失败，将由AI直接分析网页")
                use_ai_web_reading = True
            elif input_url:
                # 当前提供商不支持，尝试降级到Google
                fallback_provider = None
                try:
                    fallback_provider = AIProviderFactory.create_provider(
                        provider_type="google",
                        api_key=os.getenv("GOOGLE_API_KEY"),
                        model="gemini-2.0-flash"
                    )
                except Exception:
                    fallback_provider = None

                if fallback_provider and fallback_provider.supports_capability(AICapability.WEB_READING):
                    await _set_step(0, "completed", "本地解析失败，转交Google直接分析网页…")
                    provider = fallback_provider
                    use_ai_web_reading = True
                else:
                    await _set_step(0, "failed", "本地解析失败且无法降级处理")
                    await _set_job_status("failed", error="未提供有效的URL/文件/文本内容")
                    return
            else:
                await _set_step(0, "failed", "未提供有效内容")
                await _set_job_status("failed", error="未提供有效的URL/文件/文本内容")
                return
        else:
            # 正常抓取到内容，标记 FETCH 步骤完成
            await _set_step(0, "completed", "抓取与汇总完成")
            
            # 等待一下让前端能轮询到这个状态
            await asyncio.sleep(0.2)
            
            # 立即保存解析内容到job记录中，让前端可以查看
            context_update = {}
            if url_content:
                context_update["url_content"] = url_content
            if file_content:
                context_update["file_content"] = file_content
            
            if context_update:
                # 更新缓存中的context
                cached = get_job_from_cache(job_id_int)
                if cached:
                    cached["context"] = context_update
                    set_job_to_cache(job_id_int, cached)
                
                await database.ai_jobs.update_one(
                    {"_id": job_id_int},
                    {"$set": {"context": context_update, "updated_at": datetime.utcnow().isoformat()}}
                )

        # Step 2: parse（此处主要做轻量清洗与长度控制）
        # 如果使用AI直接读取URL或文件，跳过本地解析步骤
        if use_ai_web_reading:
            await _set_step(1, "completed", "AI将直接分析网页，跳过本地解析")
            text_for_ai = ""  # 置空，后续会使用AI直接读取URL
        elif use_ai_file_upload:
            await _set_step(1, "completed", "AI将直接分析文件，跳过本地解析")
            text_for_ai = ""  # 置空，后续会使用AI直接读取文件
        else:
            await _set_step(1, "running", "正在清洗与整理文本…")
            await asyncio.sleep(0.1)  # 短暂延迟让前端看到running状态
            
            text_for_ai = merged_text.strip()
            if not text_for_ai:
                await _set_step(1, "failed", "无有效文本可供分析")
                await _set_job_status("failed", error="无有效文本可供分析")
                return
            # 智能裁剪超长文本，保留关键信息
            if len(text_for_ai) > 6000:  # 降低到6000字符，为prompt留出空间
                # 尝试保留开头和结尾，中间截取关键段落
                lines = text_for_ai.split('\n')
                if len(lines) > 100:
                    # 保留前30%和后30%，中间取关键段落
                    keep_start = int(len(lines) * 0.3)
                    keep_end = int(len(lines) * 0.7)
                    middle_lines = lines[keep_start:keep_end]
                    
                    # 从中间选择包含关键词的行
                    keywords = ['报名', '截止', '要求', '规则', '时间', '地址', '联系', '提交', '作品', '竞赛', '比赛']
                    important_lines = []
                    for line in middle_lines:
                        if any(kw in line for kw in keywords):
                            important_lines.append(line)
                            if len(important_lines) >= 20:  # 最多保留20行关键信息
                                break
                    
                    text_for_ai = '\n'.join(lines[:keep_start] + important_lines + lines[keep_end:])
                else:
                    text_for_ai = text_for_ai[:6000]
            await _set_step(1, "completed", "本地解析完成，准备提交AI解析竞赛信息…")
            await asyncio.sleep(0.2)  # 等待让前端看到完成状态

        # Step 3: ai 调用
        await _set_step(2, "running", "正在提交AI解析竞赛信息…")
        
        # 添加调试日志
        print(f"🔍 AI提取调试信息:")
        print(f"  - 提供商: {provider.name}")
        print(f"  - 模型: {provider.model}")
        print(f"  - 文本长度: {len(text_for_ai) if text_for_ai else 0}")
        print(f"  - 源URL: {source_url}")
        print(f"  - 使用AI网页阅读: {use_ai_web_reading}")
        print(f"  - 使用AI文件直传: {use_ai_file_upload}")
        print(f"  - 文件路径: {file_path_for_ai}")
        print(f"  - 支持网页阅读: {provider.supports_capability(AICapability.WEB_READING) if hasattr(provider, 'supports_capability') else 'N/A'}")
        print(f"  - 支持文件直传: {provider.supports_capability(AICapability.FILE_UPLOAD) if hasattr(provider, 'supports_capability') else 'N/A'}")
        
        # 根据情况选择调用方式（优先级：文件直传 > 网页阅读 > 文本）
        if use_ai_file_upload and file_path_for_ai:
            # AI直接读取文件
            print(f"📄 使用AI文件直传模式，文件: {file_path_for_ai}")
            await _set_step(2, "running", "AI正在直接分析文件内容…")
            ai_resp = await provider.extract_from_file(file_path_for_ai, prompt)
        elif use_ai_web_reading and source_url:
            # AI直接读取URL
            print(f"🌐 使用AI网页阅读模式，URL: {source_url}")
            await _set_step(2, "running", "AI正在直接分析网页内容…")
            ai_resp = await provider.extract_from_url(source_url, prompt)
        elif text_for_ai:
            # 使用本地解析的文本
            print(f"📝 使用文本模式，文本预览: {text_for_ai[:100] if text_for_ai else 'None'}...")
            ai_resp = await provider.extract_from_text(text_for_ai, prompt)
        elif source_url and provider.supports_capability(AICapability.WEB_READING):
            # 本地解析失败但AI支持网页阅读，降级使用AI读取
            print(f"🌐 本地解析失败，降级使用AI网页阅读模式，URL: {source_url}")
            await _set_step(2, "running", "本地解析失败，AI正在直接分析网页…")
            ai_resp = await provider.extract_from_url(source_url, prompt)
        else:
            print(f"❌ 无有效内容可供AI分析")
            ai_resp = None

        if not ai_resp or not ai_resp.success:
            error_msg = getattr(ai_resp, "error", "AI 调用失败")
            print(f"\n{'='*60}")
            print(f"❌ AI调用失败详情:")
            print(f"{'='*60}")
            print(f"🔴 错误消息: {error_msg}")
            print(f"🔴 ai_resp对象: {ai_resp}")
            print(f"🔴 ai_resp类型: {type(ai_resp)}")
            if ai_resp:
                print(f"🔴 ai_resp.success: {getattr(ai_resp, 'success', 'N/A')}")
                print(f"🔴 ai_resp.error: {getattr(ai_resp, 'error', 'N/A')}")
                print(f"🔴 ai_resp.provider: {getattr(ai_resp, 'provider', 'N/A')}")
                print(f"🔴 ai_resp.model: {getattr(ai_resp, 'model', 'N/A')}")
                if hasattr(ai_resp, 'raw_response') and ai_resp.raw_response:
                    raw = ai_resp.raw_response
                    print(f"🔴 ai_resp.raw_response长度: {len(raw)}")
                    print(f"🔴 ai_resp.raw_response预览: {raw[:500]}...")
            print(f"{'='*60}\n")
            
            await _set_step(2, "failed", error_msg)
            await _set_job_status("failed", error=error_msg)
            return
        
        print(f"✅ AI调用成功，数据: {type(ai_resp.data)}")
        await _set_step(2, "completed", "解析成功，准备保存结果…")
        await asyncio.sleep(0.2)  # 等待让前端看到AI完成状态

        # 规范化与保存
        await _set_step(3, "running", "正在保存结果…")
        await asyncio.sleep(0.1)  # 短暂延迟让前端看到running状态
        
        data = ai_resp.data if isinstance(ai_resp.data, dict) else {}
        print(f"\n📋 AI原始返回数据:")
        print(f"  - requirements: {data.get('requirements')}")
        print(f"  - contact_info: {data.get('contact_info')}")
        print(f"  - prize_info: {data.get('prize_info')}")
        
        data = _normalize_extracted_urls(data, source_url)
        
        print(f"\n📋 规范化后数据:")
        print(f"  - requirements: {data.get('requirements')}")
        print(f"  - contact_info: {data.get('contact_info')}")
        print(f"  - prize_info: {data.get('prize_info')}")
        
        extraction_record = {
            "source_url": source_url,
            "source_doc_id": source_doc_id,
            "source_type": "mixed",
            "extracted_json": data,
            "model": ai_resp.model,
            "provider": ai_resp.provider,
            "prompt_id": payload.get("prompt_template") or "unified_extraction_v4",
            "extraction_time": datetime.utcnow().isoformat(),
            "raw_response": ai_resp.raw_response,
            "confidence": calculate_confidence(data) if isinstance(data, dict) else 0.5,
            "status": "success"
        }
        ins = await database.ai_extractions.insert_one(extraction_record)
        extraction_id = str(ins.inserted_id)

        # 更新任务状态和结果，保留已有的context内容
        update_data = {
            "status": "completed",
            "updated_at": datetime.utcnow().isoformat(),
            "result": {
                "extraction_id": extraction_id,
                "confidence": extraction_record["confidence"],
                "provider": ai_resp.provider,
                "model": ai_resp.model
            }
        }
        
        # 更新context，保留已有的内容
        context_update = {}
        if url_content:
            context_update["url_content"] = url_content
        if file_content:
            context_update["file_content"] = file_content
        
        if context_update:
            update_data["context"] = context_update
        
        # 更新缓存
        cached = get_job_from_cache(job_id_int)
        if cached:
            cached.update(update_data)
            set_job_to_cache(job_id_int, cached)
        
        await database.ai_jobs.update_one(
            {"_id": job_id_int},
            {"$set": update_data}
        )
        await _set_step(3, "completed", "保存完成")
        print(f"✅ 任务 {job_id} 执行完成")

    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        
        print(f"\n{'='*60}")
        print(f"❌ 任务 {job_id} 执行失败")
        print(f"{'='*60}")
        print(f"🔴 异常类型: {error_type}")
        print(f"🔴 异常消息: {error_msg}")
        print(f"🔴 异常详情: {repr(e)}")
        print(f"📜 完整堆栈跟踪:")
        print(stack_trace)
        print(f"{'='*60}\n")
        
        try:
            await _set_job_status("failed", error=f"{error_type}: {error_msg}")
        except Exception as db_err:
            print(f"❌ 更新任务状态失败: {type(db_err).__name__}: {db_err}")


@router.get("/extract/jobs/{job_id}")
async def get_extraction_job(job_id: str):
    """查询提取任务进度与结果。"""
    from fastapi.responses import JSONResponse
    from database import get_job_from_cache
    
    try:
        database = get_database()
        if database is None:
            return JSONResponse(
                content={"status": "error", "code": 500, "message": "数据库连接失败，请稍后重试", "data": None},
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
            )
        
        job = await database.ai_jobs.find_one({"_id": int(job_id)})
        if not job:
            return JSONResponse(
                content={"status": "error", "code": 404, "message": "任务不存在", "data": None},
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
            )
        job["_id"] = str(job["_id"])
        # 结果中的ID转字符串 - 安全检查 result 是否存在且为字典
        result = job.get("result")
        if isinstance(result, dict) and result.get("extraction_id"):
            job["result"]["extraction_id"] = str(result["extraction_id"])
        
        # 将 datetime 对象转换为 ISO 格式字符串
        if isinstance(job.get("created_at"), datetime):
            job["created_at"] = job["created_at"].isoformat()
        if isinstance(job.get("updated_at"), datetime):
            job["updated_at"] = job["updated_at"].isoformat()

        return JSONResponse(
            content={
                "status": "success",
                "code": 200,
                "message": "获取成功",
                "data": job
            },
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )
    except Exception as e:
        import traceback
        print(f"❌ get_extraction_job 错误: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(
            content={"status": "error", "code": 500, "message": f"系统错误: {str(e)}", "data": None},
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
        )


@router.post("/extract/jobs/{job_id}/cancel")
async def cancel_extraction_job(job_id: str):
    """取消提取任务"""
    from database import update_job_status_in_cache
    
    try:
        database = get_database()
        if database is None:
            return {
                "status": "error",
                "code": 500,
                "message": "数据库连接失败",
                "data": None
            }
        
        job = await database.ai_jobs.find_one({"_id": int(job_id)})
        if not job:
            return {
                "status": "error",
                "code": 404,
                "message": "任务不存在",
                "data": None
            }
        
        # 更新缓存
        update_job_status_in_cache(int(job_id), "cancelled", error="用户取消任务")
        
        # 更新数据库
        await database.ai_jobs.update_one(
            {"_id": int(job_id)},
            {"$set": {
                "status": "cancelled",
                "error": "用户取消任务",
                "updated_at": datetime.utcnow().isoformat()
            }}
        )
        
        print(f"⏹ 任务 {job_id} 已被用户取消")
        
        return {
            "status": "success",
            "code": 200,
            "message": "任务已取消",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": f"取消失败: {str(e)}",
            "data": None
        }


@router.get("/extractions/{extraction_id}")
async def get_extraction(extraction_id: str):
    """获取提取结果详情"""
    try:
        # 检查数据库连接
        database = get_database()
        if database is None:
            return {
                "status": "error",
                "code": 500,
                "message": "数据库连接失败，请稍后重试",
                "data": None
            }
        
        extraction = await database.ai_extractions.find_one({"_id": int(extraction_id)})
        
        if not extraction:
            return {
                "status": "error",
                "code": 404,
                "message": "提取记录不存在",
                "data": None
            }
        
        # 转换ID为字符串
        extraction["_id"] = str(extraction["_id"])
        if extraction.get("source_doc_id"):
            extraction["source_doc_id"] = str(extraction["source_doc_id"])
        if extraction.get("extraction_time"):
            # 只有当 extraction_time 是 datetime 对象时才转换
            if isinstance(extraction["extraction_time"], datetime):
                extraction["extraction_time"] = extraction["extraction_time"].isoformat()
        
        return {
            "status": "success",
            "code": 200,
            "message": "获取成功",
            "data": extraction
        }
        
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": f"系统错误: {str(e)}",
            "data": None
        }


@router.post("/providers/{provider_type}/retry")
async def retry_provider_health(provider_type: str):
    """重新检测单个提供商的健康状态"""
    try:
        # 检查提供商类型是否支持
        available_providers = AIProviderFactory.get_available_providers()
        provider_types = [p["type"] for p in available_providers]
        
        if provider_type not in provider_types:
            return {
                "status": "error",
                "code": 400,
                "message": f"不支持的提供商类型: {provider_type}",
                "data": None
            }
        
        # 重新检测健康状态
        health_result = await health_checker.retry_provider_health(provider_type)
        
        return {
            "status": "success",
            "code": 200,
            "message": "重新检测完成",
            "data": {
                "provider_type": provider_type,
                "health_status": health_result
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": f"重新检测失败: {str(e)}",
            "data": None
        }


@router.get("/extractions/count")
async def get_extractions_count():
    """返回AI提取记录总数"""
    try:
        database = get_database()
        if database is None:
            return {
                "status": "error",
                "code": 500,
                "message": "数据库连接失败，请稍后重试",
                "data": None
            }
        total = await database.ai_extractions.count_documents({})
        return {
            "status": "success",
            "code": 200,
            "message": "获取成功",
            "data": {
                "total": int(total)
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "message": f"系统错误: {str(e)}",
            "data": None
        }
