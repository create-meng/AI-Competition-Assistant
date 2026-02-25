"""
AI 竞赛助手 - FastAPI 主入口
"""
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # 前端地址
    allow_credentials=True,
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

