"""
AI提供商模块

使用示例:
    from utils.ai_providers import AIProviderFactory, health_checker
    
    # 创建提供商
    provider = AIProviderFactory.create_provider("google", api_key="xxx")
    
    # 提取信息
    result = await provider.extract_from_text("内容", "提示词")
    
    # 健康检查
    health = await health_checker.check_all_providers()
"""
from .base import BaseAIProvider, AIProviderResponse, AICapability
from .factory import AIProviderFactory, PROVIDER_CONFIG
from .health_checker import health_checker, AIProviderHealthChecker
from .cloudflare import CloudflareAIProvider
from .google import GoogleAIProvider
from .cerebras import CerebrasAIProvider

__all__ = [
    # 基类
    'BaseAIProvider',
    'AIProviderResponse', 
    'AICapability',
    # 工厂
    'AIProviderFactory',
    'PROVIDER_CONFIG',
    # 健康检查
    'health_checker',
    'AIProviderHealthChecker',
    # 具体提供商
    'CloudflareAIProvider',
    'GoogleAIProvider',
    'CerebrasAIProvider',
]
