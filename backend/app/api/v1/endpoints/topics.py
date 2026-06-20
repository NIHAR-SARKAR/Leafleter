"""Topic workspace endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Response, status

from app.core.deps import ActiveUserDep, DbDep, OrgIdDep, require_permissions
from app.core.exceptions import ForbiddenException
from app.core.logging import get_logger
from app.crud.topic import (
    analysis_run_repository,
    topic_repository,
    topic_source_repository,
)
from app.models.user import User
from app.schemas.topic import (
    AnalysisRunInDB,
    TopicAnalyzeRequest,
    TopicCreate,
    TopicPublic,
    TopicSourceCreate,
    TopicSourceInDB,
    TopicSourceUpdate,
    TopicUpdate,
)
from app.services.analysis_service import analysis_service
from app.services.intelligence_hooks import on_topic_created, on_topic_deleted, on_topic_updated
from app.services.search_service import search_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=list[TopicPublic])
async def list_topics(
    db: DbDep,
    org_id: OrgIdDep,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List topics for the organization."""
    topics = await topic_repository.get_multi(
        db, organization_id=org_id, skip=skip, limit=limit
    )
    return topics


@router.post("", response_model=TopicPublic, status_code=status.HTTP_201_CREATED)
async def create_topic(
    db: DbDep,
    org_id: OrgIdDep,
    obj_in: TopicCreate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Create a new topic workspace."""
    topic = await topic_repository.create(
        db,
        obj_in={
            **obj_in.model_dump(),
            "organization_id": org_id,
            "created_by_user_id": current_user.id,
            "status": "active",
        },
    )
    await db.commit()
    await db.refresh(topic)
    logger.info("topic_created", topic_id=topic.id, organization_id=org_id)
    try:
        on_topic_created(topic)
    except Exception as exc:
        logger.warning("intelligence_topic_created_hook_failed", error=str(exc))
    return topic


@router.get("/{topic_id}", response_model=TopicPublic)
async def get_topic(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    current_user: ActiveUserDep,
) -> Any:
    """Get a specific topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    return topic


@router.put("/{topic_id}", response_model=TopicPublic)
async def update_topic(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    obj_in: TopicUpdate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Update a topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    old_data = {
        "name": topic.name,
        "status": topic.status,
        "keywords": topic.keywords,
    }
    topic = await topic_repository.update(
        db, db_obj=topic, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(topic)
    try:
        on_topic_updated(topic, old_data=old_data)
    except Exception as exc:
        logger.warning("intelligence_topic_updated_hook_failed", error=str(exc))
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    current_user: User = Depends(require_permissions("topics:write")),
) -> None:
    """Soft delete a topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    topic_id_str = str(topic.id)
    await topic_repository.delete(db, db_obj=topic)
    await db.commit()
    try:
        on_topic_deleted(topic_id_str)
    except Exception as exc:
        logger.warning("intelligence_topic_deleted_hook_failed", error=str(exc))
    return None


@router.post("/{topic_id}/sources", response_model=TopicSourceInDB, status_code=status.HTTP_201_CREATED)
async def add_topic_source(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    obj_in: TopicSourceCreate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Add a source to a topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    source = await topic_source_repository.create(
        db,
        obj_in={
            **obj_in.model_dump(),
            "topic_id": topic.id,
            "fetch_status": "pending",
            "created_by_id": current_user.id,
        },
    )

    if obj_in.source_type == "search" and obj_in.query:
        source = await search_service.add_search_source(
            db,
            topic_id=topic.id,
            query=obj_in.query,
            engine_type=(obj_in.platform or "serpapi"),
            organization_id=org_id,
            created_by_id=current_user.id,
        )
    else:
        await db.commit()
        await db.refresh(source)

    return source


@router.put("/{topic_id}/sources/{source_id}", response_model=TopicSourceInDB)
async def update_topic_source(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    source_id: int,
    obj_in: TopicSourceUpdate,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Update a topic source."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    source = await topic_source_repository.get_or_404(db, source_id)
    if source.topic_id != topic.id:
        raise ForbiddenException("Source does not belong to topic")
    source = await topic_source_repository.update(
        db, db_obj=source, obj_in=obj_in.model_dump(exclude_unset=True)
    )
    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{topic_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic_source(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    source_id: int,
    current_user: User = Depends(require_permissions("topics:write")),
) -> None:
    """Delete a topic source."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    source = await topic_source_repository.get_or_404(db, source_id)
    if source.topic_id != topic.id:
        raise ForbiddenException("Source does not belong to topic")
    await topic_source_repository.delete(db, db_obj=source)
    await db.commit()
    return None


@router.post("/{topic_id}/analyze", response_model=AnalysisRunInDB)
async def analyze_topic(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    obj_in: TopicAnalyzeRequest,
    current_user: User = Depends(require_permissions("topics:write")),
) -> Any:
    """Run AI analysis on a topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    run = await analysis_service.run_analysis(
        db, topic=topic, obj_in=obj_in, user=current_user
    )
    return run


@router.get("/{topic_id}/runs", response_model=list[AnalysisRunInDB])
async def list_topic_analysis_runs(
    db: DbDep,
    org_id: OrgIdDep,
    topic_id: int,
    current_user: ActiveUserDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List analysis runs for a topic."""
    topic = await topic_repository.get_or_404_for_organization(db, topic_id, org_id)
    runs = await analysis_run_repository.get_by_topic(db, topic.id, skip=skip, limit=limit)
    return runs
