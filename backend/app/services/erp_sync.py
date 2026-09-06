import datetime
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app import models
from app.services.erp_connectors import connector_for
from app.services.extract import extract_attributes, attributes_to_rows
from app.services.importer import generate_candidates
from app.services.normalize import normalize_description

logger = logging.getLogger(__name__)


def _parse_timestamp(value: Any) -> datetime.datetime | None:
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value.replace(tzinfo=None)
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _audit(db: Session, provider: str, event_type: str, status: str, message: str, count: int = 0):
    db.add(models.IntegrationAuditEvent(provider=provider, event_type=event_type, status=status, message=message, records_processed=count))


def sync_provider(db: Session, provider: str) -> dict:
    connector = connector_for(provider)
    config_status = connector.get_sync_status()
    connection = db.query(models.ERPConnection).filter_by(provider=connector.config.provider).first()
    if not connection:
        connection = models.ERPConnection(name=f"{connector.config.provider} ERP", provider=connector.config.provider, base_url=connector.config.base_url or None, auth_type=connector.config.auth_type, material_endpoint=connector.config.material_endpoint or None, enabled="true" if connector.configured else "false")
        db.add(connection)
        db.flush()

    started = datetime.datetime.utcnow()
    run = models.ERPSyncRun(connection_id=connection.id, status="running")
    db.add(run)
    db.commit()
    if config_status["status"] != "connected":
        run.status = "not_configured" if config_status["status"] in {"not_configured", "missing_credentials"} else "failed"
        run.completed_at = datetime.datetime.utcnow()
        run.error_message = config_status["message"]
        connection.last_sync_status = run.status
        connection.last_sync_message = run.error_message
        connection.last_sync_at = started
        db.commit()
        return {"provider": connector.config.provider, "status": run.status, "message": run.error_message, "records_received": 0, "records_created": 0, "records_updated": 0, "records_skipped": 0, "records_failed": 0}

    last_sync = connection.last_sync_at
    try:
        records = connector.fetch_changes(last_sync)
        created = updated = skipped = failed = 0
        changed_ids: list[str] = []
        for record in records:
            legacy_code = str(record.get("legacy_code") or "").strip()
            description = str(record.get("description") or "").strip()
            if not legacy_code or not description:
                skipped += 1
                continue
            source = connector.config.provider
            material = db.query(models.Material).filter_by(source_system=source, legacy_code=legacy_code).first()
            source_reference = f"{source}:{legacy_code}"
            source_updated_at = _parse_timestamp(record.get("source_updated_at"))
            if material is None:
                material = models.Material(source_system=source, legacy_code=legacy_code, description=description, normalized_description=normalize_description(description), manufacturer=record.get("manufacturer"), category=record.get("category"), unit=record.get("unit"), specifications=str(record.get("raw_source", {})))
                db.add(material)
                db.flush()
                for attr_row in attributes_to_rows(extract_attributes(description)):
                    db.add(models.MaterialAttribute(material_id=material.id, **attr_row))
                db.add(models.MaterialSourceState(material_id=material.id, source_reference=source_reference, source_updated_at=source_updated_at))
                created += 1
                changed_ids.append(material.id)
                _audit(db, source, "material_imported", "success", f"Imported {source_reference}")
                continue

            state = db.query(models.MaterialSourceState).filter_by(material_id=material.id).first()
            if state and state.source_updated_at and source_updated_at and source_updated_at <= state.source_updated_at:
                skipped += 1
                continue
            if material.description == description and not source_updated_at:
                skipped += 1
                continue
            previous = material.description
            material.description = description
            material.normalized_description = normalize_description(description)
            material.manufacturer = record.get("manufacturer") or material.manufacturer
            material.category = record.get("category") or material.category
            material.unit = record.get("unit") or material.unit
            if state is None:
                state = models.MaterialSourceState(material_id=material.id, source_reference=source_reference)
                db.add(state)
            state.previous_description = previous
            state.source_updated_at = source_updated_at
            state.last_change_at = datetime.datetime.utcnow()
            state.last_change_detected = "true"
            db.query(models.MaterialMatch).filter((models.MaterialMatch.material_a == material.id) | (models.MaterialMatch.material_b == material.id), models.MaterialMatch.status == "pending").delete(synchronize_session=False)
            changed_ids.append(material.id)
            updated += 1
            _audit(db, source, "source_record_changed", "warning", f"Source record changed: {source_reference}")
        db.commit()
        candidates = generate_candidates(db) if changed_ids or created else 0
        run.status = "completed"
        run.completed_at = datetime.datetime.utcnow()
        run.records_received = len(records)
        run.records_created = created
        run.records_updated = updated
        run.records_skipped = skipped
        run.records_failed = failed
        connection.last_sync_at = datetime.datetime.utcnow()
        connection.last_sync_status = "completed"
        connection.last_sync_message = f"{candidates} match candidates generated."
        db.commit()
        _audit(db, connector.config.provider, "erp_synchronization_completed", "success", f"{len(records)} records processed", len(records))
        db.commit()
        return {"provider": connector.config.provider, "status": "completed", "message": connection.last_sync_message, "records_received": len(records), "records_created": created, "records_updated": updated, "records_skipped": skipped, "records_failed": failed, "matches_generated": candidates}
    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.completed_at = datetime.datetime.utcnow()
        run.error_message = "ERP synchronization failed. Existing identity data was not changed."
        connection.last_sync_status = "failed"
        connection.last_sync_message = run.error_message
        db.add(run)
        db.commit()
        logger.warning("ERP sync failed provider=%s status=failed", connector.config.provider)
        return {"provider": connector.config.provider, "status": "failed", "message": run.error_message, "records_received": 0, "records_created": 0, "records_updated": 0, "records_skipped": 0, "records_failed": 1}
