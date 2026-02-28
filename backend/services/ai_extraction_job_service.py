from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional

from database import get_database
from database import update_job_status_in_cache, update_job_step_in_cache, get_job_from_cache, set_job_to_cache
from models.extraction import AIExtractRequest
from utils.ai_providers.base import AICapability
from utils.ai_providers.factory import AIProviderFactory
from utils.content_extractor import ContentExtractor
from utils.file_parser import get_file_type, parse_file
from utils.logger import logger
from utils.prompt_loader import load_prompt as load_prompt_file
from utils.response import error

from services.ai_extraction_service import _normalize_extracted_urls, calculate_confidence


async def start_job(request: AIExtractRequest) -> str:
    database = get_database()
    if database is None:
        error("数据库未就绪，请稍后重试", code=503)

    job_doc = {
        "type": "ai_extraction",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "steps": [
            {"name": "fetch", "status": "pending", "detail": ""},
            {"name": "parse", "status": "pending", "detail": ""},
            {"name": "ai", "status": "pending", "detail": ""},
            {"name": "save", "status": "pending", "detail": ""},
        ],
        "request": request.model_dump(),
    }

    result = await database.ai_jobs.insert_one(job_doc)
    return str(result.inserted_id)


async def run_job(job_id: str):
    database = get_database()
    if database is None:
        logger.error("数据库连接失败，无法执行任务", {"job_id": job_id})
        return

    try:
        job_id_int = int(job_id)
    except Exception:
        logger.error("任务ID非法，无法执行任务", {"job_id": job_id})
        return

    async def _set_step(idx: int, status: str, detail: str = ""):
        update_job_step_in_cache(job_id_int, idx, status, detail)
        await database.ai_jobs.update_one(
            {"_id": job_id_int},
            {
                "$set": {
                    f"steps.{idx}.status": status,
                    f"steps.{idx}.detail": detail,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            },
        )

    async def _set_job_status(status: str, **kwargs):
        update_job_status_in_cache(job_id_int, status, **kwargs)
        update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
        update_data.update(kwargs)
        await database.ai_jobs.update_one({"_id": job_id_int}, {"$set": update_data})

    try:
        job = await database.ai_jobs.find_one({"_id": job_id_int})
        if not job:
            return

        payload = job.get("request", {}) or {}

        await _set_job_status("running")
        await _set_step(0, "running", "正在抓取与汇总网页/文档/文本内容…")

        provider_type = str(payload.get("provider") or "").lower() or "google"
        provider = _create_provider_from_payload(provider_type, payload)

        prompt_template = payload.get("prompt_template") or "unified_extraction_v4"
        prompt_base = load_prompt_file(f"{prompt_template}.txt")
        context_prefix = {
            "SOURCE_TYPE": payload.get("source_type") or "mixed",
            "BASE_URL": payload.get("source_url") or payload.get("source_content"),
            "PUBLISH_META": None,
        }
        prompt = "[CONTEXT]\n" + json.dumps(context_prefix, ensure_ascii=False) + "\n[/CONTEXT]\n\n" + prompt_base

        fetched_parts: list[str] = []
        source_url: Optional[str] = None
        source_doc_id: Optional[str] = None

        url_content: Optional[str] = None
        file_content: Optional[str] = None

        use_ai_web_reading = False
        use_ai_file_upload = False
        file_path_for_ai: Optional[str] = None

        input_url = payload.get("source_url") or payload.get("source_content")
        input_text = payload.get("source_text") or (
            payload.get("source_content") if (not payload.get("source_url") and not payload.get("file_id")) else None
        )
        input_file_id = payload.get("file_id")

        if input_url and str(input_url).strip():
            u = str(input_url).strip()
            source_url = u
            if provider.supports_capability(AICapability.WEB_READING):
                use_ai_web_reading = True
                await _set_step(0, "running", "AI支持网页阅读，将直接让AI分析URL…")
            else:
                deep = await ContentExtractor.extract_from_url_deep(u)
                if deep.get("success") and deep.get("content"):
                    url_content = deep["content"]
                    fetched_parts.append(url_content)
                else:
                    shallow = await ContentExtractor.extract_from_url(u)
                    if shallow.get("success") and shallow.get("content"):
                        url_content = shallow["content"]
                        fetched_parts.append(url_content)

        if input_file_id:
            doc = await database.documents.find_one({"_id": int(input_file_id)})
            if not doc:
                await _set_step(0, "failed", "文件不存在")
                await _set_job_status("failed", error="文件不存在")
                return

            file_path = doc.get("file_path")
            ftype = get_file_type(file_path)
            source_doc_id = str(input_file_id)

            if provider.supports_capability(AICapability.FILE_UPLOAD) and ftype == "pdf":
                use_ai_file_upload = True
                file_path_for_ai = file_path
                await _set_step(0, "running", "AI支持文件直传，将直接让AI分析文件…")
            else:
                parse_result = parse_file(file_path, ftype)
                if not parse_result.get("success", False):
                    await _set_step(0, "failed", f"文件解析失败: {parse_result.get('error', '未知错误')}")
                    await _set_job_status("failed", error="文件解析失败")
                    return
                file_content = parse_result.get("content", "")
                if isinstance(file_content, str) and file_content.strip():
                    fetched_parts.append(file_content)

        if input_text and str(input_text).strip():
            fetched_parts.append(str(input_text).strip())

        merged_text = "\n\n".join([p for p in fetched_parts if isinstance(p, str) and p.strip()])

        if use_ai_web_reading:
            await _set_step(0, "completed", "将由AI直接分析网页")
        elif use_ai_file_upload:
            await _set_step(0, "completed", "将由AI直接分析文件")
        elif not merged_text.strip():
            await _set_step(0, "failed", "未提供有效的URL/文件/文本内容")
            await _set_job_status("failed", error="未提供有效的URL/文件/文本内容")
            return
        else:
            await _set_step(0, "completed", "抓取与汇总完成")

        context_update = {}
        if url_content:
            context_update["url_content"] = url_content
        if file_content:
            context_update["file_content"] = file_content
        if context_update:
            cached = get_job_from_cache(job_id_int)
            if cached:
                cached["context"] = context_update
                set_job_to_cache(job_id_int, cached)
            await database.ai_jobs.update_one(
                {"_id": job_id_int},
                {"$set": {"context": context_update, "updated_at": datetime.utcnow().isoformat()}},
            )

        if use_ai_web_reading or use_ai_file_upload:
            await _set_step(1, "completed", "AI将直接分析输入，跳过本地解析")
            text_for_ai = ""
        else:
            await _set_step(1, "running", "正在清洗与整理文本…")
            await asyncio.sleep(0.05)
            text_for_ai = merged_text.strip()
            if not text_for_ai:
                await _set_step(1, "failed", "无有效文本可供分析")
                await _set_job_status("failed", error="无有效文本可供分析")
                return
            if len(text_for_ai) > 6000:
                text_for_ai = text_for_ai[:6000]
            await _set_step(1, "completed", "本地解析完成，准备提交AI解析竞赛信息…")

        await _set_step(2, "running", "正在提交AI解析竞赛信息…")

        if use_ai_file_upload and file_path_for_ai:
            ai_resp = await provider.extract_from_file(file_path_for_ai, prompt)
        elif use_ai_web_reading and source_url:
            ai_resp = await provider.extract_from_url(source_url, prompt)
        else:
            ai_resp = await provider.extract_from_text(text_for_ai, prompt)

        if not ai_resp or not ai_resp.success:
            error_msg = getattr(ai_resp, "error", "AI 调用失败")
            await _set_step(2, "failed", error_msg)
            await _set_job_status("failed", error=error_msg)
            return

        await _set_step(2, "completed", "解析成功，准备保存结果…")
        await _set_step(3, "running", "正在保存结果…")

        data = ai_resp.data if isinstance(ai_resp.data, dict) else {}
        data = _normalize_extracted_urls(data, source_url)

        extraction_record = {
            "source_url": source_url,
            "source_doc_id": source_doc_id,
            "source_type": payload.get("source_type") or "mixed",
            "extracted_json": data,
            "model": ai_resp.model,
            "provider": ai_resp.provider,
            "prompt_id": prompt_template,
            "extraction_time": datetime.utcnow().isoformat(),
            "raw_response": ai_resp.raw_response,
            "confidence": calculate_confidence(data) if isinstance(data, dict) else 0.5,
            "status": "success",
        }

        ins = await database.ai_extractions.insert_one(extraction_record)
        extraction_id = str(ins.inserted_id)

        update_data = {
            "status": "completed",
            "updated_at": datetime.utcnow().isoformat(),
            "result": {
                "extraction_id": extraction_id,
                "confidence": extraction_record["confidence"],
                "provider": ai_resp.provider,
                "model": ai_resp.model,
            },
        }
        if context_update:
            update_data["context"] = context_update

        cached = get_job_from_cache(job_id_int)
        if cached:
            cached.update(update_data)
            set_job_to_cache(job_id_int, cached)

        await database.ai_jobs.update_one({"_id": job_id_int}, {"$set": update_data})
        await _set_step(3, "completed", "保存完成")

    except Exception as e:
        logger.error("任务执行失败", {"job_id": job_id, "error": str(e)}, exc_info=True)
        try:
            await _set_job_status("failed", error=str(e))
        except Exception:
            pass


async def get_job(job_id: str) -> dict[str, Any]:
    database = get_database()
    if database is None:
        error("数据库未就绪，请稍后重试", code=503)

    try:
        job_id_int = int(job_id)
    except Exception:
        error("无效的任务ID", code=400)

    job = await database.ai_jobs.find_one({"_id": job_id_int})
    if not job:
        error("任务不存在", code=404)

    job["_id"] = str(job["_id"])
    result = job.get("result")
    if isinstance(result, dict) and result.get("extraction_id"):
        job["result"]["extraction_id"] = str(result["extraction_id"])

    if isinstance(job.get("created_at"), datetime):
        job["created_at"] = job["created_at"].isoformat()
    if isinstance(job.get("updated_at"), datetime):
        job["updated_at"] = job["updated_at"].isoformat()

    return job


async def cancel_job(job_id: str):
    database = get_database()
    if database is None:
        error("数据库未就绪，请稍后重试", code=503)

    try:
        job_id_int = int(job_id)
    except Exception:
        error("无效的任务ID", code=400)

    job = await database.ai_jobs.find_one({"_id": job_id_int})
    if not job:
        error("任务不存在", code=404)

    update_job_status_in_cache(job_id_int, "cancelled", error="用户取消任务")
    await database.ai_jobs.update_one(
        {"_id": job_id_int},
        {
            "$set": {
                "status": "cancelled",
                "error": "用户取消任务",
                "updated_at": datetime.utcnow().isoformat(),
            }
        },
    )


def _create_provider_from_payload(provider_type: str, payload: dict[str, Any]):
    provider_key_map = {
        "cloudflare": "CLOUDFLARE_API_KEY",
        "google": "GOOGLE_API_KEY",
        "doubao": "DOUBAO_API_KEY",
        "free_qwq": "FREE_QWQ_API_KEY",
        "suanli": "SUANLI_API_KEY",
        "cerebras": "CEREBRAS_API_KEY",
    }

    env_key = provider_key_map.get(provider_type)
    api_key = os.getenv(env_key) if env_key else None

    if not api_key and provider_type == "suanli":
        api_key = os.getenv("FREE_QWQ_API_KEY") or os.getenv("FREE_QWQ_QPI_KEY")
    if not api_key and provider_type == "free_qwq":
        api_key = os.getenv("SUANLI_API_KEY") or os.getenv("FREE_QWQ_QPI_KEY")
    if not api_key and provider_type in ("free_qwq", "suanli"):
        api_key = os.getenv("FREE_QWQ_QPI_KEY")

    kwargs: dict[str, Any] = {}
    if provider_type == "cloudflare":
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if account_id:
            kwargs["account_id"] = account_id

    return AIProviderFactory.create_provider(
        provider_type=provider_type,
        api_key=api_key,
        model=payload.get("model"),
        **kwargs,
    )
