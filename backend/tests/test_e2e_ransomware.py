"""End-to-end ransomware scenario test."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from fai.app import app
from fai.core.models import ApprovalDecision
from fai.runtime import get_settings_cached


def _wait_for(predicate, timeout: float = 12.0, interval: float = 0.1) -> None:
    """Wait until a predicate returns truthy."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError("Timed out waiting for condition")


def test_e2e_ransomware() -> None:
    """Run the ransomware playbook end to end in stub mode."""
    settings = get_settings_cached()
    settings.use_stub_llm = True
    settings.approval_ttl_seconds = 5

    with TestClient(app) as client:
        response = client.post("/api/v1/incidents", json={"scenario": "ransomware"})
        assert response.status_code == 202
        incident_id = response.json()["incident_id"]

        def _ioc_ready() -> bool:
            resp = client.get(f"/api/v1/incidents/{incident_id}/ioc")
            assert resp.status_code == 200
            return len(resp.json()) >= 3

        _wait_for(_ioc_ready)
        ioc_response = client.get(f"/api/v1/incidents/{incident_id}/ioc")
        iocs = ioc_response.json()
        assert iocs

        for ioc in iocs:
            update_response = client.patch(
                f"/api/v1/incidents/{incident_id}/ioc/{ioc['id']}",
                json={"status": "accepted", "analyst_note": "approved in e2e"},
            )
            assert update_response.status_code == 200

        finalize_response = client.post(
            f"/api/v1/incidents/{incident_id}/ioc/finalize",
            json={"operator": "M. Dobrowolski / QA Lead"},
        )
        assert finalize_response.status_code == 200
        assert finalize_response.json()["accepted_count"] == len(iocs)

        def _approval_ready() -> bool:
            resp = client.get("/api/v1/approvals/pending")
            assert resp.status_code == 200
            return bool(resp.json())

        _wait_for(_approval_ready)
        approval = client.get("/api/v1/approvals/pending").json()[0]
        assert approval["decision"] == ApprovalDecision.PENDING.value

        decide_response = client.post(
            f"/api/v1/approvals/{approval['id']}/decide",
            json={"decision": "APPROVE", "decided_by": "M. Dobrowolski / QA Lead"},
        )
        assert decide_response.status_code == 200
        assert decide_response.json()["isolation_token"]

        def _incident_done() -> bool:
            resp = client.get(f"/api/v1/incidents/{incident_id}")
            assert resp.status_code == 200
            return resp.json()["current_step"] == "done"

        _wait_for(_incident_done)

        incident = client.get(f"/api/v1/incidents/{incident_id}").json()
        report_path = incident["report_html_path"]
        assert report_path
        assert Path(report_path).exists()
        assert incident["current_step"] == "done"
        assert incident["isolation_decision"] == ApprovalDecision.APPROVED.value

        audit = client.get(f"/api/v1/audit/{incident_id}").json()
        actions = [entry["action"] for entry in audit]
        assert "HALLUCINATION_REJECTED" in actions
        assert "IOC_REVIEW_REQUESTED" in actions
        assert "IOC_REVIEW_FINALIZED" in actions
        assert "APPROVAL_REQUESTED" in actions
        assert "APPROVAL_DECIDED" in actions
        assert "LLM_STUB_MODE_ACTIVE" in actions
        assert "LLM_CALL_STARTED" in actions
        assert "LLM_CALL_COMPLETED" in actions
        assert "OTX_LOOKUP_RESULT" in actions
        assert "OTX_TIMEOUT_FALLBACK_TO_MISP" in actions

