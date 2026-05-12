"""Tests for core models."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from fai.core.models import (
    AuditEvent,
    Confidence,
    IocStatus,
    IocType,
    MitreTechnique,
    Severity,
)


def test_audit_event_creation() -> None:
    """Test creating an audit event."""
    event = AuditEvent(
        incident_id="test_incident",
        actor="system",
        action="TEST_ACTION",
        object="test_object",
        ts_utc=datetime.now(timezone.utc),
    )
    assert event.incident_id == "test_incident"
    assert event.actor == "system"
    assert event.action == "TEST_ACTION"


def test_mitre_technique_validation() -> None:
    """Test MITRE technique ID validation."""
    # Valid IDs
    tech1 = MitreTechnique(technique_id="T1234", name="Test", tactic="Tactic")
    assert tech1.technique_id == "T1234"

    tech2 = MitreTechnique(technique_id="T1234.567", name="Test", tactic="Tactic")
    assert tech2.technique_id == "T1234.567"

    # Invalid IDs
    with pytest.raises(ValueError):
        MitreTechnique(technique_id="INVALID", name="Test", tactic="Tactic")

    with pytest.raises(ValueError):
        MitreTechnique(technique_id="T123", name="Test", tactic="Tactic")


def test_enums() -> None:
    """Test enum values."""
    assert IocType.IPV4.value == "ipv4"
    assert Confidence.HIGH.value == "high"
    assert IocStatus.PENDING_REVIEW.value == "pending_review"
    assert Severity.CRITICAL.value == "critical"

