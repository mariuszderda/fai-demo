from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .core.audit import AuditTrail
from .core.chain_of_custody import ChainOfCustody
from .ingestion.siem_consumer import SiemConsumer
from .mocks import mock_host, mock_siem, mock_soar


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title="FAI", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Return a basic liveness response."""
        return {"status": "ok"}

    # Mount mock routers
    app.include_router(mock_siem.router)
    app.include_router(mock_soar.router)
    app.include_router(mock_host.router)

    return app


# Dependency injection helpers


@lru_cache(maxsize=1)
def get_audit_trail() -> AuditTrail:
    """Get the singleton audit trail instance."""
    runtime_dir = Path(__file__).parent.parent.parent / "runtime"
    return AuditTrail(runtime_dir)


@lru_cache(maxsize=1)
def get_chain_of_custody() -> ChainOfCustody:
    """Get the singleton chain of custody instance."""
    runtime_dir = Path(__file__).parent.parent.parent / "runtime"
    audit = get_audit_trail()
    return ChainOfCustody(runtime_dir, audit)


def get_siem_consumer(
    audit: AuditTrail = Depends(get_audit_trail),
    coc: ChainOfCustody = Depends(get_chain_of_custody),
) -> SiemConsumer:
    """Get a SIEM consumer instance."""
    client = httpx.AsyncClient(base_url="http://localhost:8080")
    return SiemConsumer("http://localhost:8080", coc, audit, client)


app = create_app()

