from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import materials, matches, graph, integrations, identities, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Zero-Copy Material Identity Layer",
    description="Side-car identity resolution layer for multi-ERP material records. "
                 "Source ERP data is never migrated or mutated.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(materials.router)
app.include_router(matches.router)
app.include_router(graph.router)
app.include_router(graph.analytics_router)
app.include_router(integrations.router)
app.include_router(identities.router)
app.include_router(auth.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}