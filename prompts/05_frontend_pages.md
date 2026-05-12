# [Frontend] All pages and interactive components

> **Phase 6 of 7 · Frontend pages**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 6 of the Forensics AI (FAI) project. THIS IS THE BIGGEST PHASE — pace yourself and verify each page before moving to the next.

Read `AGENTS.md` at the repo root first. PAY EXTRA ATTENTION to §5 (UI design tokens). NO purple/violet, NO chart libraries.

Then read the full spec for this phase at `prompts/05_frontend_pages.md` and execute it end-to-end.

The goal of this phase is: implement all five pages and the persistent ApprovalCard, with full interactivity. The most important pieces are the IoCReviewPanel (Tab "IoC" in incident detail), the MITRE matrix (Tab "MITRE"), and the ApprovalCard — these are the centerpiece of the defense.

Build pages in this order: DashboardPage → IncidentDetailPage Pipeline tab → IoC tab → MITRE tab → Report tab → Audit tab → IncidentsListPage → MitreMatrixPage → SettingsPage → ApprovalCard. After each page, run the dev server and verify it renders without console errors.

When done, run the full smoke test from the spec (12 steps). Summarize and stop.
```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Implement all five pages of the FAI console with full interactivity:
DashboardPage, IncidentsListPage, IncidentDetailPage (5 tabs),
MitreMatrixPage, SettingsPage. Plus the persistent ApprovalCard. After
this phase, the demo is clickable end-to-end.

This is the biggest issue. Prioritize correctness over polish — every
required interaction must work, but spend time on the IoC review panel
and MITRE matrix since those are the centerpiece of the defense.

## Scope

### 1. DashboardPage — `frontend/src/pages/DashboardPage.tsx`

Layout: vertical stack with 32px gap.

- **H1**: `Forensics AI · Konsola Analityka` in JetBrains Mono 600 28px.
  Subtitle in `text-muted` 14px: `Pulpit operatora · M. Dobrowolski`.
- **Trigger card**: shadcn `Card` with two large buttons side-by-side.
  Each button has an icon + label + small description below in
  `text-muted`:
  - Left: `<ShieldOff />` "Uruchom scenariusz ransomware" / "Symuluje
    zaszyfrowanie hosta i pełną ścieżkę reakcji"
  - Right: `<Mail />` "Uruchom scenariusz phishing" / "Symuluje
    kliknięcie w link i kwarantannę poczty"
  - On click: `api.createIncident(scenario)`, then
    `navigate(\`/incidents/\${result.incident_id}\`)`.
  - Loading state: disabled + spinner inside button (use `Loader2` icon
    with `animate-spin`).
  - Error state: shadcn toast with error message.
- **KPI strip**: 4 stat cells in a horizontal flex with 12px gap, each
  cell is `bg-surface` with 1px subtle border, 16px padding:
  - "Incydenty (łącznie)"
  - "W toku"
  - "Oczekujące zgody"
  - "Halucynacje MITRE odrzucone (sesja)"
  Each shows a 28px mono number on top and the label in 12px
  `text-secondary` below. Pull data from `api.listIncidents()` +
  `api.listPendingApprovals()` + a computation over recent audit
  events (or just count this session via local state).
  Refetch every 5s with React Query `refetchInterval`.
- **Recent incidents**: shadcn `Card` titled "Ostatnie incydenty",
  containing a `Table` with last 5 rows. Columns: ID (truncated mono),
  scenario, severity badge, current step, time ago. Row click →
  navigate to detail.

### 2. IncidentsListPage — `frontend/src/pages/IncidentsListPage.tsx`

- H2 "Incydenty".
- Toolbar above the table:
  - Filter chips for scenario (`all` / `ransomware` / `phishing`).
  - Filter chips for severity.
  - Search input filtering by partial incident ID match.
- Full table from `api.listIncidents()`. Columns:
  - ID (mono, click to detail)
  - Scenariusz
  - Severity (badge)
  - Krok (current_step rendered with Polish label map)
  - Start (formatted local time, UTC in tooltip)
  - Czas trwania (formatDurationMs of completed_at - started_at or
    "w toku")
  - IoC (number)
  - MITRE (number of unique technique IDs across accepted IoCs)
  - Izolacja (decision badge or "—")
- Sortable on all columns (click header). Use a simple internal sort
  state, do not pull in a table library.

### 3. IncidentDetailPage — `frontend/src/pages/IncidentDetailPage.tsx`

The most complex page. Use shadcn `Tabs`:
- Header above tabs: incident ID (mono, with copy-to-clipboard icon
  button), severity badge, scenario, started at, current step.
- Tabs: "Pipeline", "IoC", "MITRE", "Raport", "Audyt".

Hook `useIncidentStream(id)` once at the top level — it invalidates
queries on SSE events so subordinate components stay fresh
automatically.

#### Tab "Pipeline" — `components/pipeline/PipelineStepper.tsx`

Vertical stepper showing 9 steps (mapping to backend `current_step`
values): `ingest`, `collect`, `coc`, `ioc_extraction`, `ioc_review`,
`mitre_mapping`, `ti_lookup`, `approval`, `report`.

Each step row:
- 20px square step icon on the left with 1px border. States:
  - pending: `bg-surface-2`, `text-muted`
  - running: `bg-surface-2`, border `accent`, **1.5s infinite pulse
    animation** on the border opacity
  - done: `bg-surface-2`, border `accent`, check icon, no animation
  - failed: `bg-surface-2`, border `severity-critical`, X icon
  - awaiting: `bg-surface-2`, border `severity-high`, pause icon
- Vertical 1px line connecting steps (`bg-border-subtle`).
- Label in Polish: "Pobranie alertu", "Zebranie artefaktów",
  "Chain of custody", "Ekstrakcja IoC (LLM)", "Ocena IoC (analityk)",
  "Mapowanie MITRE", "Wyszukanie w Threat Intel", "Zgoda na izolację",
  "Generowanie raportu".
- Right-side metadata when done: `font-mono` 12px showing duration
  and a key fact (e.g. "8 IoC", "5/8 akceptowane", "3 techniki
  zweryfikowane").

#### Tab "IoC" — `components/ioc/IoCReviewPanel.tsx` + `IoCTable.tsx`

If incident's `current_step == "ioc_review"`:

- Header strip: "Przegląd IoC — wybierz, które wskaźniki przejść do
  mapowania MITRE i sprawdzenia reputacji". Counter showing X
  pending / Y accepted / Z rejected.
- Table from `api.listIocs(id)`:
  - Checkbox column (multi-select for bulk actions, optional polish).
  - Type (use `IoCBadge` component — uppercase letter mark in a 1px
    bordered chip, e.g. "IP", "DOM", "URL", "HASH", "PATH", "EMAIL").
  - Value (mono, truncated with tooltip on full).
  - Confidence (small chip with severity-style coloring: high=teal,
    medium=info, low=muted).
  - Source artifact (truncated).
  - Rationale (full text, wrap).
  - Status: dropdown with options "Oczekuje", "Akceptuj", "Odrzuć".
    On change: optimistic update via React Query mutation
    `api.updateIoc(...)`. Failed → revert + toast.
  - Notatka analityka: small `Input` that saves on blur.
- Toolbar above table:
  - "Akceptuj wszystkie pending"
  - "Odrzuć wszystkie pending o niskiej pewności"
  - Filter by type and by confidence (chips).
- Sticky footer:
  - Left: count summary.
  - Right: primary button "Finalizuj i kontynuuj pipeline".
    Disabled if any IoC has status `pending_review`. On click:
    confirm dialog "Zatwierdzasz X IoC, odrzucasz Y. Pipeline ruszy
    dalej. Kontynuować?" → on confirm:
    `api.finalizeIocReview(id, "M. Dobrowolski")`.

If `current_step` is after `ioc_review`: render read-only `IoCTable`
showing only accepted IoCs with their final state (reputation, MITRE
techniques).

#### Tab "MITRE" — `components/mitre/MitreMatrix.tsx`

Hand-built grid. No chart library.

- Fetch the full matrix: `api.getMitreMatrix()`. Fetch coverage for
  this incident: `api.getIncidentCoverage(id)`.
- Render as a horizontal-scrolling row of columns. Each column is a
  tactic. Column header: tactic name (sticky on Y-scroll),
  technique count.
- Each technique cell: 11px mono technique ID + 12px label (truncated
  to ~22 chars).
- Untriggered cells: `bg-surface-2`, `text-muted`.
- Triggered cells: `bg-surface-2`, 2px teal left border, `text-primary`.
- Hover: `bg-elevated`. Cursor pointer on triggered cells.
- Click triggered cell: opens shadcn `Sheet` on the right with details:
  - Technique name and ID (large mono).
  - Tactic.
  - "Wykryte w tym incydencie na podstawie:" list of IoC values that
    led to this technique (link them to row in IoC tab).
  - Confidence summary.

For sub-techniques: render under the parent with a small `└` glyph
indent.

Column widths: minimum 180px each. Total width can exceed viewport
— horizontal scroll is expected.

#### Tab "Raport" — `components/report/ReportViewer.tsx`

- If report not ready yet (`current_step != "done"`):
  - Show placeholder: pulsing skeleton lines + status text "Raport
    będzie gotowy po zakończeniu pipeline'a."
- If ready:
  - Header: severity badge, incident ID, generated_at, "Pobierz
    Markdown" button (downloads as `.md` blob).
  - Body: render the markdown using `react-markdown` + `remark-gfm`
    with custom component overrides:
    - `code`: mono, `bg-surface-2`, 1px subtle border
    - `pre`: mono, `bg-surface-2`, scrollable
    - `table`: dense rows, 1px border
    - `h1/h2/h3`: JetBrains Mono 600
    - `a`: teal underline
  - Width capped at 800px for readability.

#### Tab "Audyt" — `components/audit/AuditList.tsx` + `AuditFilter.tsx`

- Filter bar: action type (multi-select dropdown from
  `AUDIT_LABELS` keys), actor (text input), time-since (datepicker or
  text input with ISO).
- Table:
  - Czas (local time, UTC tooltip).
  - Aktor.
  - Akcja (Polish label via `auditLabel(action)`, plus the raw code in
    smaller mono below).
  - Obiekt (truncated mono).
  - SHA-256 (truncated middle, copy icon).
- Row click: expand inline showing the `details` JSON pretty-printed
  in a mono block.
- Cap at 200 rows visible; "Pokaż więcej" loads next page.

### 4. MitreMatrixPage — `frontend/src/pages/MitreMatrixPage.tsx`

Same `MitreMatrix` component, but fed by
`api.getGlobalCoverage()`. Each triggered cell shows a small count
badge with the number of incidents where it was detected. Click cell
→ Sheet listing incidents (id, scenario, date, link to detail).

### 5. SettingsPage — `frontend/src/pages/SettingsPage.tsx`

Read-only. Use `Card` blocks with `dl`-style rows. From
`api.getSettings()`:

- LLM: provider, model, stub-active flag. If stub active, show a
  `severity-high` notice "Tryb stub aktywny — wywołania LLM zwracają
  predefiniowane dane. Skonfiguruj ANTHROPIC_API_KEY, aby włączyć
  realne wywołania."
- OTX: key present? If not, `severity-medium` info "Brak klucza OTX —
  używany fallback z lokalnego MISP."
- MITRE: version, technique count, dataset path.
- Approval TTL.
- Runtime directories.

No editing. The page is here for the lecturer to verify configuration
matches the documented architecture.

### 6. ApprovalCard — `frontend/src/components/approval/ApprovalCard.tsx`

Mounted in `AppShell`. Polls `api.listPendingApprovals()` every 2
seconds (or driven by SSE if open). If at least one pending:

- Fixed position bottom-right, 360px wide, 1px `severity-high` border,
  `bg-elevated`, 16px padding.
- Slides in from off-screen-right with 300ms ease-out on first appear.
- Header: "Wymagana zgoda · Izolacja hosta" in 13px JetBrains Mono 600.
- Body:
  - Host ID (mono).
  - Reason text (Polish).
  - Cel: "Sieć hosta" or "Kwarantanna mail relay" depending on
    `isolation_target`.
  - Countdown in 28px mono showing mm:ss until TTL expiry. Discrete
    1s ticks (no smooth animation). When <60s: text turns
    `severity-critical`.
- Three buttons in a row:
  - "APPROVE" (primary teal solid).
  - "DENY" (outline `border-strong`).
  - "KILLSWITCH" (outline `severity-critical`).
- Keyboard shortcuts when the card is focused: A / D / K.
- On click: confirmation dialog showing the host_id and reason,
  then `api.decideApproval(...)` with `decided_by: "M. Dobrowolski"`.
- After decision, the card animates out and the next pending (if any)
  takes its place.

If multiple pending approvals exist: show count badge "1 z 3" in
the header, with chevron buttons to switch between them.

### 7. Polish text and label maps

Wherever the backend emits English codes (audit actions, decisions,
steps), use the `labels.ts` map to render Polish. Where the backend
emits free-form (rationale, summary), pass through as-is — Polish
text from the LLM stays Polish, English stays English.

### 8. Empty/loading/error states

Every query needs:
- Loading: shadcn skeletons appropriate to the layout.
- Error: inline error block with retry button (`<RefreshCw />` icon).
- Empty: friendly Polish message.

### 9. Accessibility minimums

- Every interactive element has an accessible label.
- Focus rings use the `--ring` (teal) variable.
- All buttons reachable via Tab.
- Table sort buttons have `aria-sort`.

## How to verify

End-to-end manual smoke test (backend already running):

1. `cd frontend && npm run dev`
2. Open `http://localhost:5173`. Dashboard renders.
3. Click "Uruchom scenariusz ransomware". Navigates to detail page.
4. Pipeline tab shows ingest → collect → coc → ioc_extraction
   advancing live (via SSE).
5. After IoC extraction, pipeline pauses on `ioc_review`. Switch to
   IoC tab.
6. See ~3-5 IoCs in `pending_review`. Reject the lowest-confidence one
   (set status `Odrzuć`, add a note). Click "Akceptuj wszystkie
   pending". Footer enables. Click "Finalizuj".
7. Pipeline advances to mitre_mapping, ti_lookup, approval. Approval
   card slides in bottom-right with a countdown.
8. Switch to MITRE tab. See techniques highlighted on the matrix
   including the rejection of `T9999` (visible in audit only).
9. Click APPROVE in the approval card. Pipeline goes to report. Card
   disappears.
10. Switch to Raport tab. Read the generated report.
11. Switch to Audyt tab. Find `HALLUCINATION_REJECTED` and
    `OTX_TIMEOUT_FALLBACK_TO_MISP` entries.
12. Navigate to `/mitre`. Global matrix highlights what was detected.
13. Navigate to `/settings`. See stub-LLM warning if no API key.

Plus:
- `npm run typecheck` clean.
- `npm run build` succeeds.
- All console errors fixed.

## Out of scope for this phase

- Docker compose finalization — Phase #7.
- DEMO.md — Phase #7.
- E2E playwright tests — not in this project.

## References

- AGENTS.md §5 (design tokens), §6 (language).
- Phase #4 set up the shell components and lib helpers used here.
