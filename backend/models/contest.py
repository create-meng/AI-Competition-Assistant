"""
竞赛数据模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class ContestStatus(str, Enum):
    """竞赛状态"""
    UPCOMING = "upcoming"  # 即将开始
    ONGOING = "ongoing"    # 进行中
    ENDED = "ended"        # 已结束


class ContestStage(BaseModel):
    """竞赛阶段"""
    name: str
    deadline: Optional[datetime] = None
    description: Optional[str] = None


def _validate_url(v):
    """URL校验函数"""
    if v is None or v == '':
        return None
    
    v = str(v).strip()
    
    # 长度限制
    if len(v) > 2048:
        raise ValueError('URL长度不能超过2048字符')
    
    # 最小长度检查
    if len(v) < 10:
        raise ValueError('URL格式无效，长度过短')
    
    # 协议检查
    if not v.startswith(('http://', 'https://')):
        raise ValueError('URL必须以http://或https://开头')
    
    # 基本格式验证
    url_pattern = re.compile(r'^https?://[^\s/$.?#][^\s]*$', re.IGNORECASE)
    
    if not url_pattern.match(v):
        raise ValueError('URL格式无效，请输入有效的网址')
    
    # 检查是否包含域名（至少有一个点）
    try:
        domain_part = v.split('://')[1].split('/')[0]
        if '.' not in domain_part and domain_part != 'localhost':
            raise ValueError('URL格式无效，缺少有效域名')
    except IndexError:
        raise ValueError('URL格式无效')
    
    return v


class ContestBase(BaseModel):
    """竞赛基础信息"""
    name: str = Field(..., min_length=1, max_length=200)
    organizer: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    entrant_url: Optional[str] = Field(None, max_length=2048)
    teacher_url: Optional[str] = Field(None, max_length=2048)
    default_url: Optional[str] = Field(None, max_length=2048)
    deadline: Optional[datetime] = None
    status: ContestStatus = ContestStatus.UPCOMING
    requirements: List[str] = []
    prize_info: Optional[str] = Field(None, max_length=5000)
    contact_info: Optional[str] = Field(None, max_length=2000)
    stages: List[ContestStage] = []
    
    @validator('entrant_url', 'teacher_url', 'default_url', pre=True)
    def validate_url(cls, v):
        return _validate_url(v)
    
    @validator('requirements', pre=True)
    def validate_requirements(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except:
                pass
            return [s.strip() for s in v.split(',') if s.strip()]
        return v


class ContestCreate(ContestBase):
    """创建竞赛"""
    pass


class ContestUpdate(BaseModel):
    """更新竞赛"""
    name: Optional[str] = Field(None, max_length=200)
    organizer: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=100)
    entrant_url: Optional[str] = Field(None, max_length=2048)
    teacher_url: Optional[str] = Field(None, max_length=2048)
    default_url: Optional[str] = Field(None, max_length=2048)
    deadline: Optional[datetime] = None
    status: Optional[ContestStatus] = None
    requirements: Optional[List[str]] = None
    prize_info: Optional[str] = Field(None, max_length=5000)
    contact_info: Optional[str] = Field(None, max_length=2000)
    stages: Optional[List[ContestStage]] = None
    
    @validator('entrant_url', 'teacher_url', 'default_url', pre=True)
    def validate_url(cls, v):
        return _validate_url(v)


class ContestInDB(ContestBase):
    """数据库中的竞赛"""
    id: str
    created_at: datetime
    updated_at: datetime
    knowledge_graph_id: Optional[str] = None
    documents: List[str] = []


class ContestResponse(ContestBase):
    """竞赛响应"""
    id: str
    created_at: datetime
    updated_at: datetime
    knowledge_graph_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class ContestListResponse(BaseModel):
    """竞赛列表响应"""
    items: List[ContestResponse]
    total: int
    page: int
    size: int
