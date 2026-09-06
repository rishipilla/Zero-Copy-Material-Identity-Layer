# ERP Integration Guide

Zero-Copy Material Identity uses a read-only connector boundary. SAP, Oracle, and other ERP systems remain the source of truth. The identity layer reads records into its own side-car store, preserves the original description, normalizes a separate field, and never writes back to an ERP.

## 1. Configure SAP

Set `SAP_BASE_URL`, `SAP_MATERIAL_ENDPOINT`, `SAP_CLIENT_ID`, `SAP_CLIENT_SECRET`, and `SAP_TOKEN_URL` in the FastAPI environment. Use a client-credentials OAuth application with read-only material permissions. Set `SAP_FIELD_MAPPING` when the OData property names differ from the defaults.

## 2. Configure Oracle

Set `ORACLE_BASE_URL`, `ORACLE_MATERIAL_ENDPOINT`, `ORACLE_CLIENT_ID`, `ORACLE_CLIENT_SECRET`, and `ORACLE_TOKEN_URL`. Use a read-only Oracle ERP REST integration and set `ORACLE_FIELD_MAPPING` for tenant-specific response fields.

## 3. Required credentials

The backend needs an endpoint and OAuth client credentials to test or synchronize a provider. Secrets are read from environment variables only. They are not sent to React, stored in PostgreSQL, returned by the API, or logged.

## 4. Field mapping

The connector maps provider response fields into `legacy_code`, `description`, `manufacturer`, `category`, `unit`, and optional `source_updated_at`. Example: `MaterialNumber -> legacy_code`, `MaterialDescription -> description`.

## 5. Synchronization

Use `POST /api/integrations/{provider}/sync` for a manual read-only sync. The connector sends `updated_since` when a previous synchronization exists, paginates `items` responses, deduplicates by `source_system + legacy_code`, and records created, changed, skipped, and failed counts.

## 6. Webhooks

`POST /api/integrations/{provider}/webhook` is intentionally rejected until a provider-specific signature secret and replay protection are configured. Do not expose unsigned webhook processing in production.

## 7. Security

Use HTTPS, least-privilege read-only OAuth scopes, secret storage in the deployment environment, bounded pagination, and provider rate-limit guidance. Never log authorization headers, tokens, passwords, or client secrets.

## 8. Troubleshooting

- `not_configured`: endpoint or material path is missing.
- `missing_credentials`: OAuth client ID, secret, or token URL is missing.
- `error`: the provider endpoint could not be reached or returned an HTTP error.
- `failed`: the sync failed safely; existing identity data is not changed.

## 9. Zero-Copy architecture

`ERP -> READ -> FastAPI connector -> PostgreSQL source layer -> normalization + matching -> human validation -> canonical identity + Neo4j projection`.

There is no ERP write-back path. A changed source description is recorded as a source change with previous and current values, then pending candidates for that material are regenerated for human review.
