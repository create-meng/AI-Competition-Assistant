"""
AI智能提取模块API
"""
from fastapi import APIRouter, BackgroundTasks, Request
from datetime import datetime
import json
import asyncio

from models.extraction import AIExtractRequest, ProvidersListResponse, ProviderInfo
from services import ai_extraction_job_service
from utils.ai_providers.factory import AIProviderFactory
from utils.ai_providers.health_checker import health_checker
from utils.response import success, error
from database import get_database

router = APIRouter(tags=["AI提取"]) 


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


@router.post("/extract/job")
async def start_extraction_job(request: AIExtractRequest, background_tasks: BackgroundTasks):
    """
    启动异步任务式AI提取，返回job_id，前端可轮询进度。
    进度步骤：fetch → parse → ai → save
    """
    job_id = await ai_extraction_job_service.start_job(request)
    background_tasks.add_task(ai_extraction_job_service.run_job, job_id)
    return success({"job_id": job_id}, message="任务已启动")


@router.get("/extract/jobs/{job_id}")
async def get_extraction_job(job_id: str):
    """查询提取任务进度与结果。"""
    from fastapi.responses import JSONResponse

    job = await ai_extraction_job_service.get_job(job_id)
    return JSONResponse(
        content=success(job, message="获取成功"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.post("/extract/jobs/{job_id}/cancel")
async def cancel_extraction_job(job_id: str):
    """取消提取任务"""
    await ai_extraction_job_service.cancel_job(job_id)
    return success(None, message="任务已取消")


@router.get("/extractions/{extraction_id:int}")
async def get_extraction(extraction_id: int):
    """获取提取结果详情"""
    database = get_database()
    if database is None:
        error("数据库未就绪，请稍后重试", code=503)

    extraction = await database.ai_extractions.find_one({"_id": extraction_id})
    if not extraction:
        error("提取记录不存在", code=404)

    extraction["_id"] = str(extraction["_id"])
    if extraction.get("source_doc_id"):
        extraction["source_doc_id"] = str(extraction["source_doc_id"])
    if extraction.get("extraction_time") and isinstance(extraction["extraction_time"], datetime):
        extraction["extraction_time"] = extraction["extraction_time"].isoformat()

    return success(extraction, message="获取成功")


@router.post("/providers/{provider_type}/retry")
async def retry_provider_health(provider_type: str):
    """重新检测单个提供商的健康状态"""
    available_providers = AIProviderFactory.get_available_providers()
    provider_types = [p["type"] for p in available_providers]
    if provider_type not in provider_types:
        error(f"不支持的提供商类型: {provider_type}", code=400)

    health_result = await health_checker.retry_provider_health(provider_type)
    return success(
        {
            "provider_type": provider_type,
            "health_status": health_result,
        },
        message="重新检测完成",
    )


@router.get("/extractions/count")
async def get_extractions_count():
    """返回AI提取记录总数"""
    database = get_database()
    if database is None:
        error("数据库未就绪，请稍后重试", code=503)
    total = await database.ai_extractions.count_documents({})
    return success({"total": int(total)}, message="获取成功")
