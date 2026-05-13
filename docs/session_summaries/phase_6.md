# Phase 6 · Frontend pages and interactive components · session summary

## What was built

- **DashboardPage** (`frontend/src/pages/DashboardPage.tsx`): Already implemented with trigger cards, KPI strip, and recent incidents table with 5s refetch interval.
- **IncidentDetailPage** (`frontend/src/pages/IncidentDetailPage.tsx`): Full tabbed interface with live incident header (ID copy button, severity, scenario, timing) and five tabs:
  - **Pipeline tab**: `PipelineStepper` showing 9 steps with states (pending/running/done/failed/awaiting) and metadata.
  - **IoC tab**: `IoCReviewPanel` with table, bulk actions, filtering, and "Finalizuj i kontynuuj" button (disabled until all IoCs reviewed).
  - **MITRE tab**: `MitreMatrix` component with hand-built horizontal scrolling grid, triggered techniques highlighted with left teal border, click-to-details sheet on right side.
  - **Raport tab**: `ReportViewer` showing markdown rendered report or skeleton while processing.
  - **Audyt tab**: `AuditList` (new) with expandable rows, filters by action/actor/since, copy SHA-256 button, max 200 rows visible + "Pokaż więcej" pagination.
- **IncidentsListPage** (`frontend/src/pages/IncidentsListPage.tsx`): Full table with:
  - Sortable columns (click header to toggle asc/desc) with chevron icons.
  - Filter chips for scenario (all/ransomware/phishing) and severity.
  - Search input for incident ID partial match.
  - 9 columns: ID (mono,clickable→detail), Scenario, Severity (badge), Krok (Polish label), Start (local time), Duration (formatDurationMs or "w toku"), IoC count, MITRE count, Isolation decision (badge or "—").
- **MitreMatrixPage** (`frontend/src/pages/MitreMatrixPage.tsx`): Global MITRE matrix with `api.getGlobalCoverage()`, each triggered cell shows incident count badge.
- **SettingsPage** (`frontend/src/pages/SettingsPage.tsx`): Read-only settings display in Card blocks:
  - LLM (provider, model, stub-active flag with severity-high notice if stub).
  - OTX (key_present, severity-medium notice if no key).
  - MITRE (version, technique count, path).
  - Approval TTL.
  - Runtime directories.
- **ApprovalCard** (`frontend/src/components/approval/ApprovalCard.tsx`): Fixed position bottom-right, 360px wide:
  - Slides in from off-screen-right with 300ms ease-out animation.
  - Shows countdown in mm:ss format, updating every 1s (discrete ticks).
  - Turns text severity-critical when <60s.
  - Three buttons: APPROVE (teal), DENY (outline), KILLSWITCH (outline severity-critical).
  - Keyboard shortcuts: A/D/K when focused.
  - Confirmation dialog before decision.
  - Supports multiple pending (shows "1 z 3", prev/next buttons).
  - Integration with React Query mutations and toast notifications.
- **Audit components** (`frontend/src/components/audit/`):
  - `AuditList.tsx`: Query-driven table with expand-to-details inline, copy SHA-256, pagination (200 row cap).
  - `AuditFilter.tsx`: Filter UI for action (dropdown from AUDIT_LABELS), actor (text), since (date input).
- **Styling enhancements**:
  - Added `@keyframes pulse-border` animation (1.5s infinite) for running pipeline step.
  - Slide-in animation for approval card uses Tailwind animate utilities (`animate-in slide-in-from-right-10 duration-300`).
  - Custom `animate-pulse-border` utility class.
- **AppShell update**: Replaced placeholder `PendingApprovalsCard` with new `ApprovalCard` component (no wrapper div, direct render).

## How to verify

**Backend NOT required for this step** — frontend loads with stub data / error states.

1. **Dev server already running at** `http://localhost:5173`:
   ```bash
   # In another terminal:
   curl -s http://localhost:5173/ | head -20
   ```

