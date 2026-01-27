"""管理端认证模块

JWT Token 生成和验证，密码哈希处理
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.config import Config, get_config
from src.db import User, get_db

# HTTPBearer 认证方案
security = HTTPBearer()


class AuthService:
    """认证服务"""

    def __init__(self, config: Config):
        self.config = config
        self.secret_key = config.admin_secret_key
        self.expire_hours = config.admin_jwt_expire_hours
        self.algorithm = "HS256"

    def hash_password(self, password: str) -> str:
        """哈希密码

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码

        Args:
            password: 明文密码
            password_hash: 哈希密码

        Returns:
            bool: 密码是否正确
        """
        return bcrypt.checkpw(
            password.encode("utf-8"), password_hash.encode("utf-8")
        )

    def create_access_token(self, user_id: int, username: str) -> str:
        """创建 JWT Token

        Args:
            user_id: 用户ID
            username: 用户名

        Returns:
            str: JWT Token
        """
        expire = datetime.now(timezone.utc) + timedelta(
            hours=self.expire_hours
        )

        payload = {
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        """验证 JWT Token

        Args:
            token: JWT Token

        Returns:
            Optional[dict]: Token 载荷，如果无效则返回 None
        """
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def authenticate_user(
        self, username: str, password: str, db: Session
    ) -> Optional[User]:
        """认证用户

        Args:
            username: 用户名
            password: 密码
            db: 数据库会话

        Returns:
            Optional[User]: 用户对象，如果认证失败则返回 None
        """
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return None

        if not user.is_active:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # 更新最后登录时间
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        return user


# 全局认证服务实例
_auth_service: Optional[AuthService] = None


def get_auth_service(config: Config = Depends(get_config)) -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService(config)
    return _auth_service


# 依赖注入：获取当前用户
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """获取当前登录用户

    Args:
        credentials: HTTP 认证凭据
        db: 数据库会话
        auth_service: 认证服务

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials

    # 验证 Token
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# 依赖注入：要求管理员权限
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限

    Args:
        current_user: 当前用户

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 权限不足
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return current_user


def init_default_admin(db: Session, config: Config) -> None:
    """初始化默认管理员账户

    Args:
        db: 数据库会话
        config: 配置对象
    """
    # 检查是否已存在管理员
    existing_admin = (
        db.query(User)
        .filter(User.username == config.admin_default_username)
        .first()
    )

    if existing_admin:
        return

    # 创建默认管理员
    auth_service = AuthService(config)
    password_hash = auth_service.hash_password(config.admin_default_password)

    admin_user = User(
        username=config.admin_default_username,
        password_hash=password_hash,
        role="admin",
        is_active=True,
    )

    db.add(admin_user)
    db.commit()

    print(f"默认管理员账户已创建: {config.admin_default_username}")
