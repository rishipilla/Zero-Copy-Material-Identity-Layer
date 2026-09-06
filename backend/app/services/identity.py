from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.material_identity import MaterialIdentity
from app.models.material_identity_member import MaterialIdentityMember
from app.models.material_match import MaterialMatch


def create_identity_from_material(
    material: Material,
    db: Session,
) -> MaterialIdentity:
    identity = MaterialIdentity(
        canonical_name=material.description or "Unnamed Material",
        category=material.category,
        status="active",
    )

    db.add(identity)
    db.flush()

    return identity


def build_identities(db: Session) -> list[dict]:
    # Clear previously generated identity memberships and identities.
    # Materials and matches remain untouched.
    db.query(MaterialIdentityMember).delete()
    db.query(MaterialIdentity).delete()
    db.flush()

    materials = (
        db.query(Material)
        .order_by(Material.id)
        .all()
    )

    matches = (
        db.query(MaterialMatch)
        .filter(MaterialMatch.status == "MATCH")
        .all()
    )

    # Initially, every material belongs to its own group.
    groups = {
        material.id: {material.id}
        for material in materials
    }

    def find_group(material_id: int) -> set[int]:
        for group in groups.values():
            if material_id in group:
                return group

        return set()

    # Merge groups connected by confirmed MATCH results.
    for match in matches:
        group_a = find_group(match.material_a)
        group_b = find_group(match.material_b)

        if group_a is not group_b:
            merged_group = group_a | group_b

            for material_id in merged_group:
                groups[material_id] = merged_group

    # Remove duplicate references to the same group.
    unique_groups = []
    seen = set()

    for group in groups.values():
        group_key = tuple(sorted(group))

        if group_key not in seen:
            seen.add(group_key)
            unique_groups.append(group)

    results = []

    for group in unique_groups:
        group_materials = [
            material
            for material in materials
            if material.id in group
        ]

        if not group_materials:
            continue

        # First material becomes the representative/canonical material.
        primary_material = group_materials[0]

        identity = create_identity_from_material(
            primary_material,
            db,
        )

        # Persist every material -> identity relationship.
        for material_id in sorted(group):
            membership = MaterialIdentityMember(
                identity_id=identity.identity_id,
                material_id=material_id,
            )

            db.add(membership)

        results.append(
            {
                "identity_id": identity.identity_id,
                "canonical_name": identity.canonical_name,
                "category": identity.category,
                "material_ids": sorted(group),
            }
        )

    db.commit()

    return results