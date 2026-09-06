import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services import neo4j_sync

router = APIRouter(prefix="/api/matches", tags=["matches"])


def _existing_identity_for(db: Session, material_id: str) -> str | None:
    m = db.query(models.MaterialMatch).filter(
        models.MaterialMatch.status == "accepted",
        models.MaterialMatch.identity_id.isnot(None),
        (models.MaterialMatch.material_a == material_id) | (models.MaterialMatch.material_b == material_id),
    ).first()
    return m.identity_id if m else None


@router.get("", response_model=list[schemas.MatchOut])
def list_matches(status: str = "pending", db: Session = Depends(get_db)):
    q = db.query(models.MaterialMatch)
    if status != "all":
        q = q.filter_by(status=status)
    matches = q.order_by(models.MaterialMatch.final_confidence.desc()).all()

    out = []
    for m in matches:
        out.append(schemas.MatchOut(
            id=m.id, material_a=m.material_a, material_b=m.material_b,
            material_a_detail=db.query(models.Material).get(m.material_a),
            material_b_detail=db.query(models.Material).get(m.material_b),
            semantic_score=m.semantic_score, attribute_score=m.attribute_score,
            rule_score=m.rule_score, final_confidence=m.final_confidence,
            conflict_reason=m.conflict_reason, status=m.status, identity_id=m.identity_id,
        ))
    return out


@router.post("/{match_id}/resolve", response_model=schemas.MatchOut)
def resolve_match(match_id: str, body: schemas.ResolveMatchIn, db: Session = Depends(get_db)):
    match = db.query(models.MaterialMatch).get(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="match not found")
    if match.status != "pending":
        raise HTTPException(status_code=400, detail=f"match already {match.status}")

    if body.action == "reject":
        match.status = "rejected"
        match.resolved_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(match)

    elif body.action == "accept":
        identity_id = _existing_identity_for(db, match.material_a) or _existing_identity_for(db, match.material_b)

        if not identity_id:
            mat_a = db.query(models.Material).get(match.material_a)
            name = body.canonical_name or mat_a.normalized_description or mat_a.description
            identity = models.MaterialIdentity(canonical_name=name, category=mat_a.category)
            db.add(identity)
            db.flush()
            identity_id = identity.id
            neo4j_sync.sync_identity(identity_id, identity.canonical_name, identity.category)

        match.status = "accepted"
        match.identity_id = identity_id
        match.resolved_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(match)

        for mat_id in (match.material_a, match.material_b):
            material = db.query(models.Material).get(mat_id)
            neo4j_sync.sync_material_link(
                identity_id, mat_id, material.source_system, material.legacy_code, match.final_confidence
            )
    else:
        raise HTTPException(status_code=400, detail="action must be 'accept' or 'reject'")

    return schemas.MatchOut(
        id=match.id, material_a=match.material_a, material_b=match.material_b,
        material_a_detail=db.query(models.Material).get(match.material_a),
        material_b_detail=db.query(models.Material).get(match.material_b),
        semantic_score=match.semantic_score, attribute_score=match.attribute_score,
        rule_score=match.rule_score, final_confidence=match.final_confidence,
        conflict_reason=match.conflict_reason, status=match.status, identity_id=match.identity_id,
    )
