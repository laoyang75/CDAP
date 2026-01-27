"""Pydantic 模型定义

用于 API 请求和响应的数据模型
"""

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer


class JobCreate(BaseModel):
    """创建任务请求"""

    name: str = Field(..., description="任务名称", max_length=255)
    package_name: str = Field(..., description="包名", max_length=255)
    start_date: str = Field(..., description="开始日期 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., description="结束日期 (YYYY-MM-DD)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    message_types: List[str] = Field(..., description="消息类型列表")


class JobResponse(BaseModel):
    """任务响应"""

    id: str
    name: str
    package_name: str
    start_date: str
    end_date: str
    message_types: List[str]
    status: str
    progress: int
    progress_message: str
    input_file_path: Optional[str] = None
    raw_data_path: Optional[str] = None
    report_path: Optional[str] = None
    error: Optional[str] = None
    insight_task_id: Optional[str] = None
    pipeline_ids: Optional[List[int]] = None
    cancel_requested: bool = False
    active_pid: Optional[int] = None
    active_step: Optional[str] = None
    active_started_at: Optional[datetime] = None
    debug_mode: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("created_at", "updated_at", "active_started_at")
    def serialize_datetime(self, value: datetime):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class JobListResponse(BaseModel):
    """任务列表响应"""

    total: int
    jobs: List[JobResponse]


class UserCreate(BaseModel):
    """创建用户请求（管理端）"""

    username: str = Field(..., description="用户名", max_length=50)
    password: str = Field(..., description="密码", min_length=6)
    email: Optional[str] = Field(None, description="邮箱", max_length=100)
    role: str = Field(default="user", description="角色")


class UserResponse(BaseModel):
    """用户响应（管理端）"""

    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

    @field_serializer("created_at", "last_login")
    def serialize_datetime(self, value: Optional[datetime]):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class LoginRequest(BaseModel):
    """登录请求（管理端）"""

    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应（管理端）"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class PipelineCreate(BaseModel):
    """创建流程请求（管理端）"""

    name: str = Field(..., description="流程名称", max_length=100)
    description: Optional[str] = Field(None, description="流程描述")
    config: dict = Field(..., description="流程配置")
    is_active: bool = Field(default=True, description="是否启用")


class PipelineResponse(BaseModel):
    """流程响应（管理端）"""

    id: int
    name: str
    description: Optional[str]
    config: dict
    is_active: bool
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("created_at")
    def serialize_datetime(self, value: datetime):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class PipelinePublicResponse(BaseModel):
    """管线列表（用户端）"""

    id: int
    name: str
    description: Optional[str] = None
    is_default: bool = False


class ScriptCreate(BaseModel):
    """创建脚本请求（管理端）"""

    name: str = Field(..., description="脚本名称", max_length=100)
    description: Optional[str] = Field(None, description="脚本描述")
    script_type: str = Field(..., description="脚本类型")
    code: str = Field(..., description="Python 代码")
    is_active: bool = Field(default=True, description="是否启用")


class ScriptResponse(BaseModel):
    """脚本响应（管理端）"""

    id: int
    name: str
    description: Optional[str]
    script_type: str
    code: str
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class ClientConfigUpdate(BaseModel):
    """更新客户端配置请求（管理端）"""

    key: str = Field(..., description="配置键", max_length=100)
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置说明", max_length=255)


class ClientConfigResponse(BaseModel):
    """客户端配置响应（管理端）"""

    id: int
    key: str
    value: str
    description: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer("updated_at")
    def serialize_datetime(self, value: datetime):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
