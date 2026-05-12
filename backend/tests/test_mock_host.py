"""Tests for mock host isolation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fai.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


def test_isolate_without_token(client: TestClient) -> None:
    """Test isolating host without token."""
    response = client.post("/mock/host/host-001/isolate")
    assert response.status_code == 403


def test_isolate_with_token(client: TestClient) -> None:
    """Test isolating host with token."""
    response = client.post(
        "/mock/host/host-001/isolate",
        headers={"X-Approval-Token": "test_token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["host_id"] == "host-001"
    assert data["status"] == "isolated"
    assert "isolated_at" in data


def test_restore_host(client: TestClient) -> None:
    """Test restoring a host."""
    response = client.post("/mock/host/host-001/restore")
    assert response.status_code == 200
    data = response.json()
    assert data["host_id"] == "host-001"
    assert data["status"] == "online"


def test_get_host_status(client: TestClient) -> None:
    """Test getting host status."""
    response = client.get("/mock/host/host-001")
    assert response.status_code == 200
    data = response.json()
    assert data["host_id"] == "host-001"
    assert "status" in data

