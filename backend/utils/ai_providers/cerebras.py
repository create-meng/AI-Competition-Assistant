"""
Cerebras Cloud 提供商
"""
import os
import httpx
from typing import List
from .base import BaseAIProvider, AIProviderResponse, AICapability, log_provider_call
from ..json_parser import JSONParser


class CerebrasAIProvider(BaseAIProvider):
    """Cerebras Cloud 提供商"""

    # 基于官方文档（2025年12月确认）
    # 参考: https://inference-docs.cerebras.ai/models
    SUPPORTED_MODELS: List[str] = [
        # Production 模型
        "llama3.1-8b",
        "llama-3.3-70b",
        "qwen-3-32b",
        "gpt-oss-120b",
        # Preview 模型
        "qwen-3-235b-a22b-instruct-2507",
        "zai-glm-4.6",
    ]
    
    HEALTH_CHECK_MODEL = "llama3.1-8b"
    DEFAULT_MODEL = "llama-3.3-70b"

    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or os.getenv("CEREBRAS_MODEL") or self.DEFAULT_MODEL)
        self.base_url = "https://api.cerebras.ai/v1"

    @property
    def name(self) -> str:
        return "Cerebras"

    @property
    def capabilities(self) -> List[AICapability]:
        return [AICapability.TEXT_ONLY]

    @log_provider_call("extract_from_text")
    async def extract_from_text(self, text: str, prompt: str) -> AIProviderResponse:
        if not text or not str(text).strip():
            return self._make_error_response("提交给AI的内容为空")

        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的信息提取助手，请严格按照要求提取信息并返回JSON格式。"},
                    {"role": "user", "content": f"{prompt}\n\n输入内容：\n{text}"}
                ],
                "temperature": 0.1,
                "top_p": 0.9,
                "max_completion_tokens": 2048,
                "stream": False
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload
                )
                resp.raise_for_status()
                result = resp.json()

            content = None
            if isinstance(result, dict):
                choices = result.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content")

            if not content:
                return self._make_error_response("AI没有返回有效内容")

            parsed_data, error_msg, _ = JSONParser.extract_json_from_text(content)
            if parsed_data is not None:
                return self._make_success_response(parsed_data, content)
            return self._make_error_response(f"AI返回的内容不是有效的JSON格式。{error_msg}")
            
        except httpx.HTTPStatusError as e:
            return self._make_error_response(f"HTTP错误: {e.response.status_code} - {e.response.text[:200]}")
        except Exception as e:
            return self._make_error_response(f"调用失败: {str(e)}")

    async def _do_health_check(self):
        payload = {
            "model": self.HEALTH_CHECK_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个AI助手。"},
                {"role": "user", "content": "请回复'连接正常'"}
            ],
            "temperature": 0.1,
            "max_completion_tokens": 50,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            )
            resp.raise_for_status()
            result = resp.json()
        
        if "choices" in result and result["choices"]:
            content = result["choices"][0].get("message", {}).get("content", "")
            if content and content.strip():
                return {"success": True, "error": None}
        
        return {"success": False, "error": "AI没有返回有效内容"}
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": os.getenv("USER_AGENT", "AICompetitionAssistantBot/1.0")
        }
