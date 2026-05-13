# FAI · Defense Demo Guide

This is the script for the project defense. Total target time: **8–10 minutes including Q&A**.

## Before you start

### Before the defense checklist

1. VM is running.
2. `docker compose ps` shows 3 healthy services.
3. `https://fai.mariuszderda.pl` loads the dashboard.
4. `ANTHROPIC_API_KEY` is set, so the demo is not in stub mode.
5. Run one ransomware scenario first to warm up the LLM.
6. Clear `runtime/` for a clean demo start.

### On-screen setup

- Browser open at `https://fai.mariuszderda.pl`.
- Two terminal windows visible alongside the browser:
  - `docker compose logs -f` for live backend/nginx logs.
  - `tail -f runtime/audit/*.jsonl` for live audit trail.
- Have these files ready to point at if asked:
  - `backend/fai/analysis/prompts.py` — real LLM prompts
  - `data/mitre/enterprise-attack.json` — MITRE dataset
  - `backend/tests/test_e2e_ransomware.py` — ransomware end-to-end test
  - `backend/tests/test_e2e_phishing.py` — phishing end-to-end test

## The 60-second intro

> „Forensics AI to system, który zbudowaliśmy na podstawie wymagań z czterech laboratoriów. Dzisiaj pokażę Państwu kompletny przepływ analizy incydentu: od alertu z SIEM-u, przez ekstrakcję wskaźników kompromitacji, mapowanie do MITRE ATT&CK, weryfikację threat intelligence, aż po zatwierdzenie izolacji hosta przez człowieka. W tle działa prawdziwy model Claude Sonnet, a system ma ochronę przed halucynacjami i pełny ślad audytowy. Najpierw pokażę scenariusz ransomware, a potem phishing.”

## Click-through · Ransomware

Target time: ~4 minutes.

1. **Dashboard** — point at the KPI strip and the recent incidents table.
   - Mention that the interface is a live operations console, not a static mockup.
2. **Click `Uruchom scenariusz ransomware`.**
   - Say that this creates a new incident from mock SIEM data and starts the pipeline.
3. **Pipeline tab** — watch ingest → collect → chain of custody → analysis advance live.
   - Say: „To jest SSE stream, bez odpytywania co sekundę.”
4. **IoC tab opens when the pipeline pauses on `ioc_review`.**
   - Review 3–4 extracted IoCs.
   - Reject the low-confidence internal IP with the note: `Wewnętrzny IP biura, nie incydent`.
   - Accept the remaining IoCs.
   - Click `Finalizuj i kontynuuj`.
5. **Pipeline advances to MITRE → TI → approval.**
   - Briefly switch back to Pipeline to show progression.
6. **MITRE tab.**
   - Show the matrix and point at `T1486`, `T1083`, `T1071`.
   - Click `T1486` and show the IoCs that justify it.
7. **Approval card appears bottom-right.**
   - Read the host and reason aloud.
   - Emphasize this is the human-in-the-loop gate from the course requirements.
   - Mention the kill-switch button as the emergency stop.
8. **Click `ZAAKCEPTUJ`.**
   - Point out that the host-isolation action is token-gated.
9. **Raport tab.**
   - Read the first sentence of the Polish executive summary.
   - Scroll to the timeline and IoC table.
   - Point at the chain-of-custody statement at the bottom.
10. **Audyt tab.**
    - Filter by `HALLUCINATION_REJECTED`.
    - Point at the rejected fake technique ID and say:
      - „Model może zaproponować błędny identyfikator MITRE, ale system odrzuca go przed raportem. To jest ochrona przed halucynacjami.”

## Click-through · Phishing

Target time: ~2 minutes.

1. Click `Uruchom scenariusz phishing`.
2. Skim Pipeline. At IoC review, accept all obvious malicious indicators.
3. Show the MITRE tab: `T1566`, `T1204.002`.
4. Approval card: point out that the isolation target is `mail_relay_quarantine`, not a workstation.
5. Click `ZAAKCEPTUJ` and show the report.

## Three things to point at to prove the system is real

1. **Audyt:** `HALLUCINATION_REJECTED` entries — proves the MITRE IDs are validated, not blindly trusted.
2. **Audyt or logs:** `OTX_TIMEOUT_FALLBACK_TO_MISP` or `OTX_LOOKUP_RESULT` — proves the threat-intel path is resilient.
3. **Logs:** show the mock host isolation endpoint refusing a call without approval. For example:

```bash
curl -X POST https://fai.mariuszderda.pl/mock/host/test-host/isolate
```

Without the approval token, the response is 403.

## Failure modes and recovery

- **OTX is down** → the system falls back to the local MISP JSON fixture. Show the audit trail entry.
- **Anthropic is unavailable** → switch to stub mode by omitting the API key. The demo still runs end-to-end, but explain that the model output is deterministic.
- **Approval gate times out** → the incident auto-resolves the isolation decision after TTL expiry and logs the timeout.
- **Backend restart mid-demo** → the mounted `runtime/` directory preserves the evidence, audit, and reports; reload the page after the backend is back.
- **Nginx returns 502** → verify the backend container is healthy first; the frontend static files usually recover once the backend is healthy.

## Anticipated Q&A

**Q1: Why isn’t there a real endpoint agent on the host?**  
A: The project scope is SIEM-centric. The backend consumes alert bundles from the SIEM mock, which mirrors the coursework architecture and avoids duplicating SIEM functionality.

**Q2: How do you stop MITRE hallucinations?**  
A: Every proposed technique ID is checked against the local MITRE dataset. Unknown IDs are dropped and recorded as `HALLUCINATION_REJECTED`.

**Q3: What prevents bypassing host isolation approval?**  
A: The mock host endpoint requires a one-time approval token. Without it, the request is rejected with 403.

**Q4: Why do you pause for IoC review before MITRE mapping?**  
A: It lets the analyst remove false positives before downstream analysis, which saves calls and gives a clean audit trail.

**Q5: Is the chain of custody legally admissible?**  
A: No. This is an academic prototype. The chain of custody is technically correct and auditable, but not a substitute for legal procedures.

**Q6: Can the system handle prompt injection in artifacts?**  
A: Yes. The LLM prompt explicitly treats artifact content as untrusted input and surfaces injection attempts in the `notes` field.

**Q7: What happens if the OTX API rate-limits you?**  
A: The system falls back to the local MISP data, so the workflow still completes.

**Q8: Why is the frontend behind nginx instead of a separate Node server?**  
A: Production is simpler and safer with static files served by nginx, and the backend remains isolated on an internal port.

## After the demo

If asked for a code walkthrough, open these files in order:

1. `AGENTS.md`
2. `backend/fai/analysis/prompts.py`
3. `backend/fai/analysis/mitre_mapper.py`
4. `backend/fai/orchestrator/approval_gate.py`
5. `frontend/src/components/approval/ApprovalCard.tsx`
6. `frontend/src/components/audit/AuditList.tsx`

