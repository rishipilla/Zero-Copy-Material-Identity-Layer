from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/identities", tags=["identities"])


@router.get("/{identity_id}", response_model=schemas.IdentityDetailOut)
def get_identity(identity_id: str, db: Session = Depends(get_db)):
    identity = db.query(models.MaterialIdentity).get(identity_id)
    if not identity:
        raise HTTPException(status_code=404, detail="identity not found")
    matches = db.query(models.MaterialMatch).filter_by(identity_id=identity_id, status="accepted").all()
    material_ids = {material_id for match in matches for material_id in (match.material_a, match.material_b)}
    members = db.query(models.Material).filter(models.Material.id.in_(material_ids)).all() if material_ids else []
    return schemas.IdentityDetailOut(id=identity.id, canonical_name=identity.canonical_name, category=identity.category, members=members)
