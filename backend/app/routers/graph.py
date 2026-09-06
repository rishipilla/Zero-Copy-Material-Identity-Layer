from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.graph import build_graph
from app.services import neo4j_sync

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("", response_model=schemas.GraphOut)
def get_graph(db: Session = Depends(get_db)):
    return build_graph(db)


@router.get("/status")
def graph_status():
    return {"neo4j_enabled": neo4j_sync.is_enabled()}


analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@analytics_router.get("", response_model=schemas.AnalyticsOut)
def get_analytics(db: Session = Depends(get_db)):
    total_materials = db.query(models.Material).count()
    total_identities = db.query(models.MaterialIdentity).count()
    pending = db.query(models.MaterialMatch).filter_by(status="pending").count()
    accepted = db.query(models.MaterialMatch).filter_by(status="accepted").count()
    rejected = db.query(models.MaterialMatch).filter_by(status="rejected").count()
    conflicts = db.query(models.MaterialMatch).filter(
        models.MaterialMatch.conflict_reason.isnot(None)
    ).count()

    source_systems = {}
    for row in db.query(models.Material.source_system, models.Material.id).all():
        source_systems[row[0]] = source_systems.get(row[0], 0) + 1

    return schemas.AnalyticsOut(
        total_materials=total_materials,
        total_identities=total_identities,
        pending_candidates=pending,
        accepted_matches=accepted,
        rejected_matches=rejected,
        conflicts_flagged=conflicts,
        source_systems=source_systems,
    )
