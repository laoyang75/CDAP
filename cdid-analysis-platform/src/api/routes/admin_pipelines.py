"""管理端流程管理路由"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.admin.auth import require_admin
from src.db import Pipeline, User, get_db
from src.models.schemas import PipelineCreate, PipelineResponse

router = APIRouter(prefix="/api/admin/pipelines", tags=["管理端-流程管理"])


@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取所有流程"""
    pipelines = db.query(Pipeline).order_by(Pipeline.created_at.desc()).all()
    return pipelines


@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    data: PipelineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """创建流程"""
    pipeline = Pipeline(
        name=data.name,
        description=data.description,
        config=data.config,
        is_active=data.is_active,
        created_by=current_user.id,
    )

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    return pipeline


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取流程详情"""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="流程不存在")
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(
    pipeline_id: int,
    data: PipelineCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新流程"""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流程不存在")

    pipeline.name = data.name
    pipeline.description = data.description
    pipeline.config = data.config
    pipeline.is_active = data.is_active

    db.commit()
    db.refresh(pipeline)
    return pipeline


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除流程"""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()

    if not pipeline:
        raise HTTPException(status_code=404, detail="流程不存在")

    db.delete(pipeline)
    db.commit()
