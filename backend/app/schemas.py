import datetime
from pydantic import BaseModel


class AttributeOut(BaseModel):
    attribute_name: str
    attribute_value: str | None = None
    normalized_value: str | None = None
    unit: str | None = None

    class Config:
        from_attributes = True


class MaterialOut(BaseModel):
    id: str
    source_system: str
    legacy_code: str
    description: str
    normalized_description: str | None = None
    manufacturer: str | None = None
    category: str | None = None
    unit: str | None = None
    attributes: list[AttributeOut] = []

    class Config:
        from_attributes = True


class MaterialDetailOut(MaterialOut):
    source_reference: str | None = None
    source_updated_at: datetime.datetime | None = None
    ingested_at: datetime.datetime | None = None
    previous_description: str | None = None
    source_changed: bool = False


class IdentityDetailOut(BaseModel):
    id: str
    canonical_name: str
    category: str | None = None
    members: list[MaterialOut] = []


class MatchOut(BaseModel):
    id: str
    material_a: str
    material_b: str
    material_a_detail: MaterialOut | None = None
    material_b_detail: MaterialOut | None = None
    semantic_score: float
    attribute_score: float
    rule_score: float
    final_confidence: float
    conflict_reason: str | None = None
    status: str
    identity_id: str | None = None

    class Config:
        from_attributes = True


class ResolveMatchIn(BaseModel):
    action: str
    canonical_name: str | None = None


class ImportSummary(BaseModel):
    source_system: str
    imported: int
    skipped: int
    matches_generated: int


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    source_system: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    confidence: float | None = None


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    material_node_count: int
    identity_node_count: int
    membership_count: int


class AnalyticsOut(BaseModel):
    total_materials: int
    total_identities: int
    pending_candidates: int
    accepted_matches: int
    rejected_matches: int
    conflicts_flagged: int
    source_systems: dict[str, int]


class ERPConnectionOut(BaseModel):
    provider: str
    name: str
    base_url: str | None = None
    material_endpoint: str | None = None
    auth_type: str
    configured: bool
    credentials_configured: bool
    status: str
    message: str
    last_sync_at: datetime.datetime | None = None
    last_sync_status: str | None = None


class ERPSyncOut(BaseModel):
    provider: str
    status: str
    message: str
    records_received: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_failed: int = 0
    matches_generated: int = 0


class IntegrationAuditOut(BaseModel):
    id: str
    provider: str | None = None
    event_type: str
    status: str
    message: str
    records_processed: int = 0
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class IntegrationHealthOut(BaseModel):
    postgresql: str
    neo4j: str
    providers: dict[str, str]