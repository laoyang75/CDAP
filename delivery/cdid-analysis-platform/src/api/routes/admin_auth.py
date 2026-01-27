"""管理端认证路由

登录、登出等认证相关端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.admin.auth import AuthService, get_auth_service, get_current_user
from src.db import User, get_db
from src.models.schemas import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/api/admin/auth", tags=["管理端-认证"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
):
    """管理员登录

    Args:
        request: 登录请求
        db: 数据库会话
        auth_service: 认证服务

    Returns:
        LoginResponse: 包含 access_token 和用户信息
    """
    # 认证用户
    user = auth_service.authenticate_user(request.username, request.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 生成 Token
    access_token = auth_service.create_access_token(user.id, user.username)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息

    Args:
        current_user: 当前用户

    Returns:
        UserResponse: 用户信息
    """
    return current_user