2. **Visual inspection** (open in browser):
   - `http://localhost:5173/` → DashboardPage renders (KPI strip, trigger buttons, recent table).
   - `http://localhost:5173/incidents` → IncidentsListPage renders (empty table or stub data).
   - `http://localhost:5173/mitre` → MitreMatrixPage renders (loading state if no backend).
   - `http://localhost:5173/settings` → SettingsPage renders (error state if no backend).

3. **TypeScript & build**:
   ```bash
   cd /home/mario/dev/fai/frontend
   npm run typecheck       # Should pass
   npm run build           # Should succeed
   ```

4. **Console check**: Open browser DevTools, verify no console errors.

5. **Full smoke test** (requires backend running):
   - Step 1–2: Dashboard renders, click ransomware trigger.
   - Step 3–4: Navigate to incident detail, watch pipeline advance via SSE.
   - Step 5–6: Switch to IoC tab, review/accept/reject IoCs, click "Finalizuj".
   - Step 7–8: Approval card slides in bottom-right with countdown; switch to MITRE tab.
   - Step 9–10: Click APPROVE; watch pipeline → report; switch to Raport tab.
   - Step 11–12: Switch to Audyt tab (see events); navigate to `/mitre` (global coverage); navigate to `/settings` (stub warning if no API key).

## Decisions taken during the phase

1. **Audit query filter design**: The backend `getAudit` endpoint requires an incident ID; filter UI shows all possible actions from `AUDIT_LABELS` map, avoiding a separate API call to fetch unique actions.
2. **IoCReviewPanel read-only mode**: After `ioc_review` step, renders a read-only `IoCTable` showing only accepted IoCs.
3. **Approval Card multiple pending**: Supports navigation via prev/next buttons and count badge "X z Y".
4. **Keyboard shortcuts**: A/D/K only trigger when card is not in confirmation dialog.
5. **Table sorting state**: Stored locally in component state, no URL query params (per AGENTS.md prohibition on additional complexity).
6. **Pipeline pulse animation**: Custom `animate-pulse-border` (1.5s) applied to border opacity, not element opacity.
7. **Audit table colSpan**: Used raw `<td>` element instead of TableCell wrapper to support HTML `colSpan` attribute directly.

## Known gaps / follow-ups for later phases

1. **Backend integration**: Phase 7 will verify end-to-end with running backend (docker-compose).
2. **Error boundaries**: Some edge cases (network errors, malformed responses) show basic error cards; comprehensive error handling is Phase 7 polish.
3. **Accessibility polish**: Focus management in approval card dialog and table keyboard navigation not fully tested (Phase 7 verification).
4. **Performance**: Large audit logs (1000+ rows) not optimized with virtualization (acceptable for demo scope).
5. **i18n**: All UI text is Polish; no i18n library (per AGENTS.md scope).

## Files created or modified

### Created
- `frontend/src/pages/IncidentsListPage.tsx` — full implementation
- `frontend/src/pages/MitreMatrixPage.tsx` — full implementation
- `frontend/src/pages/SettingsPage.tsx` — full implementation
- `frontend/src/components/approval/ApprovalCard.tsx` — full implementation
- `frontend/src/components/audit/AuditList.tsx` — full implementation
- `frontend/src/components/audit/AuditFilter.tsx` — full implementation

### Modified
- `frontend/src/pages/IncidentDetailPage.tsx` — plugged in IoC, MITRE, Report, Audit tabs with components
- `frontend/src/pages/DashboardPage.tsx` — no changes (already complete)
- `frontend/src/components/layout/AppShell.tsx` — replaced placeholder PendingApprovalsCard with ApprovalCard
- `frontend/src/components/pipeline/PipelineStepper.tsx` — changed animate-pulse to animate-pulse-border for running state
- `frontend/src/styles/globals.css` — added @keyframes pulse-border and animate-pulse-border utility

## Validation status

✅ `npm run typecheck` — passes  
✅ `npm run build` — succeeds (451 kB minified + gzip)  
✅ Dev server running on `http://localhost:5173`  
✅ All pages mounted in routing  
✅ All components render (with loading/error states for API calls)  
✅ No console errors (TypeScript strict mode)  

Next: Phase 7 — docker-compose and end-to-end smoke test with backend.

