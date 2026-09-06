from itertools import combinations

from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.material_attribute import MaterialAttribute
from app.models.material_match import MaterialMatch
from app.services.matching import (
    semantic_similarity,
    attribute_similarity,
    has_attribute_conflict,
    match_decision,
)


def get_material_attributes(
    material_id: int,
    db: Session,
) -> dict:
    """
    Load all extracted attributes for one material.
    """

    rows = (
        db.query(MaterialAttribute)
        .filter(MaterialAttribute.material_id == material_id)
        .all()
    )

    attributes = {}

    for row in rows:
        if row.attribute_name == "normalized_description":
            continue

        value = row.attribute_value

        # Convert numeric attributes back to numbers.
        if row.attribute_name in ["diameter", "length"]:
            try:
                value = float(value)
            except (TypeError, ValueError):
                pass

        attributes[row.attribute_name] = value

    return attributes


def get_normalized_description(
    material_id: int,
    db: Session,
) -> str:
    """
    Get the normalized description stored for a material.
    """

    row = (
        db.query(MaterialAttribute)
        .filter(
            MaterialAttribute.material_id == material_id,
            MaterialAttribute.attribute_name == "normalized_description",
        )
        .first()
    )

    if row:
        return row.attribute_value or ""

    return ""


def calculate_rule_score(
    material_a: Material,
    material_b: Material,
) -> float:
    """
    Calculate basic rule compatibility.

    Prototype rules:
    - Same category -> compatible
    - Different category -> incompatible
    """

    if (
        material_a.category
        and material_b.category
        and material_a.category.lower() != material_b.category.lower()
    ):
        return 0.0

    return 1.0


def compare_materials(
    material_a: Material,
    material_b: Material,
    db: Session,
) -> dict:
    """
    Compare two materials using semantic, attribute,
    and rule-based matching.
    """

    normalized_a = get_normalized_description(
        material_a.id,
        db,
    )

    normalized_b = get_normalized_description(
        material_b.id,
        db,
    )

    attributes_a = get_material_attributes(
        material_a.id,
        db,
    )

    attributes_b = get_material_attributes(
        material_b.id,
        db,
    )

    semantic_score = semantic_similarity(
        normalized_a,
        normalized_b,
    )

    attribute_score = attribute_similarity(
        attributes_a,
        attributes_b,
    )

    rule_score = calculate_rule_score(
        material_a,
        material_b,
    )

    conflict = has_attribute_conflict(
        attributes_a,
        attributes_b,
    )

    decision = match_decision(
        semantic_score=semantic_score,
        attribute_score=attribute_score,
        rule_score=rule_score,
        has_conflict=conflict,
    )

    return {
        "material_a": material_a.id,
        "material_b": material_b.id,
        "semantic_score": semantic_score,
        "attribute_score": attribute_score,
        "rule_score": rule_score,
        "final_confidence": decision["confidence"],
        "status": decision["decision"],
        "reason": decision["reason"],
    }


def run_matching(
    db: Session,
) -> list[dict]:
    """
    Compare all material pairs and save the results
    to material_matches.
    """

    materials = (
        db.query(Material)
        .order_by(Material.id)
        .all()
    )

    results = []

    for material_a, material_b in combinations(materials, 2):

        result = compare_materials(
            material_a,
            material_b,
            db,
        )

        existing = (
            db.query(MaterialMatch)
            .filter(
                MaterialMatch.material_a == material_a.id,
                MaterialMatch.material_b == material_b.id,
            )
            .first()
        )

        if existing:
            existing.semantic_score = result["semantic_score"]
            existing.attribute_score = result["attribute_score"]
            existing.rule_score = result["rule_score"]
            existing.final_confidence = result["final_confidence"]
            existing.status = result["status"]

        else:
            match = MaterialMatch(
                material_a=result["material_a"],
                material_b=result["material_b"],
                semantic_score=result["semantic_score"],
                attribute_score=result["attribute_score"],
                rule_score=result["rule_score"],
                final_confidence=result["final_confidence"],
                status=result["status"],
            )

            db.add(match)

        results.append(result)

    db.commit()

    return results