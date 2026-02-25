"""
Google Gemini AI 提供商
"""
import httpx
import json
import base64
from pathlib import Path
from typing import List
from .base import BaseAIProvider, AIProviderResponse, AICapability, log_provider_call
from ..json_parser import JSONParser


class GoogleAIProvider(BaseAIProvider):
    """Google Gemini AI 提供商"""
    
    SUPPORTED_MODELS: List[str] = [
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]
    
    URL_CONTEXT_MODELS: List[str] = [
        "gemini-3-pro-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]
    
    HEALTH_CHECK_MODEL = "gemini-2.0-flash-lite"
    DEFAULT_MODEL = "gemini-2.5-flash"
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    
    @property
    def name(self) -> str:
        return "Google Gemini"
    
    @property
    def capabilities(self) -> List[AICapability]:
        caps = [AICapability.TEXT_ONLY, AICapability.FILE_UPLOAD]
        if self.model in self.URL_CONTEXT_MODELS:
            caps.append(AICapability.WEB_READING)
        return caps
    
    def supports_url_context(self) -> bool:
        return self.model in self.URL_CONTEXT_MODELS

    @log_provider_call("extract_from_text")
    async def extract_from_text(self, text: str, prompt: str) -> AIProviderResponse:
        if not text or not str(text).strip():
            return self._make_error_response("提交给AI的内容为空")
        
        try:
            data = {
                "contents": [{"parts": [{"text": f"{prompt}\n\n输入内容：\n{text}"}]}],
                "generationConfig": {"temperature": 0.1, "topK": 1, "topP": 1, "maxOutputTokens": 4096}
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return self._parse_response(response.json())
                
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e)
        except Exception as e:
            return self._make_error_response(f"调用失败: {str(e)}")

    @log_provider_call("extract_from_file")
    async def extract_from_file(self, file_path: str, prompt: str) -> AIProviderResponse:
        try:
            path = Path(file_path)
            if not path.exists():
                return self._make_error_response(f"文件不存在: {file_path}")
            
            mime_types = {".pdf": "application/pdf", ".txt": "text/plain", ".html": "text/html"}
            mime_type = mime_types.get(path.suffix.lower(), "application/octet-stream")
            
            with open(file_path, "rb") as f:
                encoded_data = base64.b64encode(f.read()).decode("utf-8")
            
            data = {
                "contents": [{
                    "parts": [
                        {"inlineData": {"mimeType": mime_type, "data": encoded_data}},
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096}
            }
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return self._parse_response(response.json())
                
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e)
        except Exception as e:
            return self._make_error_response(f"文件直传失败: {str(e)}")

    @log_provider_call("extract_from_url")
    async def extract_from_url(self, url: str, prompt: str) -> AIProviderResponse:
        if not self.supports_url_context():
            return await self._extract_from_url_fallback(url, prompt)
        
        try:
            data = {
                "contents": [{"parts": [{"text": f"请分析以下网页URL的内容：\n网页URL: {url}\n\n{prompt}"}]}],
                "tools": [{"url_context": {}}],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096}
            }
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.model}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json=data
                )
                
                if response.status_code != 200:
                    response.raise_for_status()
                
                result = response.json()
                
                if "candidates" in result and result["candidates"]:
                    parts = result["candidates"][0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0] or not parts[0]["text"]:
                        return await self._extract_from_url_fallback(url, prompt)
                
                return self._parse_response(result)
                
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e)
        except Exception as e:
            return await self._extract_from_url_fallback(url, prompt)
    
    async def _extract_from_url_fallback(self, url: str, prompt: str) -> AIProviderResponse:
        from ..content_extractor import ContentExtractor
        
        result = await ContentExtractor.extract_from_url_deep(url)
        if not result.get("success") or not result.get("content"):
            result = await ContentExtractor.extract_from_url(url)
        
        if not result.get("success") or not result.get("content"):
            return self._make_error_response(f"网页抓取失败: {result.get('error', '未知错误')}")
        
        return await self.extract_from_text(result["content"], prompt)

    async def _do_health_check(self):
        data = {
            "contents": [{"parts": [{"text": "请回复'连接正常'"}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 50}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/{self.HEALTH_CHECK_MODEL}:generateContent?key={self.api_key}",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
        
        if "candidates" in result and result["candidates"]:
            candidate = result["candidates"][0]
            if candidate.get("finishReason") != "SAFETY":
                parts = candidate.get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    return {"success": True, "error": None}
        
        return {"success": False, "error": "AI没有返回有效内容"}

    def _parse_response(self, result: dict) -> AIProviderResponse:
        if "candidates" not in result or not result["candidates"]:
            error_msg = result.get("error", {}).get("message", "未知错误")[:100]
            return self._make_error_response(f"AI没有返回候选结果: {error_msg}")
        
        candidate = result["candidates"][0]
        finish_reason = candidate.get("finishReason")
        
        if finish_reason == "SAFETY":
            return self._make_error_response("内容被安全过滤器拦截")
        if finish_reason == "MAX_TOKENS":
            return self._make_error_response("达到最大token限制")
        
        parts = candidate.get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            return self._make_error_response("AI没有返回有效内容")
        
        ai_response = parts[0]["text"]
        if not ai_response or not ai_response.strip():
            return self._make_error_response("AI返回了空内容")
        
        parsed_data, error_msg, _ = JSONParser.extract_json_from_text(ai_response)
        if parsed_data is not None:
            return self._make_success_response(parsed_data, ai_response)
        return self._make_error_response(f"AI返回的内容不是有效的JSON格式。{error_msg}")
    
    def _handle_http_error(self, e: httpx.HTTPStatusError) -> AIProviderResponse:
        status_code = e.response.status_code
        
        if status_code == 429:
            return self._make_error_response("Google AI 配额超限，请稍后重试")
        
        try:
            error_json = json.loads(e.response.text)
            error_msg = error_json.get("error", {}).get("message", "")[:100]
            if "User location is not supported" in error_msg:
                return self._make_error_response("Google AI API在您的地理位置不可用")
        except Exception:
            error_msg = e.response.text[:100]
        
        return self._make_error_response(f"HTTP错误: {status_code} - {error_msg}")
