import os

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.importer import import_csv
from app.services.extract import extract_attributes, attributes_to_rows
from app.services import neo4j_sync
from app.services.graph import clear_identity_graph

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
    """Loads the bundled synthetic ERP datasets to populate the pipeline
    from the committed seed data without requiring an external CSV upload."""
    results = []

    for fname, source in [
        ("erp_a_sap.csv", "SAP-A"),
        ("erp_b_sap.csv", "SAP-B"),
        ("erp_c_legacy.csv", "LEGACY-ERP"),
    ]:
        path = os.path.join(SAMPLE_DIR, fname)

        if not os.path.exists(path):
            raise HTTPException(
                status_code=500,
                detail=f"missing sample file {fname}",
            )

        with open(path, "rb") as f:
            results.append(import_csv(db, source, f.read()))

    return results


@router.get("", response_model=list[schemas.MaterialOut])
def list_materials(
    source_system: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Material)

    if source_system:
        q = q.filter_by(source_system=source_system)

    return q.order_by(
        models.Material.created_at.desc()
    ).all()


@router.post("/reextract")
def reextract_attributes(db: Session = Depends(get_db)):
    """
    Re-extract derived attributes for all existing materials.

    This does NOT modify:
    - source material descriptions
    - source systems
    - legacy codes
    - identities
    - accepted matches
    - rejected matches

    It only refreshes the derived material_attributes records.
    """

    materials = db.query(models.Material).all()

    updated = 0
    attributes_created = 0

    for material in materials:
        # Remove existing derived attributes for this material.
        db.query(models.MaterialAttribute).filter_by(
            material_id=material.id
        ).delete(synchronize_session=False)

        # Run the latest extractor against the stored description.
        attrs = extract_attributes(
            material.description or ""
        )

        rows = attributes_to_rows(attrs)

        for row in rows:
            db.add(
                models.MaterialAttribute(
                    material_id=material.id,
                    attribute_name=row["attribute_name"],
                    attribute_value=row["attribute_value"],
                    normalized_value=row["normalized_value"],
                )
            )

        updated += 1
        attributes_created += len(rows)

    db.commit()

    return {
        "status": "reextracted",
        "materials_updated": updated,
        "attributes_created": attributes_created,
    }


@router.delete("/reset")
def reset_all(db: Session = Depends(get_db)):
    """Wipe the demo dataset (materials, attributes, matches, identities).
    Never touches anything outside this app's own tables. If Neo4j is
    configured, clear that identity graph projection as well so the
    PostgreSQL source-of-truth and the graph mirror stay consistent."""

    if neo4j_sync.is_enabled():
        try:
            clear_identity_graph()
        except Exception:
            # Neo4j is optional; reset should remain safe and idempotent.
            pass

    db.query(models.MaterialMatch).delete()
    db.query(models.MaterialIdentity).delete()
    db.query(models.MaterialAttribute).delete()
    db.query(models.Material).delete()

    db.commit()

    return {"status": "reset"}


@router.get("/{material_id}", response_model=schemas.MaterialDetailOut)
def get_material(
    material_id: str,
    db: Session = Depends(get_db),
):
    material = db.query(models.Material).get(material_id)

    if not material:
        raise HTTPException(
            status_code=404,
            detail="material not found",
        )

    state = (
        db.query(models.MaterialSourceState)
        .filter_by(material_id=material.id)
        .first()
    )

    return schemas.MaterialDetailOut(
        **schemas.MaterialOut.model_validate(material).model_dump(),
        source_reference=(
            state.source_reference
            if state
            else f"{material.source_system}:{material.legacy_code}"
        ),
        source_updated_at=(
            state.source_updated_at
            if state
            else None
        ),
        ingested_at=(
            state.ingested_at
            if state
            else material.created_at
        ),
        previous_description=(
            state.previous_description
            if state
            else None
        ),
        source_changed=(
            state.last_change_detected == "true"
            if state
            else False
        ),
    )