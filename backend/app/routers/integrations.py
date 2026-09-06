import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import get_db
from app.services import neo4j_sync
from app.services.erp_connectors import connector_for
from app.services.erp_sync import sync_provider

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _connection_status(provider: str, db: Session) -> schemas.ERPConnectionOut:
    connector = connector_for(provider)
    saved = db.query(models.ERPConnection).filter_by(provider=connector.config.provider).first()
    status = connector.get_sync_status()
    return schemas.ERPConnectionOut(provider=connector.config.provider, name=f"{connector.config.provider} ERP", base_url=connector.config.base_url or None, material_endpoint=connector.config.material_endpoint or None, auth_type=connector.config.auth_type, configured=connector.configured, credentials_configured=connector.credentials_configured, status=status["status"], message=status["message"], last_sync_at=saved.last_sync_at if saved else None, last_sync_status=saved.last_sync_status if saved else None)


@router.get("", response_model=list[schemas.ERPConnectionOut])
def list_integrations(db: Session = Depends(get_db)):
    return [_connection_status("sap", db), _connection_status("oracle", db)]


@router.get("/health", response_model=schemas.IntegrationHealthOut)
def integration_health(db: Session = Depends(get_db)):
    providers = {}
    for provider in ("sap", "oracle"):
        providers[provider.upper()] = _connection_status(provider, db).status
    return schemas.IntegrationHealthOut(postgresql="connected", neo4j="connected" if neo4j_sync.is_enabled() else "not_configured", providers=providers)


@router.get("/{provider}/status", response_model=schemas.ERPConnectionOut)
def integration_status(provider: str, db: Session = Depends(get_db)):
    try:
        return _connection_status(provider, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{provider}/test", response_model=schemas.ERPConnectionOut)
def test_integration(provider: str, db: Session = Depends(get_db)):
    return integration_status(provider, db)


@router.post("/{provider}/sync", response_model=schemas.ERPSyncOut)
def sync_integration(provider: str, db: Session = Depends(get_db)):
    try:
        return sync_provider(db, provider)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{provider}/webhook")
def integration_webhook(provider: str, payload: dict, db: Session = Depends(get_db)):
    # Webhooks remain opt-in: without a provider-specific signature secret, reject safely.
    raise HTTPException(status_code=501, detail="Webhook validation is not configured for this provider.")


@router.get("/activity", response_model=list[schemas.IntegrationAuditOut])
def integration_activity(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.IntegrationAuditEvent).order_by(models.IntegrationAuditEvent.created_at.desc()).limit(min(limit, 100)).all()
