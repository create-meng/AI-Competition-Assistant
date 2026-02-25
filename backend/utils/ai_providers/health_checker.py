"""
AI提供商健康检查工具
"""
import asyncio
import os
from typing import Dict, Optional, Callable
from datetime import datetime
from .factory import AIProviderFactory


# API 密钥环境变量映射
API_KEY_MAP = {
    "cloudflare": "CLOUDFLARE_API_KEY",
    "google": "GOOGLE_API_KEY",
    "doubao": "DOUBAO_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
}

# 启用的提供商列表
ENABLED_PROVIDERS = ["cloudflare", "google", "cerebras"]


class AIProviderHealthChecker:
    """AI提供商健康检查器"""
    
    def __init__(self):
        self.health_cache: Dict[str, Dict] = {}
        self.cache_duration = 300  # 5分钟缓存
    
    def get_api_key(self, provider_type: str) -> Optional[str]:
        """获取提供商的 API 密钥"""
        env_key = API_KEY_MAP.get(provider_type)
        return os.getenv(env_key) if env_key else None
    
    async def check_provider_health(self, provider_type: str) -> Dict:
        """检查单个提供商的健康状态"""
        now = datetime.utcnow().isoformat()
        print(f"\n🔍 [{provider_type}] 开始健康检查...")
        
        # 检查 API 密钥
        api_key = self.get_api_key(provider_type)
        if not api_key:
            result = {"status": "unavailable", "reason": "API密钥未配置", "available_models": [], "last_check": now}
            print(f"❌ [{provider_type}] API密钥未配置")
            print(f"📊 [{provider_type}] 结果: {result}")
            return result
        
        print(f"✅ [{provider_type}] API密钥已配置")
        
        # Cloudflare 需要额外的 account_id
        kwargs = {}
        if provider_type == "cloudflare":
            account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
            if not account_id:
                result = {"status": "unavailable", "reason": "Cloudflare Account ID未配置", "available_models": [], "last_check": now}
                print(f"❌ [{provider_type}] Account ID未配置")
                print(f"📊 [{provider_type}] 结果: {result}")
                return result
            kwargs["account_id"] = account_id
            print(f"✅ [{provider_type}] Account ID已配置")
        
        try:
            # 创建提供商实例并执行健康检查
            print(f"🔄 [{provider_type}] 创建提供商实例...")
            provider = AIProviderFactory.create_provider(provider_type, api_key, **kwargs)
            print(f"✅ [{provider_type}] 提供商实例创建成功，模型: {provider.model}")
            
            print(f"🔄 [{provider_type}] 执行健康检查（超时30秒）...")
            health_result = await asyncio.wait_for(provider.health_check(), timeout=30.0)
            print(f"📡 [{provider_type}] 健康检查原始结果: {health_result}")
            
            result = {
                "status": "available" if health_result["success"] else "unavailable",
                "reason": health_result.get("error") or "连接正常",
                "available_models": health_result.get("models", []),
                "last_check": now,
                "response_time": health_result.get("response_time", 0)
            }
            
            status_icon = "✅" if result["status"] == "available" else "❌"
            print(f"{status_icon} [{provider_type}] 状态: {result['status']}, 原因: {result['reason']}")
            print(f"📋 [{provider_type}] 可用模型数量: {len(result['available_models'])}")
            print(f"📊 [{provider_type}] 最终结果: {result}")
            return result
            
        except asyncio.TimeoutError:
            result = {"status": "unavailable", "reason": "健康检查超时（30秒）", "available_models": [], "last_check": now}
            print(f"⏰ [{provider_type}] 健康检查超时")
            print(f"📊 [{provider_type}] 结果: {result}")
            return result
        except Exception as e:
            result = {"status": "unavailable", "reason": f"检查失败: {str(e)}", "available_models": [], "last_check": now}
            print(f"❌ [{provider_type}] 检查异常: {str(e)}")
            print(f"📊 [{provider_type}] 结果: {result}")
            return result

    async def check_all_providers(self, progress_callback: Callable = None) -> Dict[str, Dict]:
        """并行检查所有提供商的健康状态"""
        print("\n" + "="*60)
        print("🚀 开始健康检查所有AI提供商")
        print(f"📋 启用的提供商: {ENABLED_PROVIDERS}")
        print("="*60)
        
        results = {}
        available_count = 0
        total_count = len(ENABLED_PROVIDERS)
        
        # 先快速标记无 API 密钥的提供商
        providers_to_check = []
        for provider in ENABLED_PROVIDERS:
            if not self.get_api_key(provider):
                results[provider] = {
                    "status": "unavailable",
                    "reason": "API密钥未配置",
                    "available_models": [],
                    "last_check": datetime.utcnow().isoformat()
                }
                print(f"⚠️ [{provider}] 跳过检查 - API密钥未配置")
            else:
                providers_to_check.append(provider)
        
        print(f"📋 需要检查的提供商: {providers_to_check}")
        
        if not providers_to_check:
            print("⚠️ 没有需要检查的提供商")
            print("="*60 + "\n")
            return results
        
        # 并发检查有密钥的提供商
        async def check_with_callback(provider: str):
            nonlocal available_count
            result = await self.check_provider_health(provider)
            results[provider] = result
            
            if result.get("status") == "available":
                available_count += 1
            
            if progress_callback:
                progress_callback(len(results), total_count, available_count)
            
            return result
        
        tasks = [check_with_callback(p) for p in providers_to_check]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n" + "="*60)
        print("📊 健康检查汇总:")
        for provider, result in results.items():
            status_icon = "✅" if result["status"] == "available" else "❌"
            models_count = len(result.get("available_models", []))
            print(f"  {status_icon} {provider}: {result['status']} ({models_count} 模型) - {result.get('reason', '')}")
        print(f"📈 总计: {available_count}/{total_count} 可用")
        print("="*60 + "\n")
        
        return results
    
    def get_cached_health(self, provider_type: str) -> Optional[Dict]:
        """获取缓存的健康状态"""
        if provider_type not in self.health_cache:
            return None
        
        cached = self.health_cache[provider_type]
        last_check = datetime.fromisoformat(cached["last_check"])
        if (datetime.utcnow() - last_check).seconds < self.cache_duration:
            return cached
        return None
    
    def cache_health_result(self, provider_type: str, result: Dict):
        """缓存健康检查结果"""
        self.health_cache[provider_type] = result


# 全局实例
health_checker = AIProviderHealthChecker()
