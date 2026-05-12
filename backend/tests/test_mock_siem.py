"""Tests for mock SIEM."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fai.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


def test_trigger_ransomware_alert(client: TestClient) -> None:
    """Test triggering a ransomware alert."""
    response = client.post("/mock/siem/trigger/ransomware")
    assert response.status_code == 200
    alert = response.json()
    assert "alert_id" in alert


def test_trigger_phishing_alert(client: TestClient) -> None:
    """Test triggering a phishing alert."""
    response = client.post("/mock/siem/trigger/phishing")
    assert response.status_code == 200
    alert = response.json()
    assert "alert_id" in alert


def test_trigger_invalid_scenario(client: TestClient) -> None:
    """Test triggering with invalid scenario."""
    response = client.post("/mock/siem/trigger/invalid")
    assert response.status_code == 400


def test_get_alert(client: TestClient) -> None:
    """Test retrieving an alert."""
    # Trigger alert
    trigger_response = client.post("/mock/siem/trigger/ransomware")
    alert_id = trigger_response.json()["alert_id"]

    # Retrieve alert
    response = client.get(f"/mock/siem/alert/{alert_id}")
    assert response.status_code == 200
    alert = response.json()
    assert alert["alert_id"] == alert_id


def test_get_nonexistent_alert(client: TestClient) -> None:
    """Test retrieving nonexistent alert."""
    response = client.get("/mock/siem/alert/nonexistent")
    assert response.status_code == 404


def test_list_artifacts(client: TestClient) -> None:
    """Test listing artifacts for an alert."""
    # Trigger alert
    trigger_response = client.post("/mock/siem/trigger/ransomware")
    alert_id = trigger_response.json()["alert_id"]

    # List artifacts
    response = client.get(f"/mock/siem/artifacts/{alert_id}")
    assert response.status_code == 200
    artifacts = response.json()
    assert isinstance(artifacts, list)
    if len(artifacts) > 0:
        assert "filename" in artifacts[0]
        assert "download_url" in artifacts[0]


def test_download_artifact(client: TestClient) -> None:
    """Test downloading an artifact."""
    # Trigger alert
    trigger_response = client.post("/mock/siem/trigger/ransomware")
    alert_id = trigger_response.json()["alert_id"]

    # List artifacts
    artifacts_response = client.get(f"/mock/siem/artifacts/{alert_id}")
    artifacts = artifacts_response.json()

    if len(artifacts) > 0:
        filename = artifacts[0]["filename"]
        # Download artifact
        response = client.get(f"/mock/siem/artifacts/{alert_id}/{filename}")
        assert response.status_code == 200
        assert len(response.content) > 0

