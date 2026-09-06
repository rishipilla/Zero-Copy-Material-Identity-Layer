import os

from neo4j import GraphDatabase
from sqlalchemy.orm import Session

from app import models


NEO4J_URI = os.getenv(
    "NEO4J_URI",
    "bolt://localhost:7687",
)

NEO4J_USERNAME = os.getenv(
    "NEO4J_USERNAME",
    "neo4j",
)

NEO4J_PASSWORD = os.getenv(
    "NEO4J_PASSWORD",
    "materials123",
)


driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(
        NEO4J_USERNAME,
        NEO4J_PASSWORD,
    ),
)


def verify_graph_connection() -> None:
    """
    Verify that the application can connect to Neo4j.
    """
    driver.verify_connectivity()


def close_graph_connection() -> None:
    """
    Close the Neo4j driver.
    """
    driver.close()


def clear_identity_graph() -> None:
    """
    Remove all Identity nodes and their relationships.

    Material nodes are intentionally preserved.
    """
    query = """
    MATCH (i:Identity)
    DETACH DELETE i
    """

    with driver.session() as session:
        session.run(query)


def create_material_node(
    material_id: int,
    description: str,
    category: str | None = None,
    source_system: str | None = None,
    legacy_code: str | None = None,
) -> None:
    """
    Create or update a Material node in Neo4j.
    """
    query = """
    MERGE (m:Material {material_id: $material_id})
    SET
        m.description = $description,
        m.category = $category,
        m.source_system = $source_system,
        m.legacy_code = $legacy_code
    """

    with driver.session() as session:
        session.run(
            query,
            material_id=material_id,
            description=description,
            category=category,
            source_system=source_system,
            legacy_code=legacy_code,
        )


def create_identity_node(
    identity_id: int,
    canonical_name: str,
    category: str | None = None,
    status: str = "active",
) -> None:
    """
    Create or update an Identity node in Neo4j.
    """
    query = """
    MERGE (i:Identity {identity_id: $identity_id})
    SET
        i.canonical_name = $canonical_name,
        i.category = $category,
        i.status = $status
    """

    with driver.session() as session:
        session.run(
            query,
            identity_id=identity_id,
            canonical_name=canonical_name,
            category=category,
            status=status,
        )


def create_identity_membership(
    identity_id: int,
    material_id: int,
    confidence: float | None = None,
) -> None:
    """
    Create a HAS_MEMBER relationship between an Identity
    and a Material.
    """
    query = """
    MATCH (i:Identity {identity_id: $identity_id})
    MATCH (m:Material {material_id: $material_id})
    MERGE (i)-[r:HAS_MEMBER]->(m)
    SET r.confidence = $confidence
    """

    with driver.session() as session:
        session.run(
            query,
            identity_id=identity_id,
            material_id=material_id,
            confidence=confidence,
        )


def build_graph(db: Session) -> dict:
    """
    Build the application graph from PostgreSQL data
    and synchronize it into Neo4j.

    PostgreSQL remains the source of truth.
    Neo4j is only the graph projection.
    """

    # Verify Neo4j before starting.
    verify_graph_connection()

    # Remove old Identity nodes and their relationships.
    clear_identity_graph()

    # Keep Material nodes that may already exist, but update them
    # from the current PostgreSQL source records.
    materials = (
        db.query(models.Material)
        .order_by(models.Material.id)
        .all()
    )

    for material in materials:
        create_material_node(
            material_id=material.id,
            description=material.description or "",
            category=material.category,
            source_system=material.source_system,
            legacy_code=material.legacy_code,
        )

    # Load identities from PostgreSQL.
    identities = (
        db.query(models.MaterialIdentity)
        .order_by(models.MaterialIdentity.id)
        .all()
    )

    nodes = []
    edges = []

    # Create Identity nodes in Neo4j.
    for identity in identities:
        create_identity_node(
            identity_id=identity.id,
            canonical_name=identity.canonical_name,
            category=identity.category,
            status=getattr(identity, "status", "active"),
        )

        nodes.append(
            {
                "id": identity.id,
                "label": identity.canonical_name,
                "type": "identity",
                "source_system": None,
            }
        )

    # Accepted matches define Identity -> Material membership.
    accepted_matches = (
        db.query(models.MaterialMatch)
        .filter(
            models.MaterialMatch.status == "accepted",
            models.MaterialMatch.identity_id.isnot(None),
        )
        .all()
    )

    seen_material_ids = set()
    membership_count = 0

    for match in accepted_matches:
        for material_id in (
            match.material_a,
            match.material_b,
        ):
            if material_id in seen_material_ids:
                continue

            material = (
                db.query(models.Material)
                .filter(
                    models.Material.id == material_id
                )
                .first()
            )

            if not material:
                continue

            seen_material_ids.add(material_id)

            nodes.append(
                {
                    "id": material.id,
                    "label": material.legacy_code,
                    "type": "material",
                    "source_system": material.source_system,
                }
            )

            create_identity_membership(
                identity_id=match.identity_id,
                material_id=material.id,
                confidence=match.final_confidence,
            )

            edges.append(
                {
                    "source": match.identity_id,
                    "target": material.id,
                    "confidence": match.final_confidence,
                }
            )

            membership_count += 1

    return {
        "nodes": nodes,
        "edges": edges,
        "material_node_count": len(materials),
        "identity_node_count": len(identities),
        "membership_count": membership_count,
    }