"""
用户数据模型
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    ENTRANT = "entrant"  # 参赛者
    TEACHER = "teacher"  # 指导老师
    ADMIN = "admin"      # 管理员

class UserProfile(BaseModel):
    """用户资料"""
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: UserRole
    school: Optional[str] = None
    real_name: Optional[str] = None

class UserCreate(UserBase):
    """用户注册"""
    password: str = Field(..., min_length=6, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度至少6位')
        return v

class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str

class UserInDB(UserBase):
    """数据库中的用户"""
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    profile: UserProfile = UserProfile()

class UserResponse(UserBase):
    """用户响应（不含密码）"""
    created_at: datetime
    last_login: Optional[datetime] = None
    profile: UserProfile = UserProfile()
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """JWT Token"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

