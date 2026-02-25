"""
AI提供商工厂
"""
from typing import Optional
import os
from .base import BaseAIProvider
from .cloudflare import CloudflareAIProvider
from .google import GoogleAIProvider
from .cerebras import CerebrasAIProvider


# 提供商配置
PROVIDER_CONFIG = {
    "cloudflare": {
        "class": CloudflareAIProvider,
        "name": "Cloudflare Workers AI",
        "capabilities": ["text_only"],
        "requires": ["api_key", "account_id"],
        "default_model": CloudflareAIProvider.DEFAULT_MODEL,
    },
    "google": {
        "class": GoogleAIProvider,
        "name": "Google Gemini",
        "capabilities": ["text_only", "file_upload", "web_reading"],
        "requires": ["api_key"],
        "default_model": GoogleAIProvider.DEFAULT_MODEL,
    },
    "cerebras": {
        "class": CerebrasAIProvider,
        "name": "Cerebras Cloud",
        "capabilities": ["text_only"],
        "requires": ["api_key"],
        "default_model": CerebrasAIProvider.DEFAULT_MODEL,
    },
}


class AIProviderFactory:
    """AI提供商工厂"""
    
    @staticmethod
    def create_provider(
        provider_type: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseAIProvider:
        """创建AI提供商实例"""
        provider_type = provider_type.lower()
        
        if provider_type not in PROVIDER_CONFIG:
            raise ValueError(f"不支持的AI提供商类型: {provider_type}")
        
        config = PROVIDER_CONFIG[provider_type]
        provider_class = config["class"]
        
        # Cloudflare 需要 account_id
        if provider_type == "cloudflare":
            account_id = kwargs.get("account_id") or os.getenv("CLOUDFLARE_ACCOUNT_ID")
            if not account_id:
                raise ValueError("Cloudflare提供商需要account_id参数")
            return provider_class(api_key=api_key, account_id=account_id, model=model)
        
        return provider_class(api_key=api_key, model=model)
    
    @staticmethod
    def get_available_providers() -> list[dict]:
        """获取所有可用的提供商列表"""
        return [
            {
                "type": ptype,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "requires": config["requires"],
                "default_model": config["default_model"],
            }
            for ptype, config in PROVIDER_CONFIG.items()
        ]
    
    @staticmethod
    def get_provider_models(provider_type: str) -> list[str]:
        """获取指定提供商的支持模型列表"""
        provider_type = provider_type.lower()
        if provider_type not in PROVIDER_CONFIG:
            return []
        return PROVIDER_CONFIG[provider_type]["class"].SUPPORTED_MODELS
