from __future__ import annotations

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import approvals, audit, incidents, mitre, settings as settings_api, stream, ioc
from .core.audit import AuditTrail
from .core.chain_of_custody import ChainOfCustody
from .core.events import get_event_bus
from .mocks import mock_host, mock_siem, mock_soar
from .ingestion.siem_consumer import SiemConsumer
from .orchestrator.approval_gate import get_approval_gate
from .orchestrator.ioc_review_gate import get_ioc_review_gate
from .orchestrator.incident_store import get_incident_store
from .runtime import (
    clear_internal_http_client,
    get_audit_trail as runtime_get_audit_trail,
    get_chain_of_custody as runtime_get_chain_of_custody,
    get_settings_cached,
    get_siem_consumer as runtime_get_siem_consumer,
    get_threat_intel_client as runtime_get_threat_intel_client,
    set_internal_http_client,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings_cached()
    app = FastAPI(title="Forensics AI API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup() -> None:
        transport = httpx.ASGITransport(app=app)
        client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
        set_internal_http_client(client)
        await get_approval_gate().close()
        get_incident_store().clear()
        get_ioc_review_gate().clear()
        get_event_bus().clear()
        get_approval_gate().clear()
        _ = runtime_get_audit_trail()
        _ = runtime_get_chain_of_custody()
        _ = runtime_get_siem_consumer()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await get_approval_gate().close()
        client = None
        try:
            client = runtime_get_siem_consumer().client
        except RuntimeError:
            client = None
        if client is not None:
            await client.aclose()
        try:
            await runtime_get_threat_intel_client().client.aclose()
        except Exception:  # noqa: BLE001
            pass
        clear_internal_http_client()

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Return a basic liveness response."""
        return {"status": "ok"}

    app.include_router(incidents.router, prefix="/api/v1")
    app.include_router(ioc.router, prefix="/api/v1")
    app.include_router(approvals.router, prefix="/api/v1")
    app.include_router(mitre.router, prefix="/api/v1")
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(stream.router, prefix="/api/v1")
    app.include_router(settings_api.router, prefix="/api/v1")

    # Mount mock routers
    app.include_router(mock_siem.router)
    app.include_router(mock_soar.router)
    app.include_router(mock_host.router)

    return app


def get_siem_consumer() -> SiemConsumer:
    """Get a SIEM consumer instance."""
    return runtime_get_siem_consumer()


def get_audit_trail() -> AuditTrail:
    """Get the singleton audit trail instance."""
    return runtime_get_audit_trail()


def get_chain_of_custody() -> ChainOfCustody:
    """Get the singleton chain of custody instance."""
    return runtime_get_chain_of_custody()


app = create_app()

