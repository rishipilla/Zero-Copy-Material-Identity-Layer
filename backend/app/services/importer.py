import csv
import io
import itertools

from sqlalchemy.orm import Session

from app import models
from app.services.normalize import normalize_description
from app.services.extract import extract_attributes, attributes_to_rows
from app.services.matching import (
    semantic_similarity_matrix,
    attribute_score,
    detect_conflict,
    rule_score,
    hybrid_confidence,
)
from app.config import settings


REQUIRED_COLUMNS = {
    "source_system",
    "legacy_code",
    "description",
}


def import_csv(
    db: Session,
    source_system: str,
    csv_bytes: bytes,
) -> dict:
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    fieldnames = {
        h.strip()
        for h in (reader.fieldnames or [])
        if h
    }

    if not REQUIRED_COLUMNS.issubset(fieldnames):
        raise ValueError(
            f"CSV must include columns: {sorted(REQUIRED_COLUMNS)}"
        )

    imported = 0
    skipped = 0

    for row in reader:
        legacy_code = (
            row.get("legacy_code") or ""
        ).strip()

        description = (
            row.get("description") or ""
        ).strip()

        if not legacy_code or not description:
            skipped += 1
            continue

        # Use the source_system from the CSV when present.
        # The form value is used only as a fallback.
        row_source_system = (
            row.get("source_system") or source_system
        ).strip()

        if not row_source_system:
            skipped += 1
            continue

        # Prevent duplicate imports of the same source record.
        exists = (
            db.query(models.Material)
            .filter_by(
                source_system=row_source_system,
                legacy_code=legacy_code,
            )
            .first()
        )

        if exists:
            skipped += 1
            continue

        normalized = normalize_description(
            description
        )

        material = models.Material(
            source_system=row_source_system,
            legacy_code=legacy_code,
            description=description,
            normalized_description=normalized,
            manufacturer=(
                row.get("manufacturer") or ""
            ).strip() or None,
            category=(
                row.get("category") or ""
            ).strip() or None,
            unit=(
                row.get("unit") or ""
            ).strip() or None,
            specifications=(
                row.get("specifications") or ""
            ).strip() or None,
        )

        db.add(material)
        db.flush()

        attrs = extract_attributes(description)

        for attr_row in attributes_to_rows(attrs):
            db.add(
                models.MaterialAttribute(
                    material_id=material.id,
                    **attr_row,
                )
            )

        imported += 1

    db.commit()

    # Generate cross-source match candidates.
    matches_generated = generate_candidates(db)

    return {
        "source_system": source_system,
        "imported": imported,
        "skipped": skipped,
        "matches_generated": matches_generated,
    }


def _material_attr_dict(
    db: Session,
    material_id: str,
) -> dict:
    rows = (
        db.query(models.MaterialAttribute)
        .filter_by(material_id=material_id)
        .all()
    )

    return {
        row.attribute_name: (
            row.normalized_value
            or row.attribute_value
        )
        for row in rows
    }


def generate_candidates(db: Session) -> int:
    """
    Generate match candidates between materials
    belonging to different source systems.

    The matcher combines:
    - semantic similarity
    - attribute similarity
    - conflict detection
    - rule score
    - hybrid confidence

    At hackathon/demo scale this pairwise approach
    is sufficient.
    """

    materials = (
        db.query(models.Material)
        .order_by(models.Material.id)
        .all()
    )

    if len(materials) < 2:
        return 0

    existing_pairs = set()

    for match in db.query(models.MaterialMatch).all():
        existing_pairs.add(
            frozenset(
                (
                    match.material_a,
                    match.material_b,
                )
            )
        )

    descriptions = [
        material.normalized_description
        or material.description
        or ""
        for material in materials
    ]

    sim_matrix = semantic_similarity_matrix(
        descriptions
    )

    created = 0

    for i, j in itertools.combinations(
        range(len(materials)),
        2,
    ):
        material_a = materials[i]
        material_b = materials[j]

        # Only compare records coming from different
        # source systems.
        if (
            material_a.source_system
            == material_b.source_system
        ):
            continue

        pair = frozenset(
            (
                material_a.id,
                material_b.id,
            )
        )

        if pair in existing_pairs:
            continue

        semantic = float(
            sim_matrix[i][j]
        )

        attributes_a = _material_attr_dict(
            db,
            material_a.id,
        )

        attributes_b = _material_attr_dict(
            db,
            material_b.id,
        )

        attribute_sc = attribute_score(
            attributes_a,
            attributes_b,
        )

        conflict = detect_conflict(
            attributes_a,
            attributes_b,
        )

        rule_sc = rule_score(conflict)

        confidence = hybrid_confidence(
            semantic,
            attribute_sc,
            rule_sc,
        )

        # Surface plausible matches.
        is_plausible = (
            confidence >= settings.MATCH_FLOOR
        )

        # Also surface meaningful conflicts when
        # semantic similarity is high enough.
        is_worth_a_look = (
            conflict
            and semantic
            >= settings.CONFLICT_SEMANTIC_FLOOR
        )

        if not is_plausible and not is_worth_a_look:
            continue

        db.add(
            models.MaterialMatch(
                material_a=material_a.id,
                material_b=material_b.id,
                semantic_score=round(
                    semantic,
                    4,
                ),
                attribute_score=round(
                    attribute_sc,
                    4,
                ),
                rule_score=round(
                    rule_sc,
                    4,
                ),
                final_confidence=confidence,
                conflict_reason=conflict,
                status="pending",
            )
        )

        created += 1

    db.commit()

    return created