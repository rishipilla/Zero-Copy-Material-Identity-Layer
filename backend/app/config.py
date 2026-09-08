"""
Central configuration. Everything here is overridable via environment
variables so the same codebase runs three ways:

1. Zero-setup local dev  -> SQLite file, no Neo4j (default)
2. docker-compose stack  -> Postgres + Neo4j (see docker-compose.yml)
3. Real deployment       -> Postgres + Neo4j + eventually real ERP creds
"""
import os
import json


class Settings:
    # --- Database (source-of-truth for materials & identities) ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./zerocopy.db")

    # --- Neo4j (identity graph mirror; optional, app works without it) ---
    NEO4J_URI: str | None = os.getenv("NEO4J_URI")  # e.g. bolt://neo4j:7687
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # --- Matching engine weights (production-tunable defaults) ---
    WEIGHT_SEMANTIC: float = float(os.getenv("WEIGHT_SEMANTIC", "0.5"))
    WEIGHT_ATTRIBUTE: float = float(os.getenv("WEIGHT_ATTRIBUTE", "0.3"))
    WEIGHT_RULE: float = float(os.getenv("WEIGHT_RULE", "0.2"))

    # Below this, don't even surface a candidate pair
    MATCH_FLOOR: float = float(os.getenv("MATCH_FLOOR", "0.55"))
    # A conflicting pair is only worth a human's attention if the text was
    # otherwise plausibly describing the same family of item — this keeps
    # two unrelated items that happen to both have a "diameter" attribute
    # from cluttering the review queue.
    CONFLICT_SEMANTIC_FLOOR: float = float(os.getenv("CONFLICT_SEMANTIC_FLOOR", "0.5"))

    # --- Embedding backend ---
    # "tfidf"  -> scikit-learn TF-IDF + cosine similarity. Ships with zero
    #             external downloads, works fully offline. Default.
    # "sentence-transformers" -> swap in when you have model-download access;
    #             see app/services/matching.py::_embed_sentence_transformers
    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "tfidf")

    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    ACCESS_PASSWORD: str = os.getenv("ACCESS_PASSWORD", os.getenv("DEMO_PASSWORD", "demo123"))

    # --- Read-only ERP connector configuration. Secrets stay in environment variables. ---
    ERP_PROVIDER: str = os.getenv("ERP_PROVIDER", "")
    ERP_SYNC_INTERVAL_SECONDS: int = int(os.getenv("ERP_SYNC_INTERVAL_SECONDS", "300"))
    SAP_BASE_URL: str = os.getenv("SAP_BASE_URL", "")
    SAP_MATERIAL_ENDPOINT: str = os.getenv("SAP_MATERIAL_ENDPOINT", "")
    SAP_CLIENT_ID: str = os.getenv("SAP_CLIENT_ID", "")
    SAP_CLIENT_SECRET: str = os.getenv("SAP_CLIENT_SECRET", "")
    SAP_TOKEN_URL: str = os.getenv("SAP_TOKEN_URL", "")
    SAP_FIELD_MAPPING: dict = json.loads(os.getenv("SAP_FIELD_MAPPING", "{}"))
    ORACLE_BASE_URL: str = os.getenv("ORACLE_BASE_URL", "")
    ORACLE_MATERIAL_ENDPOINT: str = os.getenv("ORACLE_MATERIAL_ENDPOINT", "")
    ORACLE_CLIENT_ID: str = os.getenv("ORACLE_CLIENT_ID", "")
    ORACLE_CLIENT_SECRET: str = os.getenv("ORACLE_CLIENT_SECRET", "")
    ORACLE_TOKEN_URL: str = os.getenv("ORACLE_TOKEN_URL", "")
    ORACLE_FIELD_MAPPING: dict = json.loads(os.getenv("ORACLE_FIELD_MAPPING", "{}"))


settings = Settings()
