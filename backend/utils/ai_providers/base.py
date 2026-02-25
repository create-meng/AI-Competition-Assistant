"""
AI提供商基类
定义所有AI提供商必须实现的接口
"""
import time
import httpx
import functools
import traceback
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field


class AICapability(Enum):
    """AI提供商能力枚举"""
    TEXT_ONLY = "text_only"
    FILE_UPLOAD = "file_upload"
    WEB_READING = "web_reading"
    IMAGE_READING = "image_reading"


@dataclass
class AIProviderResponse:
    """AI提供商响应"""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    raw_response: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


@dataclass
class ProviderConfig:
    """提供商配置"""
    supported_models: List[str]
    default_model: str
    health_check_model: str
    api_base_url: str


def log_provider_call(method_name: str):
    """统一的提供商方法日志装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            provider_name = getattr(self, 'name', 'Unknown')
            model = getattr(self, 'model', 'Unknown')
            
            # 记录调用开始
            print(f"\n{'='*50}")
            print(f"🔵 [{provider_name}] {method_name} 开始")
            print(f"🔵 [{provider_name}] 模型: {model}")
            
            # 记录参数（脱敏处理）
            if args:
                for i, arg in enumerate(args):
                    if isinstance(arg, str):
                        preview = arg[:200] + "..." if len(arg) > 200 else arg
                        print(f"🔵 [{provider_name}] 参数{i+1}长度: {len(arg)}, 预览: {preview}")
                    else:
                        print(f"🔵 [{provider_name}] 参数{i+1}: {type(arg).__name__}")
            
            start_time = time.time()
            try:
                result = await func(self, *args, **kwargs)
                elapsed = time.time() - start_time
                
                # 记录结果
                if isinstance(result, AIProviderResponse):
                    if result.success:
                        print(f"✅ [{provider_name}] {method_name} 成功 ({elapsed:.2f}s)")
                        if result.raw_response:
                            preview = result.raw_response[:300] + "..." if len(result.raw_response) > 300 else result.raw_response
                            print(f"🔵 [{provider_name}] 原始响应预览: {preview}")
                    else:
                        print(f"❌ [{provider_name}] {method_name} 失败 ({elapsed:.2f}s)")
                        print(f"🔴 [{provider_name}] 错误: {result.error}")
                        if result.raw_response:
                            print(f"🔴 [{provider_name}] 原始响应: {result.raw_response[:500]}")
                print(f"{'='*50}\n")
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ [{provider_name}] {method_name} 异常 ({elapsed:.2f}s)")
                print(f"🔴 [{provider_name}] 异常类型: {type(e).__name__}")
                print(f"🔴 [{provider_name}] 异常消息: {str(e)}")
                print(f"🔴 [{provider_name}] 堆栈跟踪:\n{traceback.format_exc()}")
                print(f"{'='*50}\n")
                raise
        return wrapper
    return decorator


class BaseAIProvider(ABC):
    """AI提供商基类"""
    
    # 子类必须定义这些类属性
    SUPPORTED_MODELS: List[str] = []
    DEFAULT_MODEL: str = ""
    HEALTH_CHECK_MODEL: str = ""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[AICapability]:
        """提供商支持的能力列表"""
        pass
    
    def supports_capability(self, capability: AICapability) -> bool:
        """检查是否支持某个能力"""
        return capability in self.capabilities
    
    @abstractmethod
    async def extract_from_text(self, text: str, prompt: str) -> AIProviderResponse:
        """从文本中提取信息"""
        pass
    
    async def extract_from_file(self, file_path: str, prompt: str) -> AIProviderResponse:
        """从文件中提取信息"""
        if not self.supports_capability(AICapability.FILE_UPLOAD):
            return AIProviderResponse(
                success=False,
                error=f"{self.name} 不支持文件上传功能",
                provider=self.name,
                model=self.model
            )
        raise NotImplementedError("子类必须实现此方法")
    
    async def extract_from_url(self, url: str, prompt: str) -> AIProviderResponse:
        """从URL中提取信息"""
        if not self.supports_capability(AICapability.WEB_READING):
            # 降级：先抓取网页内容再处理
            from ..content_extractor import ContentExtractor
            result = await ContentExtractor.extract_from_url(url)
            if not result["success"]:
                return AIProviderResponse(
                    success=False,
                    error=f"网页抓取失败: {result.get('error', '未知错误')}",
                    provider=self.name,
                    model=self.model
                )
            return await self.extract_from_text(result["content"], prompt)
        raise NotImplementedError("子类必须实现此方法")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查 - 统一实现，子类可重写 _do_health_check 自定义逻辑
        """
        start_time = time.time()
        
        # 检查 API 密钥
        if not self.api_key or not self.api_key.strip():
            return self._health_result(False, "API密钥未配置", 0)
        
        try:
            result = await self._do_health_check()
            response_time = time.time() - start_time
            return self._health_result(
                result.get("success", False),
                result.get("error"),
                response_time
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return self._health_result(True, "API可用，但当前请求频率受限", 0)
            return self._health_result(False, f"HTTP错误: {e.response.status_code}", 0)
        except Exception as e:
            return self._health_result(False, str(e)[:100], 0)
    
    @abstractmethod
    async def _do_health_check(self) -> Dict[str, Any]:
        """
        执行实际的健康检查请求
        子类必须实现此方法
        
        Returns:
            {"success": bool, "error": str or None}
        """
        pass
    
    def _health_result(self, success: bool, error: Optional[str], response_time: float) -> Dict[str, Any]:
        """构建健康检查结果"""
        return {
            "success": success,
            "error": error if not success or error else None,
            "models": self.SUPPORTED_MODELS,
            "response_time": response_time
        }
    
    def _make_error_response(self, error: str) -> AIProviderResponse:
        """创建错误响应的便捷方法"""
        return AIProviderResponse(
            success=False,
            error=error,
            provider=self.name,
            model=self.model
        )
    
    def _make_success_response(self, data: Dict, raw_response: str = None) -> AIProviderResponse:
        """创建成功响应的便捷方法"""
        return AIProviderResponse(
            success=True,
            data=data,
            raw_response=raw_response,
            provider=self.name,
            model=self.model
        )
