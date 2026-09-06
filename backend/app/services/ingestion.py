import csv
import io
import json

from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.material_attribute import MaterialAttribute
from app.services.normalization import normalize_text, extract_attributes


def import_materials(file_content: bytes, db: Session) -> int:
    text = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    imported_count = 0

    for row in reader:
        source_system = row.get("source_system")
        legacy_code = row.get("legacy_code")

        # Prevent duplicate imports of the same source record.
        existing = (
            db.query(Material)
            .filter(
                Material.source_system == source_system,
                Material.legacy_code == legacy_code,
            )
            .first()
        )

        if existing:
            continue

        original_description = row.get("description")
        specifications = row.get("specifications")

        if specifications:
            try:
                specifications = json.loads(specifications)
            except json.JSONDecodeError:
                specifications = {"raw": specifications}
        else:
            specifications = None

        material = Material(
            source_system=source_system,
            legacy_code=legacy_code,
            description=original_description,
            manufacturer=row.get("manufacturer"),
            category=row.get("category"),
            unit=row.get("unit"),
            specifications=specifications,
        )

        db.add(material)
        db.flush()

        normalized_description = normalize_text(
            original_description or ""
        )

        attributes = extract_attributes(
            original_description or ""
        )

        attributes["normalized_description"] = normalized_description

        for attribute_name, attribute_value in attributes.items():
            if attribute_value is None:
                continue

            attribute = MaterialAttribute(
                material_id=material.id,
                attribute_name=attribute_name,
                attribute_value=str(attribute_value),
                normalized_value=str(attribute_value),
                unit=None,
            )

            db.add(attribute)

        imported_count += 1

    db.commit()

    return imported_count