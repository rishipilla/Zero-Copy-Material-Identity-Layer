"""
Optional Neo4j mirror.

Postgres/SQLite is the source of truth (see services/graph.py). This module
pushes the same Identity -> legacy-code fan-out into Neo4j *when configured*,
so teams that want native Cypher graph queries get it for free. If
NEO4J_URI isn't set, or the driver can't connect, every function here is a
silent no-op — the rest of the app never depends on Neo4j being up.
"""
from app.config import settings

_driver = None
_enabled = bool(settings.NEO4J_URI)


def _get_driver():
    global _driver
    if not _enabled:
        return None
    if _driver is None:
        from neo4j import GraphDatabase  # imported lazily so it's an optional dep at runtime
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    return _driver


def sync_identity(identity_id: str, canonical_name: str, category: str | None) -> None:
    driver = _get_driver()
    if driver is None:
        return
    with driver.session() as session:
        session.run(
            """
            MERGE (i:Identity {id: $id})
            SET i.canonical_name = $name, i.category = $category
            """,
            id=identity_id, name=canonical_name, category=category,
        )


def sync_material_link(identity_id: str, material_id: str, source_system: str,
                        legacy_code: str, confidence: float) -> None:
    driver = _get_driver()
    if driver is None:
        return
    with driver.session() as session:
        session.run(
            """
            MATCH (i:Identity {id: $identity_id})
            MERGE (m:LegacyCode {id: $material_id})
            SET m.source_system = $source_system, m.legacy_code = $legacy_code
            MERGE (i)-[r:MAPS_TO]->(m)
            SET r.confidence = $confidence
            """,
            identity_id=identity_id, material_id=material_id,
            source_system=source_system, legacy_code=legacy_code, confidence=confidence,
        )


def is_enabled() -> bool:
    return _enabled
