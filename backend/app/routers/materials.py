import os

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.importer import import_csv

router = APIRouter(prefix="/api/materials", tags=["materials"])

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data")


@router.post("/import", response_model=schemas.ImportSummary)
def import_materials(
    source_system: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        content = file.file.read()
        result = import_csv(db, source_system, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/import-sample", response_model=list[schemas.ImportSummary])
def import_sample_data(db: Session = Depends(get_db)):
    """Loads the two bundled synthetic ERP datasets — the fastest way to see
    the whole pipeline work end to end without preparing your own CSVs."""
    results = []
    for fname, source in [("erp_a_sap.csv", "SAP-A"), ("erp_b_sap.csv", "SAP-B")]:
        path = os.path.join(SAMPLE_DIR, fname)
        if not os.path.exists(path):
            raise HTTPException(status_code=500, detail=f"missing sample file {fname}")
        with open(path, "rb") as f:
            results.append(import_csv(db, source, f.read()))
    return results


@router.get("", response_model=list[schemas.MaterialOut])
def list_materials(source_system: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Material)
    if source_system:
        q = q.filter_by(source_system=source_system)
    return q.order_by(models.Material.created_at.desc()).all()


@router.delete("/reset")
def reset_all(db: Session = Depends(get_db)):
    """Wipe the demo dataset (materials, attributes, matches, identities).
    Never touches anything outside this app's own tables."""
    db.query(models.MaterialMatch).delete()
    db.query(models.MaterialIdentity).delete()
    db.query(models.MaterialAttribute).delete()
    db.query(models.Material).delete()
    db.commit()
    return {"status": "reset"}


@router.get("/{material_id}", response_model=schemas.MaterialDetailOut)
def get_material(material_id: str, db: Session = Depends(get_db)):
    material = db.query(models.Material).get(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="material not found")
    state = db.query(models.MaterialSourceState).filter_by(material_id=material.id).first()
    return schemas.MaterialDetailOut(
        **schemas.MaterialOut.model_validate(material).model_dump(),
        source_reference=state.source_reference if state else f"{material.source_system}:{material.legacy_code}",
        source_updated_at=state.source_updated_at if state else None,
        ingested_at=state.ingested_at if state else material.created_at,
        previous_description=state.previous_description if state else None,
        source_changed=state.last_change_detected == "true" if state else False,
    )
