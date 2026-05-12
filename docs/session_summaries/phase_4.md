# Phase 4 · Orchestrator + REST API · session summary

## What was built
- Added the orchestrator layer with in-memory `IncidentStore`, `IocReviewGate`, `ApprovalGate`, abstract `Playbook`, `RansomwarePlaybook`, `PhishingPlaybook`, and `dispatcher`.
- Wired the backend into `/api/v1` routers for incidents, IoC review, approvals, MITRE coverage, audit, SSE stream, and settings.
- Connected approval-token validation to the mock SOAR and mock host isolation endpoints using the approval gate registry.
- Extended shared models and runtime factories to support incident metadata, approval tokens, shared singletons, and background orchestration.
- Added E2E coverage for ransomware and phishing flows in stub-LLM mode, including approval, finalization, report generation, and audit verification.
- Updated legacy mock tests so they issue real approval tokens instead of bypassing the gate.

## How to verify
```bash
cd backend && pytest -q
```

```bash
cd backend && pytest -q tests/test_e2e_ransomware.py tests/test_e2e_phishing.py
```

## Decisions taken during the phase
- Used `StreamingResponse` for SSE instead of adding an extra SSE dependency.
- Kept all orchestrator state in memory, per the project constraints.
- Preserved compatibility tests by updating them to obtain valid one-time approval tokens from the gate.
- Used the application startup hook to reset in-memory state between test runs.

## Known gaps / follow-ups for later phases
- FastAPI emits deprecation warnings for `on_event` startup/shutdown hooks; these can be converted to lifespan handlers later.
- The runtime still uses a shared in-process HTTP client for mock-to-mock calls; this is acceptable for the demo but not production-grade.

## Files created or modified
- `backend/fai/app.py`
- `backend/fai/api/__init__.py`
- `backend/fai/api/approvals.py`
- `backend/fai/api/audit.py`
- `backend/fai/api/incidents.py`
- `backend/fai/api/mitre.py`
- `backend/fai/api/schemas.py`
- `backend/fai/api/settings.py`
- `backend/fai/api/stream.py`
- `backend/fai/config.py`
- `backend/fai/core/events.py`
- `backend/fai/core/models.py`
- `backend/fai/ingestion/siem_consumer.py`
- `backend/fai/mocks/mock_host.py`
- `backend/fai/mocks/mock_soar.py`
- `backend/fai/orchestrator/__init__.py`
- `backend/fai/orchestrator/approval_gate.py`
- `backend/fai/orchestrator/dispatcher.py`
- `backend/fai/orchestrator/ioc_review_gate.py`
- `backend/fai/orchestrator/incident_store.py`
- `backend/fai/orchestrator/phishing.py`
- `backend/fai/orchestrator/playbook.py`
- `backend/fai/orchestrator/ransomware.py`
- `backend/fai/runtime.py`
- `backend/tests/test_e2e_phishing.py`
- `backend/tests/test_e2e_ransomware.py`
- `backend/tests/test_mock_host.py`
- `backend/tests/test_mock_soar.py`

