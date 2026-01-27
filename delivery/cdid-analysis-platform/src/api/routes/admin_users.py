"""管理端用户管理路由

用户 CRUD 操作
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.admin.auth import (
    AuthService,
    get_auth_service,
    require_admin,
)
from src.db import User, get_db
from src.models.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/api/admin/users", tags=["管理端-用户管理"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取用户列表（需要管理员权限）

    Args:
        skip: 跳过数量
        limit: 返回数量限制
        db: 数据库会话

    Returns:
        List[UserResponse]: 用户列表
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    _: User = Depends(require_admin),
):
    """创建用户（需要管理员权限）

    Args:
        user_data: 用户数据
        db: 数据库会话
        auth_service: 认证服务

    Returns:
        UserResponse: 创建的用户
    """
    # 检查用户名是否已存在
    existing_user = (
        db.query(User).filter(User.username == user_data.username).first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # 创建用户
    password_hash = auth_service.hash_password(user_data.password)

    user = User(
        username=user_data.username,
        password_hash=password_hash,
        email=user_data.email,
        role=user_data.role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取用户详情（需要管理员权限）

    Args:
        user_id: 用户ID
        db: 数据库会话

    Returns:
        UserResponse: 用户信息
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除用户（需要管理员权限）

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户

    Raises:
        HTTPException: 用户不存在或不允许删除自己
    """
    # 不允许删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    db.delete(user)
    db.commit()


@router.patch("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """切换用户激活状态（需要管理员权限）

    Args:
        user_id: 用户ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        UserResponse: 更新后的用户信息
    """
    # 不允许禁用自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    return user
