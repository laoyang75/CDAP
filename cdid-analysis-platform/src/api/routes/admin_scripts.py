"""管理端脚本编辑器路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.admin.auth import require_admin
from src.db import Script, User, get_db
from src.models.schemas import ScriptCreate, ScriptResponse

router = APIRouter(prefix="/api/admin/scripts", tags=["管理端-脚本管理"])


@router.get("", response_model=List[ScriptResponse])
async def list_scripts(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取所有脚本"""
    scripts = db.query(Script).all()
    return scripts


@router.post("", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    data: ScriptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建脚本"""
    script = Script(
        name=data.name,
        description=data.description,
        script_type=data.script_type,
        code=data.code,
        is_active=data.is_active,
        created_by=current_user.id,
    )

    db.add(script)
    db.commit()
    db.refresh(script)

    return script


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取脚本详情"""
    script = db.query(Script).filter(Script.id == script_id).first()

    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    return script


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    data: ScriptCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新脚本"""
    script = db.query(Script).filter(Script.id == script_id).first()

    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    script.name = data.name
    script.description = data.description
    script.script_type = data.script_type
    script.code = data.code
    script.is_active = data.is_active

    db.commit()
    db.refresh(script)

    return script


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除脚本"""
    script = db.query(Script).filter(Script.id == script_id).first()

    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")

    db.delete(script)
    db.commit()
