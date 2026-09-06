import os

from neo4j import GraphDatabase


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
) -> None:
    """
    Create or update a Material node in Neo4j.
    """
    query = """
    MERGE (m:Material {material_id: $material_id})
    SET
        m.description = $description,
        m.category = $category
    """

    with driver.session() as session:
        session.run(
            query,
            material_id=material_id,
            description=description,
            category=category,
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
) -> None:
    """
    Create a HAS_MEMBER relationship between an Identity
    and a Material.
    """
    query = """
    MATCH (i:Identity {identity_id: $identity_id})
    MATCH (m:Material {material_id: $material_id})
    MERGE (i)-[:HAS_MEMBER]->(m)
    """

    with driver.session() as session:
        session.run(
            query,
            identity_id=identity_id,
            material_id=material_id,
        )