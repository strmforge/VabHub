"""
认证相关API
使用统一响应模型
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from loguru import logger

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.schemas import (
    BaseResponse,
    UnauthorizedResponse,
    success_response,
    error_response
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


class UserCreate(BaseModel):
    """用户创建请求"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    用户注册
    
    返回统一响应格式：
    {
        "success": true,
        "message": "注册成功",
        "data": UserResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        # 检查用户名是否已存在
        existing_user = await User.get_by_username(db, user_data.username)
        if existing_user:
            error_resp = error_response(
                error_code="USERNAME_EXISTS",
                error_message="用户名已存在"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_resp.model_dump(mode='json')  # 使用mode='json'确保datetime被序列化为字符串
            )
        
        # 检查邮箱是否已存在
        existing_email = await User.get_by_email(db, user_data.email)
        if existing_email:
            error_resp = error_response(
                error_code="EMAIL_EXISTS",
                error_message="邮箱已被注册"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_resp.model_dump(mode='json')  # 使用mode='json'确保datetime被序列化为字符串
            )
        
        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        await user.save(db)
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at
        )
        
        # 手动构建响应避免序列化问题
        return {
            "success": True,
            "message": "注册成功", 
            "data": user_response.model_dump(mode='json'),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"用户注册时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/login", response_model=BaseResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录
    
    返回统一响应格式：
    {
        "success": true,
        "message": "登录成功",
        "data": {
            "access_token": "...",
            "token_type": "bearer"
        },
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        user = await User.get_by_username(db, form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnauthorizedResponse(
                    error_code="INVALID_CREDENTIALS",
                    error_message="用户名或密码错误"
                ).model_dump(),
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_response(
                    error_code="USER_DISABLED",
                    error_message="用户已被禁用"
                ).model_dump()
            )
        
        # 创建访问令牌
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return success_response(
            data={
                "access_token": access_token,
                "token_type": "bearer"
            },
            message="登录成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"用户登录时发生错误: {str(e)}"
            ).model_dump()
        )


@router.get("/me", response_model=BaseResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户信息
    
    返回统一响应格式：
    {
        "success": true,
        "message": "获取成功",
        "data": UserResponse,
        "timestamp": "2025-01-XX..."
    }
    """
    try:
        from app.core.security import decode_access_token
        
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnauthorizedResponse(
                    error_code="INVALID_TOKEN",
                    error_message="无效的认证凭据"
                ).model_dump()
            )
        
        user = await User.get_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=UnauthorizedResponse(
                    error_code="USER_NOT_FOUND",
                    error_message="用户不存在"
                ).model_dump()
            )
        
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at
        )
        
        return success_response(data=user_response.model_dump(), message="获取成功")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                error_code="INTERNAL_SERVER_ERROR",
                error_message=f"获取当前用户信息时发生错误: {str(e)}"
            ).model_dump()
        )


@router.post("/logout", response_model=BaseResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    用户登出
    
    返回统一响应格式：
    {
        "success": true,
        "message": "登出成功",
        "data": null,
        "timestamp": "2025-01-XX..."
    }
    
    注意：由于JWT是无状态的，登出主要是客户端删除token。
    这里可以记录登出日志或实现token黑名单（如果需要）。
    """
    try:
        from app.core.security import decode_access_token
        
        # 验证token（确保token有效）
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        
        if username:
            logger.info(f"用户登出: {username}")
            # 可以在这里实现token黑名单机制（如果需要）
            # 或者记录登出日志
        
        return success_response(message="登出成功")
    except HTTPException:
        raise
    except Exception as e:
        # 即使token无效，也允许登出（客户端清理token）
        logger.warning(f"登出时token验证失败（允许登出）: {e}")
        return success_response(message="登出成功")

