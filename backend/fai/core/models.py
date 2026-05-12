"""Pydantic v2 models for the entire system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class IocType(str, Enum):
    """Indicator of Compromise type enumeration."""

    IPV4 = "ipv4"
    IPV6 = "ipv6"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    FILE_PATH = "file_path"
    EMAIL = "email"


class Confidence(str, Enum):
    """Confidence level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IocStatus(str, Enum):
    """Indicator of Compromise status enumeration."""

    PENDING_REVIEW = "pending_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Severity(str, Enum):
    """Incident severity enumeration."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Reputation(str, Enum):
    """Reputation enumeration."""

    MALICIOUS = "malicious"
    CLEAN = "clean"
    UNKNOWN = "unknown"


class Artifact(BaseModel):
    """Collected evidence artifact."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    filename: str
    source: str
    size_bytes: int
    sha256: str
    collected_at_utc: datetime
    collector_version: str

    @field_validator("collected_at_utc", mode="before")
    @classmethod
    def validate_datetime_utc(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware UTC."""
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("Datetime must be timezone-aware")
        return v


class IoC(BaseModel):
    """Indicator of Compromise."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    type: IocType
    value: str
    confidence: Confidence
    source_artifact_id: str
    rationale: str
    status: IocStatus = IocStatus.PENDING_REVIEW
    analyst_note: str | None = None
    reputation: Reputation | None = None
    reputation_source: str | None = None
    mitre_technique_ids: list[str] = Field(default_factory=list)


class MitreTechnique(BaseModel):
    """MITRE ATT&CK technique."""

    technique_id: str
    name: str
    tactic: str

    @field_validator("technique_id")
    @classmethod
    def validate_technique_id(cls, v: str) -> str:
        """Validate MITRE technique ID format (T#### or T####.###)."""
        import re

        if not re.match(r"^T\d{4}(\.\d{3})?$", v):
            raise ValueError(f"Invalid technique ID format: {v}")
        return v


class ApprovalDecision(str, Enum):
    """Approval decision enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    KILLSWITCH = "killswitch"
    TIMEOUT = "timeout"


class ApprovalRequest(BaseModel):
    """Approval request for isolation action."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    host_id: str
    reason: str
    created_at_utc: datetime
    ttl_seconds: int
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decided_at_utc: datetime | None = None
    decided_by: str | None = None
    isolation_target: Literal["host_network", "mail_relay_quarantine"] = (
        "host_network"
    )

    @field_validator("created_at_utc", "decided_at_utc", mode="before")
    @classmethod
    def validate_datetime_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware UTC."""
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("Datetime must be timezone-aware")
        return v


class Incident(BaseModel):
    """Security incident record."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    scenario: Literal["ransomware", "phishing"]
    siem_alert_id: str
    started_at_utc: datetime
    severity: Severity = Severity.INFO
    current_step: str
    completed_at_utc: datetime | None = None

    @field_validator("started_at_utc", "completed_at_utc", mode="before")
    @classmethod
    def validate_datetime_utc(cls, v: datetime | None) -> datetime | None:
        """Ensure datetime is timezone-aware UTC."""
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("Datetime must be timezone-aware")
        return v


class AuditEvent(BaseModel):
    """Audit trail event."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    ts_utc: datetime
    actor: str
    action: str
    object: str
    sha256: str | None = None
    details: dict = Field(default_factory=dict)

    @field_validator("ts_utc", mode="before")
    @classmethod
    def validate_datetime_utc(cls, v: datetime) -> datetime:
        """Ensure datetime is timezone-aware UTC."""
        if isinstance(v, datetime):
            if v.tzinfo is None:
                raise ValueError("Datetime must be timezone-aware")
        return v


