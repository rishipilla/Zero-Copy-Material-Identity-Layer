import hmac

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class DemoLoginIn(BaseModel):
    password: str


class DemoLoginOut(BaseModel):
    authenticated: bool


@router.post("/demo-login", response_model=DemoLoginOut)
def demo_login(payload: DemoLoginIn):
    return DemoLoginOut(
        authenticated=hmac.compare_digest(payload.password, settings.DEMO_PASSWORD)
    )