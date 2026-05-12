"""Tests for mock SOAR."""

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from fai.app import create_app
from fai.core.models import ApprovalDecision
from fai.orchestrator.approval_gate import get_approval_gate


def _issue_token() -> str:
    """Issue a valid one-time approval token for the mock SOAR test."""

    async def _inner() -> str:
        gate = get_approval_gate()
        approval = await gate.request("test-incident", "host-001", "test")
        decided = await gate.decide(approval.id, ApprovalDecision.APPROVED, "tester")
        assert decided.isolation_token is not None
        return decided.isolation_token

    return asyncio.run(_inner())


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


def test_create_case(client: TestClient) -> None:
    """Test creating a case."""
    response = client.post(
        "/mock/soar/case",
        json={
            "title": "Test Case",
            "severity": "high",
            "description": "Test description",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data


def test_create_observable(client: TestClient) -> None:
    """Test creating an observable."""
    # Create case
    case_response = client.post(
        "/mock/soar/case",
        json={
            "title": "Test Case",
            "severity": "high",
            "description": "Test",
        },
    )
    case_id = case_response.json()["case_id"]

    # Create observable
    response = client.post(
        "/mock/soar/observable",
        json={
            "case_id": case_id,
            "type": "ipv4",
            "value": "203.0.113.1",
            "reputation": "malicious",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "observable_id" in data


def test_isolate_host_without_token(client: TestClient) -> None:
    """Test isolating host without approval token."""
    # Create case
    case_response = client.post(
        "/mock/soar/case",
        json={
            "title": "Test Case",
            "severity": "high",
            "description": "Test",
        },
    )
    case_id = case_response.json()["case_id"]

    # Try to isolate without token
    response = client.post(
        "/mock/soar/responder/isolate-host",
        json={
            "case_id": case_id,
            "host_id": "host-001",
            "approval_token": "",
        },
    )
    assert response.status_code == 403


def test_isolate_host_with_token(client: TestClient) -> None:
    """Test isolating host with approval token."""
    token = _issue_token()
    # Create case
    case_response = client.post(
        "/mock/soar/case",
        json={
            "title": "Test Case",
            "severity": "high",
            "description": "Test",
        },
    )
    case_id = case_response.json()["case_id"]

    # Isolate with token
    response = client.post(
        "/mock/soar/responder/isolate-host",
        json={
            "case_id": case_id,
            "host_id": "host-001",
            "approval_token": token,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "job_id" in data


def test_get_case(client: TestClient) -> None:
    """Test retrieving a case."""
    # Create case
    case_response = client.post(
        "/mock/soar/case",
        json={
            "title": "Test Case",
            "severity": "high",
            "description": "Test",
        },
    )
    case_id = case_response.json()["case_id"]

    # Retrieve case
    response = client.get(f"/mock/soar/case/{case_id}")
    assert response.status_code == 200
    case = response.json()
    assert case["case_id"] == case_id
    assert "observables" in case
    assert "responder_jobs" in case

