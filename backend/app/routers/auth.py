import hmac

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    password: str


class LoginOut(BaseModel):
    authenticated: bool


@router.post("/login", response_model=LoginOut)
@router.post("/demo-login", response_model=LoginOut)
def login(payload: LoginIn):
    return LoginOut(
        authenticated=hmac.compare_digest(payload.password, settings.ACCESS_PASSWORD)
    )