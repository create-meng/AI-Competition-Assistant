"""
Cloudflare Workers AI 提供商
"""
import httpx
from typing import List
import os
from .base import BaseAIProvider, AIProviderResponse, AICapability, log_provider_call
from ..json_parser import JSONParser


class CloudflareAIProvider(BaseAIProvider):
    """Cloudflare Workers AI 提供商"""
    
    # 基于官方定价文档，按 Neurons 消耗排序（免费层级: 10,000 Neurons/天）
    # 参考: https://developers.cloudflare.com/workers-ai/platform/pricing
    SUPPORTED_MODELS: List[str] = [
        # 超小型（最省配额）
        "@cf/meta/llama-3.2-1b-instruct",
        "@cf/meta/llama-3.2-3b-instruct",
        # 中型（推荐）
        "@cf/meta/llama-3.1-8b-instruct-fp8-fast",
        "@cf/meta/llama-3.1-8b-instruct-fp8",
        "@cf/meta/llama-3.1-8b-instruct-awq",
        "@cf/meta/llama-3.1-8b-instruct",
        "@cf/mistral/mistral-7b-instruct-v0.1",
        # 大型
        "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        "@cf/meta/llama-4-scout-17b-16e-instruct",
        "@cf/google/gemma-3-12b-it",
        # 推理/代码
        "@cf/qwen/qwq-32b",
        "@cf/qwen/qwen2.5-coder-32b-instruct",
        "@cf/qwen/qwen3-30b-a3b-fp8",
        "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        # 注意: gpt-oss 系列模型API格式不兼容，暂不支持
        # "@cf/openai/gpt-oss-20b",
        # "@cf/openai/gpt-oss-120b",
    ]
    
    # 需要特殊输入格式的模型
    SPECIAL_INPUT_MODELS: List[str] = [
        "@cf/openai/gpt-oss-20b",
        "@cf/openai/gpt-oss-120b",
    ]
    
    # 推理模型（会输出思考过程，需要更多token）
    REASONING_MODELS: List[str] = [
        "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        "@cf/qwen/qwq-32b",
    ]
    
    HEALTH_CHECK_MODEL = "@cf/meta/llama-3.2-1b-instruct"
    DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct-fp8-fast"

    def __init__(self, api_key: str, account_id: str, model: str = None):
        effective_model = model or os.getenv("CLOUDFLARE_MODEL") or self.DEFAULT_MODEL
        if effective_model and not effective_model.startswith("@"):
            effective_model = f"@{effective_model}"
        super().__init__(api_key, effective_model)
        self.account_id = account_id
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run"
    
    @property
    def name(self) -> str:
        return "Cloudflare Workers AI"
    
    @property
    def capabilities(self) -> List[AICapability]:
        return [AICapability.TEXT_ONLY]
    
    @log_provider_call("extract_from_text")
    async def extract_from_text(self, text: str, prompt: str) -> AIProviderResponse:
        if not text or not str(text).strip():
            return self._make_error_response("提交给AI的内容为空")
        
        try:
            print(f"🔧 [Cloudflare] 当前模型: '{self.model}'")
            print(f"🔧 [Cloudflare] 特殊模型列表: {self.SPECIAL_INPUT_MODELS}")
            print(f"🔧 [Cloudflare] 是否在特殊列表中: {self.model in self.SPECIAL_INPUT_MODELS}")
            
            # 推理模型需要更多token
            max_tokens = 8192 if self.model in self.REASONING_MODELS else 4096
            
            # 推理模型的特殊提示
            if self.model in self.REASONING_MODELS:
                system_prompt = "你是一个专业的信息提取助手。请直接返回JSON格式结果，不要输出思考过程。"
            else:
                system_prompt = "你是一个专业的信息提取助手，请严格按照要求提取信息并返回JSON格式。"
            
            # gpt-oss 系列模型使用 text-generation 格式
            if self.model in self.SPECIAL_INPUT_MODELS:
                print(f"🔧 [Cloudflare] 使用特殊输入格式，模型: {self.model}")
                data = {
                    "input": {
                        "prompt": f"{system_prompt}\n\n{prompt}\n\n输入内容：\n{text}"
                    },
                    "max_tokens": max_tokens
                }
                print(f"🔧 [Cloudflare] 请求数据结构: {list(data.keys())}")
            else:
                print(f"🔧 [Cloudflare] 使用标准messages格式")
                data = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{prompt}\n\n输入内容：\n{text}"}
                    ],
                    "max_tokens": max_tokens
                }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                url = f"{self.base_url}/{self.model}"
                print(f"🔧 [Cloudflare] 请求URL: {url}")
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=data
                )
                print(f"🔧 [Cloudflare] 响应状态: {response.status_code}")
                print(f"🔧 [Cloudflare] 响应内容: {response.text[:500]}")
                response.raise_for_status()
                result = response.json()
            
            if result.get("success"):
                # gpt-oss 模型返回格式也不同
                if self.model in self.SPECIAL_INPUT_MODELS:
                    ai_response = result.get("result", {}).get("generated_text", "") or result.get("result", {}).get("response", "") or str(result.get("result", ""))
                else:
                    ai_response = result.get("result", {}).get("response", "")
                
                parsed_data, error_msg, _ = JSONParser.extract_json_from_text(ai_response)
                
                if parsed_data is not None:
                    return self._make_success_response(parsed_data, ai_response)
                return self._make_error_response(f"AI返回的内容不是有效的JSON格式。{error_msg}")
            
            errors = result.get("errors", [])
            error_msg = errors[0].get("message", "未知错误") if errors else "未知错误"
            return self._make_error_response(f"Cloudflare API错误: {error_msg}")
            
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e)
        except Exception as e:
            return self._make_error_response(f"调用失败: {str(e)}")

    async def _do_health_check(self):
        data = {
            "messages": [
                {"role": "system", "content": "你是一个AI助手。"},
                {"role": "user", "content": "请回复'连接正常'"}
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/{self.HEALTH_CHECK_MODEL}",
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            result = response.json()
        
        if result.get("success") and "result" in result:
            content = result["result"].get("response", "")
            if content and content.strip():
                return {"success": True, "error": None}
        
        return {"success": False, "error": "AI没有返回有效内容"}
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _handle_http_error(self, e: httpx.HTTPStatusError) -> AIProviderResponse:
        try:
            detail = e.response.json()
            if detail.get("errors"):
                err = detail["errors"][0]
                msg = err.get("message", "")
                if err.get("code") == 7000 or "No route for that URI" in msg:
                    hint = "模型路由无效，建议使用 '@cf/meta/llama-3.1-8b-instruct-fp8-fast'"
                    return self._make_error_response(f"HTTP错误: {e.response.status_code} - {msg}。{hint}")
        except Exception:
            pass
        return self._make_error_response(f"HTTP错误: {e.response.status_code} - {e.response.text[:200]}")
