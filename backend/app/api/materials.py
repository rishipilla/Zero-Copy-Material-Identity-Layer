from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.material import Material
from app.models.material_identity import MaterialIdentity

from app.services.ingestion import import_materials
from app.services.matcher import run_matching
from app.services.identity import build_identities

from app.services.graph import (
    clear_identity_graph,
    create_material_node,
    create_identity_node,
    create_identity_membership,
)


router = APIRouter(
    prefix="/api/materials",
    tags=["materials"],
)


@router.post("/import")
async def import_materials_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A CSV file is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    content = await file.read()

    try:
        count = import_materials(content, db)

        return {
            "message": "Materials imported successfully.",
            "imported_count": count,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/match")
def match_materials(
    db: Session = Depends(get_db),
):
    try:
        results = run_matching(db)

        return {
            "message": "Material matching completed successfully.",
            "matched_pairs": len(results),
            "results": results,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/identities")
def create_material_identities(
    db: Session = Depends(get_db),
):
    try:
        identities = build_identities(db)

        return {
            "message": "Material identities created successfully.",
            "identity_count": len(identities),
            "identities": identities,
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/graph")
def create_material_graph(
    db: Session = Depends(get_db),
):
    try:
        # Remove old Identity nodes and their relationships.
        # Material nodes are preserved.
        clear_identity_graph()

        # Load all materials from PostgreSQL.
        materials = (
            db.query(Material)
            .order_by(Material.id)
            .all()
        )

        # Create or update Material nodes in Neo4j.
        for material in materials:
            create_material_node(
                material_id=material.id,
                description=material.description or "",
                category=material.category,
            )

        # Load current identities from PostgreSQL.
        identities = (
            db.query(MaterialIdentity)
            .order_by(MaterialIdentity.identity_id)
            .all()
        )

        # Create Identity nodes in Neo4j.
        for identity in identities:
            create_identity_node(
                identity_id=identity.identity_id,
                canonical_name=identity.canonical_name,
                category=identity.category,
                status=identity.status,
            )

        # Load identity-material memberships.
        membership_rows = (
            db.execute(
                text(
                    """
                    SELECT identity_id, material_id
                    FROM material_identity_members
                    ORDER BY identity_id, material_id
                    """
                )
            )
            .fetchall()
        )

        # Create Identity -> Material relationships.
        for identity_id, material_id in membership_rows:
            create_identity_membership(
                identity_id=identity_id,
                material_id=material_id,
            )

        return {
            "message": "Material and identity graph created successfully.",
            "material_node_count": len(materials),
            "identity_node_count": len(identities),
            "membership_count": len(membership_rows),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )