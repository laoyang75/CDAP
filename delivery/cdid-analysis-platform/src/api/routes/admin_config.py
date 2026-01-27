"""管理端配置管理路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.admin.auth import require_admin
from src.db import ClientConfig, User, get_db
from src.models.schemas import ClientConfigResponse, ClientConfigUpdate

router = APIRouter(prefix="/api/admin/config", tags=["管理端-配置管理"])


@router.get("", response_model=List[ClientConfigResponse])
async def list_configs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取所有配置"""
    configs = db.query(ClientConfig).all()
    return configs


@router.put("/{config_id}", response_model=ClientConfigResponse)
async def update_config(
    config_id: int,
    data: ClientConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新配置"""
    config = db.query(ClientConfig).filter(ClientConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    config.key = data.key
    config.value = data.value
    config.description = data.description

    db.commit()
    db.refresh(config)

    return config
