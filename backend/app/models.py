import datetime
import uuid

from sqlalchemy import (
    Column, String, Float, ForeignKey, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


def _uid() -> str:
    return uuid.uuid4().hex[:12]


class Material(Base):
    """
    A single material record exactly as it exists in one source ERP.
    NEVER mutated by the matching engine — this table is the read-only
    mirror that makes the whole system Zero-Copy.
    """
    __tablename__ = "materials"

    id = Column(String, primary_key=True, default=_uid)
    source_system = Column(String, nullable=False)      # e.g. "SAP-A", "SAP-B"
    legacy_code = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    normalized_description = Column(Text, nullable=True)
    manufacturer = Column(String, nullable=True)
    category = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    specifications = Column(Text, nullable=True)         # raw free text spec, if any
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    attributes = relationship("MaterialAttribute", back_populates="material", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("source_system", "legacy_code", name="uq_source_code"),)


class MaterialAttribute(Base):
    __tablename__ = "material_attributes"

    id = Column(String, primary_key=True, default=_uid)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)
    attribute_name = Column(String, nullable=False)       # e.g. "diameter"
    attribute_value = Column(String, nullable=True)        # raw, e.g. "M10"
    normalized_value = Column(String, nullable=True)       # e.g. "10mm"
    unit = Column(String, nullable=True)

    material = relationship("Material", back_populates="attributes")


class MaterialIdentity(Base):
    """
    A canonical, cross-ERP identity. Legacy records are linked to this via
    MaterialMatch rows with status='accepted' — never merged in place.
    """
    __tablename__ = "material_identities"

    id = Column(String, primary_key=True, default=_uid)
    canonical_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    status = Column(String, default="active")             # active | archived
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MaterialMatch(Base):
    """
    A proposed (or resolved) link between two materials, or between a
    material and an identity once accepted.
    """
    __tablename__ = "material_matches"

    id = Column(String, primary_key=True, default=_uid)
    material_a = Column(String, ForeignKey("materials.id"), nullable=False)
    material_b = Column(String, ForeignKey("materials.id"), nullable=False)
    semantic_score = Column(Float, default=0.0)
    attribute_score = Column(Float, default=0.0)
    rule_score = Column(Float, default=0.0)
    final_confidence = Column(Float, default=0.0)
    conflict_reason = Column(String, nullable=True)        # null unless a hard conflict was detected
    status = Column(String, default="pending")             # pending | accepted | rejected
    identity_id = Column(String, ForeignKey("material_identities.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ERPConnection(Base):
    __tablename__ = "erp_connections"

    id = Column(String, primary_key=True, default=_uid)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False, unique=True)
    base_url = Column(String, nullable=True)
    auth_type = Column(String, nullable=False, default="oauth2")
    material_endpoint = Column(String, nullable=True)
    field_mapping = Column(Text, nullable=True)
    enabled = Column(String, nullable=False, default="false")
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String, nullable=True)
    last_sync_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ERPSyncRun(Base):
    __tablename__ = "erp_sync_runs"

    id = Column(String, primary_key=True, default=_uid)
    connection_id = Column(String, ForeignKey("erp_connections.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="running")
    records_received = Column(Float, default=0)
    records_created = Column(Float, default=0)
    records_updated = Column(Float, default=0)
    records_skipped = Column(Float, default=0)
    records_failed = Column(Float, default=0)
    error_message = Column(String, nullable=True)


class MaterialSourceState(Base):
    """Side-car source metadata; the original ERP row remains external and read-only."""
    __tablename__ = "material_source_state"

    id = Column(String, primary_key=True, default=_uid)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False, unique=True)
    source_reference = Column(String, nullable=False, unique=True)
    source_updated_at = Column(DateTime, nullable=True)
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    previous_description = Column(Text, nullable=True)
    last_change_at = Column(DateTime, nullable=True)
    last_change_detected = Column(String, nullable=False, default="false")


class IntegrationAuditEvent(Base):
    __tablename__ = "integration_audit_events"

    id = Column(String, primary_key=True, default=_uid)
    provider = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=False)
    records_processed = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
