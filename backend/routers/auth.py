"""
认证路由 - 注册、登录
完全重构版本
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from datetime import datetime, timezone
# from bson import ObjectId  # MongoDB 专用，SQLite 不需要

from models.user import UserCreate, UserLogin, Token, UserResponse
from utils.security import get_password_hash, verify_password, create_access_token, get_current_user
from utils.rate_limiter import check_rate_limit
from utils.logger import logger
from database import get_database

router = APIRouter()


@router.post("/register")
async def register(user: UserCreate, request: Request):
    """用户注册"""
    # 速率限制检查
    await check_rate_limit(request, "register")
    
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                request.headers.get("X-Real-IP", "") or \
                (request.client.host if request.client else "unknown")
    
    try:
        db = get_database()
        
        # 检查用户名是否已存在
        existing_user = await db.users.find_one({"username": user.username})
        if existing_user:
            logger.auth_event("register", user.username, False, client_ip, "用户名已存在")
            raise HTTPException(
                status_code=400,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if user.email:
            existing_email = await db.users.find_one({"email": user.email})
            if existing_email:
                logger.auth_event("register", user.username, False, client_ip, "邮箱已被注册")
                raise HTTPException(
                    status_code=400,
                    detail="邮箱已被注册"
                )
        
        # 创建用户
        user_dict = user.dict(exclude={"password"})
        user_dict["hashed_password"] = get_password_hash(user.password)
        user_dict["role"] = user.role.value if hasattr(user.role, 'value') else user.role
        user_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        user_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        user_dict["last_login"] = None
        user_dict["profile"] = {"bio": None, "avatar_url": None}
        
        # 如果email为空，则不存储该字段
        if not user_dict.get("email"):
            user_dict.pop("email", None)
        
        result = await db.users.insert_one(user_dict)
        
        # 返回用户信息
        created_user = await db.users.find_one({"_id": result.inserted_id})
        created_user["id"] = str(created_user.pop("_id"))
        created_user.pop("hashed_password", None)
        
        logger.auth_event("register", user.username, True, client_ip)
        
        return {
            "status": "success",
            "code": 200,
            "message": "注册成功",
            "data": created_user
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"注册错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/login")
async def login(credentials: UserLogin, request: Request):
    """用户登录"""
    # 速率限制检查
    await check_rate_limit(request, "login")
    
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or \
                request.headers.get("X-Real-IP", "") or \
                (request.client.host if request.client else "unknown")
    
    try:
        db = get_database()
        
        # 查找用户
        user = await db.users.find_one({"username": credentials.username})
        if not user:
            logger.auth_event("login", credentials.username, False, client_ip, "用户名不存在")
            raise HTTPException(
                status_code=401,
                detail="用户名不存在，请先注册"
            )
        
        # 验证密码
        if not verify_password(credentials.password, user["hashed_password"]):
            logger.auth_event("login", credentials.username, False, client_ip, "密码错误")
            raise HTTPException(
                status_code=401,
                detail="密码错误，请重新输入"
            )
        
        # 更新最后登录时间
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        # 生成JWT令牌
        access_token = create_access_token(
            data={
                "sub": user["username"],
                "user_id": str(user["_id"]),
                "role": user["role"]
            }
        )
        
        # 准备用户响应
        user["id"] = str(user.pop("_id"))
        user.pop("hashed_password", None)
        
        logger.auth_event("login", credentials.username, True, client_ip)
        
        return {
            "status": "success",
            "code": 200,
            "message": "登录成功",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"登录错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"登录失败: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(request: Request, current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    try:
        db = get_database()
        
        # SQLite 使用整数 ID
        user_id = current_user["user_id"]
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            pass
        
        user = await db.users.find_one({"_id": user_id})
        if not user:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )
        
        user["id"] = str(user.pop("_id"))
        user.pop("hashed_password", None)
        
        return {
            "status": "success",
            "code": 200,
            "message": "获取成功",
            "data": user
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"获取用户信息错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )
