"""
AI提取相关的数据模型（宽松校验，避免422，逻辑校验在路由中完成）
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AIExtractRequest(BaseModel):
    """AI提取请求"""
    # 兼容旧字段：source_content 作为文本或URL
    source_content: Optional[str] = Field(None, description="文本内容或URL（兼容旧字段）")
    # 新增独立字段，便于混合提交
    source_url: Optional[str] = Field(None, description="网页URL（可选）")
    source_text: Optional[str] = Field(None, description="纯文本内容（可选）")
    file_id: Optional[str] = Field(None, description="文件ID（如果是文件）")
    provider: Optional[str] = Field(None, description="AI提供商: cloudflare/google/doubao/free_qwq")
    model: Optional[str] = Field(None, description="模型名称")
    prompt_template: str = Field("unified_extraction_v4", description="Prompt模板名称")
    source_type: str = Field("mixed", description="来源类型: url/text/file/mixed/auto")
    # 说明：不在模型层做严格校验，避免422；在路由内统一lower并做兼容


class AIExtractResponse(BaseModel):
    """AI提取响应"""
    status: str = Field(..., description="success/error")
    code: int = Field(200, description="状态码")
    message: str = Field("", description="消息")
    data: Optional[Dict[str, Any]] = Field(None, description="提取的数据")
    
    class ExtractionData(BaseModel):
        """提取数据详情"""
        extraction_id: Optional[str] = None
        extracted_json: Dict[str, Any]
        raw_response: str
        provider: str
        model: str
        confidence: float = 0.0
        source_url: Optional[str] = None
        source_doc_id: Optional[str] = None
        source_type: str
        extraction_time: datetime
        status: str = "success"
        error: Optional[str] = None
        warning: Optional[str] = None


class ProviderInfo(BaseModel):
    """AI提供商信息"""
    type: str
    name: str
    capabilities: List[str]
    requires: List[str]
    default_model: str
    status: Optional[str] = Field(None, description="提供商状态: available/unavailable/unknown")
    reason: Optional[str] = Field(None, description="状态原因")
    available_models: Optional[List[str]] = Field(None, description="可用模型列表")
    last_check: Optional[str] = Field(None, description="最后检查时间")
    response_time: Optional[float] = Field(None, description="响应时间(秒)")


class ProvidersListResponse(BaseModel):
    """提供商列表响应"""
    status: str = "success"
    code: int = 200
    message: str = "获取成功"
    data: List[ProviderInfo]
