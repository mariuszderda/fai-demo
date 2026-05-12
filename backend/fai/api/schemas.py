"""Shared API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from fai.core.models import Incident, IoC


class IncidentCreateRequest(BaseModel):
    """Request body for incident creation."""

    scenario: Literal["ransomware", "phishing"]


class IncidentCreateResponse(BaseModel):
    """Response body for incident creation."""

    incident_id: str
    status: Literal["ingesting"]


class IncidentSummaryResponse(BaseModel):
    """Compact incident listing item."""

    id: str
    scenario: Literal["ransomware", "phishing"]
    severity: str
    current_step: str
    started_at_utc: datetime
    completed_at_utc: datetime | None = None
    ioc_count: int = 0
    technique_count: int = 0
    isolation_decision: str | None = None


class IncidentDetailResponse(Incident):
    """Full incident response."""

    iocs: list[IoC] = Field(default_factory=list)


class IocUpdateRequest(BaseModel):
    """Request body for IoC status updates."""

    status: Literal["accepted", "rejected"]
    analyst_note: str | None = None


class IocFinalizeRequest(BaseModel):
    """Request body for IoC review finalization."""

    operator: str


class ApprovalDecideRequest(BaseModel):
    """Request body for approval decisions."""

    decision: Literal["APPROVE", "DENY", "KILLSWITCH"]
    decided_by: str


class MitreDetectedTechnique(BaseModel):
    """MITRE coverage entry."""

    technique_id: str
    ioc_ids: list[str]
    confidence: Literal["high", "medium", "low"]


class MitreCoverageResponse(BaseModel):
    """MITRE coverage response."""

    detected: list[MitreDetectedTechnique]


class SettingsLlmSummary(BaseModel):
    """LLM settings summary."""

    provider: Literal["anthropic", "stub"]
    model: str
    stub_active: bool


class SettingsOtxSummary(BaseModel):
    """OTX settings summary."""

    key_present: bool


class SettingsMitreSummary(BaseModel):
    """MITRE settings summary."""

    version: str
    path: str
    techniques_count: int


class SettingsDirectoriesSummary(BaseModel):
    """Runtime directories summary."""

    audit: str
    artifacts: str
    reports: str


class SettingsResponse(BaseModel):
    """Settings summary response."""

    llm: SettingsLlmSummary
    otx: SettingsOtxSummary
    mitre: SettingsMitreSummary
    approval_ttl_seconds: int
    directories: SettingsDirectoriesSummary

