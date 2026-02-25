"""
速率限制模块
基于滑动窗口算法实现请求限流
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
from fastapi import HTTPException, Request
from functools import wraps


class RateLimiter:
    """滑动窗口速率限制器"""
    
    def __init__(self):
        # 存储格式: {key: [(timestamp, count), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, Dict]:
        """
        检查请求是否被允许
        
        Args:
            key: 限流键（如 IP 或用户 ID）
            limit: 窗口内最大请求数
            window_seconds: 时间窗口（秒）
        
        Returns:
            (是否允许, 限流信息)
        """
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            # 清理过期记录
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]
            
            current_count = len(self._requests[key])
            remaining = max(0, limit - current_count)
            
            # 计算重置时间
            if self._requests[key]:
                oldest = min(self._requests[key])
                reset_at = oldest + timedelta(seconds=window_seconds)
                reset_seconds = int((reset_at - now).total_seconds())
            else:
                reset_seconds = window_seconds
            
            info = {
                "limit": limit,
                "remaining": remaining,
                "reset_seconds": max(0, reset_seconds),
                "window_seconds": window_seconds
            }
            
            if current_count >= limit:
                return False, info
            
            # 记录本次请求
            self._requests[key].append(now)
            info["remaining"] = remaining - 1
            
            return True, info
    
    async def cleanup(self) -> int:
        """清理所有过期记录"""
        async with self._lock:
            now = datetime.utcnow()
            cleaned = 0
            
            keys_to_delete = []
            for key, timestamps in self._requests.items():
                # 保留最近1小时的记录
                cutoff = now - timedelta(hours=1)
                original_len = len(timestamps)
                self._requests[key] = [ts for ts in timestamps if ts > cutoff]
                cleaned += original_len - len(self._requests[key])
                
                if not self._requests[key]:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._requests[key]
            
            return cleaned
    
    def stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_keys": len(self._requests),
            "total_records": sum(len(v) for v in self._requests.values())
        }


# 全局限流器实例
rate_limiter = RateLimiter()


# 预定义的限流规则
RATE_LIMITS = {
    # AI 提取接口：每分钟 10 次
    "ai_extract": {"limit": 10, "window": 60},
    # 登录接口：每分钟 5 次
    "login": {"limit": 5, "window": 60},
    # 注册接口：每小时 10 次
    "register": {"limit": 10, "window": 3600},
    # 通用 API：每分钟 60 次
    "default": {"limit": 60, "window": 60},
    # 文件上传：每分钟 5 次
    "upload": {"limit": 5, "window": 60},
}


def get_client_ip(request: Request) -> str:
    """获取客户端 IP"""
    # 优先从代理头获取真实 IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    rule_name: str = "default",
    custom_key: Optional[str] = None
) -> Dict:
    """
    检查速率限制
    
    Args:
        request: FastAPI 请求对象
        rule_name: 限流规则名称
        custom_key: 自定义限流键（默认使用 IP）
    
    Returns:
        限流信息字典
    
    Raises:
        HTTPException: 超出限制时抛出 429 错误
    """
    rule = RATE_LIMITS.get(rule_name, RATE_LIMITS["default"])
    
    # 构建限流键
    client_ip = get_client_ip(request)
    key = custom_key or f"{rule_name}:{client_ip}"
    
    allowed, info = await rate_limiter.is_allowed(
        key=key,
        limit=rule["limit"],
        window_seconds=rule["window"]
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "请求过于频繁，请稍后再试",
                "retry_after": info["reset_seconds"],
                "limit": info["limit"],
                "window": info["window_seconds"]
            },
            headers={
                "Retry-After": str(info["reset_seconds"]),
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset_seconds"])
            }
        )
    
    return info


def rate_limit(rule_name: str = "default"):
    """速率限制装饰器（用于路由函数）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中找到 request 对象
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                await check_rate_limit(request, rule_name)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
