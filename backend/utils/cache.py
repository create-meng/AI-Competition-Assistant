"""
缓存管理模块
支持内存缓存和可选的 Redis 缓存
"""
import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from functools import wraps
import os


class MemoryCache:
    """内存缓存实现（单机部署使用）"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            item = self._cache[key]
            if datetime.utcnow() > item["expires_at"]:
                del self._cache[key]
                return None
            
            return item["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        async with self._lock:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl or self._default_ttl)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.utcnow()
            }
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self.get(key) is not None
    
    async def clear(self) -> int:
        """清空所有缓存"""
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count
    
    async def cleanup_expired(self) -> int:
        """清理过期缓存"""
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                k for k, v in self._cache.items()
                if now > v["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "type": "memory",
            "total_keys": len(self._cache),
            "default_ttl": self._default_ttl
        }


class RedisCache:
    """Redis 缓存实现（分布式部署使用）"""
    
    def __init__(self, redis_url: str = None, default_ttl: int = 300):
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._default_ttl = default_ttl
        self._client = None
        self._connected = False
    
    async def _get_client(self):
        """获取 Redis 客户端"""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.from_url(self._redis_url, decode_responses=True)
                await self._client.ping()
                self._connected = True
            except Exception as e:
                print(f"⚠️ Redis 连接失败: {e}，将使用内存缓存")
                self._connected = False
                return None
        return self._client
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        client = await self._get_client()
        if not client:
            return None
        try:
            value = await client.get(f"cache:{key}")
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        client = await self._get_client()
        if not client:
            return False
        try:
            await client.setex(
                f"cache:{key}",
                ttl or self._default_ttl,
                json.dumps(value, ensure_ascii=False, default=str)
            )
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        client = await self._get_client()
        if not client:
            return False
        try:
            await client.delete(f"cache:{key}")
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        client = await self._get_client()
        if not client:
            return False
        try:
            return await client.exists(f"cache:{key}") > 0
        except Exception:
            return False
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "type": "redis",
            "connected": self._connected,
            "url": self._redis_url.split("@")[-1] if "@" in self._redis_url else self._redis_url,
            "default_ttl": self._default_ttl
        }


# 全局缓存实例
_cache_instance: Optional[MemoryCache] = None


def get_cache() -> MemoryCache:
    """获取缓存实例（默认使用内存缓存）"""
    global _cache_instance
    if _cache_instance is None:
        # 检查是否配置了 Redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio
                _cache_instance = RedisCache(redis_url)
                print("✅ 使用 Redis 缓存")
            except ImportError:
                print("⚠️ redis 包未安装，使用内存缓存")
                _cache_instance = MemoryCache()
        else:
            _cache_instance = MemoryCache()
            print("✅ 使用内存缓存")
    return _cache_instance


def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存键"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            cache_key = f"{prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
