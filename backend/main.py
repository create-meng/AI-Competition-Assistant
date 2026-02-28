"""
AI 竞赛助手 - FastAPI 主入口
"""
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from database import init_db, close_db
from routers import auth, contests, ai_extract, documents
from utils.logger import logger, setup_logging
from utils.rate_limiter import rate_limiter
from utils.cache import get_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化日志系统
    setup_logging()
    logger.info("应用启动中...")
    
    # 启动时初始化数据库连接
    await init_db()
    
    # 初始化缓存
    cache = get_cache()
    logger.info("缓存系统初始化完成", cache.stats())
    
    yield
    
    # 关闭时清理资源
    await close_db()
    logger.info("应用已关闭")

app = FastAPI(
    title="AI竞赛助手API",
    description="智能竞赛信息提取与管理平台",
    version="1.0.0",
    lifespan=lifespan
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一 HTTPException 错误响应格式"""
    message = exc.detail
    # 兼容某些地方 detail 可能是 dict 的情况
    if isinstance(message, dict):
        message = message.get("message") or message.get("detail") or str(message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": message,
            "data": None,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一 422 参数校验错误响应格式"""
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": 422,
            "message": "请求参数校验失败",
            "data": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """统一未捕获异常响应格式（避免直接返回框架默认HTML）"""
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
        },
    )

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志和响应时间"""
    start_time = time.time()
    
    # 获取客户端 IP
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP", "")
    if not client_ip and request.client:
        client_ip = request.client.host
    
    # 记录请求
    logger.api_request(
        method=request.method,
        path=request.url.path,
        client_ip=client_ip
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算耗时
    duration_ms = (time.time() - start_time) * 1000
    
    # 记录响应
    logger.api_response(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms
    )
    
    # 添加响应头
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    
    return response

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(contests.router, prefix="/api/v1/contests", tags=["竞赛"])
app.include_router(ai_extract.router, prefix="/api/v1/ai", tags=["AI提取"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["文档管理"])

@app.get("/")
async def root():
    """根路径"""
    return {
        "status": "success",
        "message": "AI竞赛助手 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    cache = get_cache()
    return {
        "status": "healthy",
        "cache": cache.stats(),
        "rate_limiter": rate_limiter.stats()
    }

@app.get("/api/v1/stats")
async def get_system_stats():
    """获取系统统计信息"""
    cache = get_cache()
    return {
        "status": "success",
        "data": {
            "cache": cache.stats(),
            "rate_limiter": rate_limiter.stats()
        }
    }

