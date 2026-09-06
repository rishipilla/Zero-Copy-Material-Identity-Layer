"""Read-only ERP connector abstraction.

Credentials are read only from process environment and are never returned or logged.
"""
import datetime
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass
class ConnectorConfig:
    provider: str
    base_url: str
    material_endpoint: str
    auth_type: str
    client_id: str
    client_secret: str
    token_url: str
    field_mapping: dict[str, str]


DEFAULT_MAPPING = {
    "id": "legacy_code",
    "materialNumber": "legacy_code",
    "materialDescription": "description",
    "description": "description",
    "manufacturerName": "manufacturer",
    "manufacturer": "manufacturer",
    "materialGroup": "category",
    "category": "category",
    "baseUnit": "unit",
    "unit": "unit",
    "lastModified": "source_updated_at",
    "updated_at": "source_updated_at",
}


def config_for(provider: str) -> ConnectorConfig:
    normalized = provider.lower()
    if normalized == "sap":
        return ConnectorConfig("SAP", settings.SAP_BASE_URL, settings.SAP_MATERIAL_ENDPOINT, "oauth2", settings.SAP_CLIENT_ID, settings.SAP_CLIENT_SECRET, settings.SAP_TOKEN_URL, {**DEFAULT_MAPPING, **settings.SAP_FIELD_MAPPING})
    if normalized in {"oracle", "oracle-erp"}:
        return ConnectorConfig("ORACLE", settings.ORACLE_BASE_URL, settings.ORACLE_MATERIAL_ENDPOINT, "oauth2", settings.ORACLE_CLIENT_ID, settings.ORACLE_CLIENT_SECRET, settings.ORACLE_TOKEN_URL, {**DEFAULT_MAPPING, **settings.ORACLE_FIELD_MAPPING})
    raise ValueError(f"Unsupported ERP provider: {provider}")


class ERPConnector:
    def __init__(self, config: ConnectorConfig):
        self.config = config

    @property
    def configured(self) -> bool:
        return bool(self.config.base_url and self.config.material_endpoint)

    @property
    def credentials_configured(self) -> bool:
        return bool(self.config.client_id and self.config.client_secret and self.config.token_url)

    def _token(self) -> str | None:
        if self.config.auth_type != "oauth2":
            return None
        if not self.credentials_configured:
            return None
        response = httpx.post(self.config.token_url, data={"grant_type": "client_credentials"}, auth=(self.config.client_id, self.config.client_secret), timeout=15)
        response.raise_for_status()
        return response.json().get("access_token")

    def _headers(self) -> dict[str, str]:
        token = self._token()
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _url(self) -> str:
        return f"{self.config.base_url.rstrip('/')}/{self.config.material_endpoint.lstrip('/')}"

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_error = None
        for attempt in range(3):
            try:
                response = httpx.request(method, url, timeout=kwargs.pop("timeout", 30), **kwargs)
                if response.status_code == 429 or response.status_code >= 500:
                    delay = response.headers.get("Retry-After")
                    time.sleep(float(delay) if delay and delay.replace('.', '', 1).isdigit() else 2 ** attempt)
                    last_error = httpx.HTTPStatusError("transient ERP response", request=response.request, response=response)
                    continue
                return response
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2 ** attempt)
        raise last_error or RuntimeError("ERP request failed")

    def test_connection(self) -> dict[str, Any]:
        if not self.configured:
            return {"status": "not_configured", "message": f"{self.config.provider} connector is not configured."}
        if not self.credentials_configured:
            return {"status": "missing_credentials", "message": f"{self.config.provider} connector configured but credentials are missing."}
        try:
            response = self._request("GET", self._url(), headers=self._headers(), params={"$top": 1, "limit": 1}, timeout=15)
            response.raise_for_status()
            return {"status": "connected", "message": "Connection successful."}
        except httpx.HTTPStatusError as exc:
            return {"status": "error", "message": f"Connection failed with ERP status {exc.response.status_code}."}
        except (httpx.HTTPError, ValueError):
            return {"status": "error", "message": "Connection failed. The ERP endpoint is unavailable."}

    def fetch_materials(self, updated_since: datetime.datetime | None = None) -> list[dict[str, Any]]:
        if not self.configured:
            raise RuntimeError(f"{self.config.provider} connector is not configured.")
        if not self.credentials_configured:
            raise RuntimeError(f"{self.config.provider} connector configured but credentials are missing.")
        params: dict[str, Any] = {"limit": 100}
        if updated_since:
            params["updated_since"] = updated_since.isoformat()
        records: list[dict[str, Any]] = []
        next_url = self._url()
        for _ in range(100):
            response = self._request("GET", next_url, headers=self._headers(), params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
            items = payload.get("items", payload if isinstance(payload, list) else [])
            records.extend(self.map_record(item) for item in items)
            next_url = payload.get("next") if isinstance(payload, dict) else None
            if not next_url:
                break
            params = {}
        return records

    def fetch_material(self, material_id: str) -> dict[str, Any] | None:
        if not self.configured or not self.credentials_configured:
            return None
        response = self._request("GET", f"{self._url().rstrip('/')}/{material_id}", headers=self._headers(), timeout=20)
        response.raise_for_status()
        return self.map_record(response.json())

    def fetch_changes(self, updated_since: datetime.datetime | None = None) -> list[dict[str, Any]]:
        return self.fetch_materials(updated_since)

    def get_sync_status(self) -> dict[str, Any]:
        result = self.test_connection()
        return {"provider": self.config.provider, **result}

    def map_record(self, record: dict[str, Any]) -> dict[str, Any]:
        mapped: dict[str, Any] = {}
        for source_key, target_key in self.config.field_mapping.items():
            if source_key in record and record[source_key] is not None:
                mapped[target_key] = record[source_key]
        mapped["raw_source"] = record
        return mapped


class SAPConnector(ERPConnector):
    pass


class OracleConnector(ERPConnector):
    pass


class GenericRESTConnector(ERPConnector):
    pass


def connector_for(provider: str) -> ERPConnector:
    config = config_for(provider)
    if provider.lower() == "sap":
        return SAPConnector(config)
    if provider.lower() in {"oracle", "oracle-erp"}:
        return OracleConnector(config)
    return GenericRESTConnector(config)
