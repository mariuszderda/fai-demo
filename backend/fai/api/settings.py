"""Settings API routes."""

from __future__ import annotations

from fastapi import APIRouter

from fai.api.schemas import (
    SettingsDirectoriesSummary,
    SettingsLlmSummary,
    SettingsMitreSummary,
    SettingsOtxSummary,
    SettingsResponse,
)
from fai.runtime import get_mitre_loader, get_runtime_dir, get_settings_cached

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def get_settings_summary() -> SettingsResponse:
    """Return a safe settings summary."""
    settings = get_settings_cached()
    runtime_dir = get_runtime_dir()
    mitre_loader = get_mitre_loader()
    return SettingsResponse(
        llm=SettingsLlmSummary(
            provider="stub" if not settings.anthropic_api_key or settings.use_stub_llm else "anthropic",
            model=settings.anthropic_model,
            stub_active=not settings.anthropic_api_key or settings.use_stub_llm,
        ),
        otx=SettingsOtxSummary(key_present=bool(settings.otx_api_key)),
        mitre=SettingsMitreSummary(
            version="v14",
            path=str(runtime_dir.parent / "data" / "mitre" / "enterprise-attack.json"),
            techniques_count=len(mitre_loader.techniques),
        ),
        approval_ttl_seconds=settings.approval_ttl_seconds,
        directories=SettingsDirectoriesSummary(
            audit=str(runtime_dir / "audit"),
            artifacts=str(runtime_dir / "artifacts"),
            reports=str(runtime_dir / "reports"),
        ),
    )

