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


# Required columns for imported CSV files.
REQUIRED_COLUMNS = {
    "legacy_code",
    "description",
}

# Maximum number of candidates shown to a human reviewer.
# Keeping this small keeps the review experience focused.
MAX_REVIEW_CANDIDATES = 10


def normalize_category(
    category: str | None,
) -> str:
    """
    Normalize category names so small ERP naming differences
    do not prevent otherwise valid matches.

    Examples:
        Fastener  -> fastener
        Fasteners -> fastener
        Electrical -> electrical
    """

    if not category:
        return ""

    value = category.strip().lower()

    if value.endswith("ies"):
        value = value[:-3] + "y"

    elif value.endswith("s") and not value.endswith("ss"):
        value = value[:-1]

    return value


def categories_compatible(
    category_a: str | None,
    category_b: str | None,
) -> bool:
    """
    Prevent obviously unrelated material categories from
    becoming match candidates.

    Missing categories are allowed so the matcher can still
    use descriptions and structured attributes.
    """

    a = normalize_category(category_a)
    b = normalize_category(category_b)

    if not a or not b:
        return True

    return a == b


def import_csv(
    db: Session,
    source_system: str,
    csv_bytes: bytes,
    generate_matches: bool = True,
) -> dict:
    """
    Import material records from a CSV file.

    generate_matches=True:
        Generate candidates immediately.

    generate_matches=False:
        Import only. This is used by the bundled seed route so
        multiple source systems can be imported first and
        candidates generated once across the complete dataset.
    """

    text = csv_bytes.decode("utf-8-sig")

    reader = csv.DictReader(
        io.StringIO(text)
    )

    fieldnames = {
        h.strip()
        for h in (reader.fieldnames or [])
        if h
    }

    if not REQUIRED_COLUMNS.issubset(fieldnames):
        raise ValueError(
            f"CSV must include columns: "
            f"{sorted(REQUIRED_COLUMNS)}"
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

        # A CSV row may optionally contain source_system.
        # Otherwise use the source_system supplied by the caller.
        row_source_system = (
            row.get("source_system")
            or source_system
        ).strip()

        if not row_source_system:
            skipped += 1
            continue

        # Avoid importing the same source record twice.
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

        # Extract structured attributes from the original
        # description and store them separately.
        attrs = extract_attributes(
            description
        )

        for attr_row in attributes_to_rows(attrs):
            db.add(
                models.MaterialAttribute(
                    material_id=material.id,
                    **attr_row,
                )
            )

        imported += 1

    db.commit()

    # Generate candidates only when requested.
    matches_generated = (
        generate_candidates(db)
        if generate_matches
        else 0
    )

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
    """
    Return extracted attributes for one material.
    """

    rows = (
        db.query(models.MaterialAttribute)
        .filter_by(
            material_id=material_id
        )
        .all()
    )

    return {
        row.attribute_name: (
            row.normalized_value
            or row.attribute_value
        )
        for row in rows
    }


def generate_candidates(
    db: Session,
) -> int:
    """
    Generate the strongest cross-source candidate matches.

    Process:

    1. Load all materials.
    2. Never compare records from the same source.
    3. Never recreate an existing pair.
    4. Require compatible categories.
    5. Calculate semantic similarity.
    6. Calculate structured attribute similarity.
    7. Detect deterministic hard conflicts.
    8. Exclude hard-conflict pairs.
    9. Calculate hybrid confidence.
    10. Apply MATCH_FLOOR.
    11. Rank every eligible candidate.
    12. Keep only the top 10.
    13. Add them to the human-review queue.

    This means the UI always gets a focused set of
    high-quality candidates instead of dozens of records.
    """

    materials = (
        db.query(models.Material)
        .order_by(models.Material.id)
        .all()
    )

    if len(materials) < 2:
        return 0

    # ---------------------------------------------------------
    # EXISTING PAIRS
    # ---------------------------------------------------------

    existing_pairs = set()

    for match in (
        db.query(models.MaterialMatch)
        .all()
    ):
        existing_pairs.add(
            frozenset(
                (
                    match.material_a,
                    match.material_b,
                )
            )
        )

    # ---------------------------------------------------------
    # DESCRIPTION VECTORS
    # ---------------------------------------------------------

    descriptions = [
        material.normalized_description
        or material.description
        or ""
        for material in materials
    ]

    sim_matrix = semantic_similarity_matrix(
        descriptions
    )

    # ---------------------------------------------------------
    # ATTRIBUTE CACHE
    # ---------------------------------------------------------

    # Avoid repeatedly querying the database for attributes
    # during pair comparison.
    attribute_cache = {}

    for material in materials:
        attribute_cache[material.id] = (
            _material_attr_dict(
                db,
                material.id,
            )
        )

    # ---------------------------------------------------------
    # COLLECT CANDIDATES
    # ---------------------------------------------------------

    candidates = []

    for i, j in itertools.combinations(
        range(len(materials)),
        2,
    ):

        material_a = materials[i]
        material_b = materials[j]

        # -----------------------------------------------------
        # SOURCE GATE
        # -----------------------------------------------------

        # Never compare two records from the same ERP source.
        if (
            material_a.source_system
            == material_b.source_system
        ):
            continue

        # -----------------------------------------------------
        # EXISTING PAIR GATE
        # -----------------------------------------------------

        pair = frozenset(
            (
                material_a.id,
                material_b.id,
            )
        )

        if pair in existing_pairs:
            continue

        # -----------------------------------------------------
        # CATEGORY GATE
        # -----------------------------------------------------

        if not categories_compatible(
            material_a.category,
            material_b.category,
        ):
            continue

        # -----------------------------------------------------
        # SEMANTIC SCORE
        # -----------------------------------------------------

        semantic = float(
            sim_matrix[i][j]
        )

        # -----------------------------------------------------
        # ATTRIBUTE SCORE
        # -----------------------------------------------------

        attributes_a = attribute_cache[
            material_a.id
        ]

        attributes_b = attribute_cache[
            material_b.id
        ]

        attribute_sc = attribute_score(
            attributes_a,
            attributes_b,
        )

        # -----------------------------------------------------
        # HARD CONFLICT DETECTION
        # -----------------------------------------------------

        conflict = detect_conflict(
            attributes_a,
            attributes_b,
        )

        # Keep deterministic conflict pairs visible as flagged review
        # candidates instead of silently dropping them. The hard
        # conflict must be surfaced as conflict_reason and must never
        # be resolved via auto-accept.
        rule_sc = rule_score(conflict)

        # -----------------------------------------------------
        # HYBRID CONFIDENCE
        # -----------------------------------------------------

        confidence = hybrid_confidence(
            semantic,
            attribute_sc,
            rule_sc,
        )

        # Only plausible candidates enter the queue.
        # Conflicts remain flagged pending records if the score
        # crosses the floor, but they never become a match.
        if confidence < settings.MATCH_FLOOR:
            continue

        candidates.append(
            {
                "material_a": material_a,
                "material_b": material_b,
                "semantic": semantic,
                "attribute_score": attribute_sc,
                "rule_score": rule_sc,
                "confidence": confidence,
                "conflict_reason": conflict,
            }
        )

    # ---------------------------------------------------------
    # RANK CANDIDATES
    # ---------------------------------------------------------

    # Highest-confidence candidates first.
    candidates.sort(
        key=lambda candidate: (
            candidate["confidence"],
            candidate["attribute_score"],
            candidate["semantic"],
        ),
        reverse=True,
    )

    # ---------------------------------------------------------
    # TOP 10 ONLY
    # ---------------------------------------------------------

    selected_candidates = candidates[
        :MAX_REVIEW_CANDIDATES
    ]

    # Preserve a hard-conflict signal in the visible review queue
    # when the best 10 by confidence would otherwise hide every
    # conflict-bearing candidate. This keeps the request from
    # silently dropping conflict evidence while still enforcing the
    # maximum candidate count precisely.
    conflict_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("conflict_reason")
    ]
    if conflict_candidates and not any(
        candidate.get("conflict_reason")
        for candidate in selected_candidates
    ):
        conflict_candidates.sort(
            key=lambda candidate: (
                candidate["confidence"],
                candidate["attribute_score"],
                candidate["semantic"],
            ),
            reverse=True,
        )
        selected_candidates = selected_candidates[:-1]
        selected_candidates.append(conflict_candidates[0])

    # ---------------------------------------------------------
    # INSERT PENDING MATCHES
    # ---------------------------------------------------------

    for candidate in selected_candidates:

        material_a = candidate[
            "material_a"
        ]

        material_b = candidate[
            "material_b"
        ]

        db.add(
            models.MaterialMatch(
                material_a=material_a.id,
                material_b=material_b.id,
                semantic_score=round(
                    candidate["semantic"],
                    4,
                ),
                attribute_score=round(
                    candidate["attribute_score"],
                    4,
                ),
                rule_score=round(
                    candidate["rule_score"],
                    4,
                ),
                final_confidence=(
                    candidate["confidence"]
                ),
                conflict_reason=candidate.get("conflict_reason"),
                status="pending",
            )
        )

    db.commit()

    return len(selected_candidates)