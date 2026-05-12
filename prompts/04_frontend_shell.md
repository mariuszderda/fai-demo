# [Frontend] Vite + Tailwind + shadcn shell

> **Phase 5 of 7 · Frontend shell**
>
> This file is read by GitHub Copilot Agent Mode in IntelliJ as part of
> the FAI build. To start this phase, open Copilot Chat in IntelliJ,
> switch to Agent mode (not Ask mode), and paste the prompt below.

## Agent Mode Prompt — copy and paste this into Copilot Chat

```
You are working in agent mode on Phase 5 of the Forensics AI (FAI) project. THIS IS A FRONTEND PHASE — design and aesthetic details matter.

Read `AGENTS.md` at the repo root first — treat it as hard constraints. PAY EXTRA ATTENTION to §5 (UI design tokens) and §13 (prohibited things). NO purple/violet anywhere. NO chart libraries. Industrial-utilitarian dark theme only.

Then read the full spec for this phase at `prompts/04_frontend_shell.md` and execute it end-to-end.

The goal of this phase is: set up the React + Vite + Tailwind + shadcn/ui shell — install shadcn components, wire CSS variables, build AppShell with Sidebar and Topbar, set up routing, TanStack Query, the typed API client, and the SSE hook. Pages stay as stubs returning their name — they will be filled in Phase 6.

Build the `_DesignProbe` route as specified so I can visually verify the design tokens are wired correctly before we proceed.

When done, run `npm run dev`, open the dashboard and the `_probe` route, verify visually. Summarize and stop.
```

---

## Full specification

The rest of this document is the detailed spec the agent will read from
disk after you send the prompt above. You don't need to copy it — the
agent will open this file itself.


## Goal

Build the frontend shell: shadcn/ui setup, AppShell with Sidebar and
Topbar, design tokens fully wired, routing, API client, SSE hook, and
React Query setup. After this phase, the app boots into an empty layout
that's already styled to spec, and the next issue can fill in pages.

## Scope

### 1. shadcn/ui setup

Run `npx shadcn@latest init` with these answers:
- TypeScript: yes
- Style: New York
- Base color: Zinc
- CSS variables: yes (we already have them in `globals.css` — merge,
  do not overwrite our tokens)

Then install components we will need:

```bash
npx shadcn@latest add button card tabs table dialog sheet badge \
  tooltip toast scroll-area separator input textarea label \
  dropdown-menu
```

Adjust `components.json` so `aliases.components` points to
`@/components/ui`.

**Important:** shadcn ships with its own color palette via CSS
variables. After install, edit `frontend/src/styles/globals.css` to
override the shadcn variables so they map to our tokens. For example:

```css
:root {
  /* our tokens stay as defined in Phase #1 */

  /* shadcn variables mapped onto ours */
  --background: var(--bg-base);
  --foreground: var(--text-primary);
  --card: var(--bg-surface);
  --card-foreground: var(--text-primary);
  --popover: var(--bg-elevated);
  --popover-foreground: var(--text-primary);
  --primary: var(--accent);
  --primary-foreground: var(--bg-base);
  --secondary: var(--bg-surface-2);
  --secondary-foreground: var(--text-primary);
  --muted: var(--bg-surface-2);
  --muted-foreground: var(--text-muted);
  --accent-foreground: var(--bg-base);
  --destructive: var(--severity-critical);
  --destructive-foreground: var(--text-primary);
  --border: var(--border-subtle);
  --input: var(--border-strong);
  --ring: var(--accent);
  --radius: 0.25rem;
}
```

Remove any light-mode `:root` variants shadcn adds — we are dark-only.

### 2. Global styles — `frontend/src/styles/globals.css`

Final state should include:
- Tailwind directives.
- Google Fonts import (JetBrains Mono 400/600/700, Inter Tight
  400/500/600) at the top (or in `index.html`, pick one place).
- `:root` block with all our tokens + shadcn mappings.
- `body` rules: `font-body`, color `var(--text-primary)`,
  background `var(--bg-base)`, antialiased.
- `.font-mono` → JetBrains Mono with `font-feature-settings: "tnum"`.
- `.font-body` → Inter Tight.
- `h1,h2,h3` → JetBrains Mono 600, tighter letter-spacing.
- Selection color: teal with text-primary foreground.
- Custom scrollbar styling (subtle, on `bg-surface-2`).

### 3. Tailwind config — `frontend/tailwind.config.ts`

```ts
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-base': 'var(--bg-base)',
        'bg-surface': 'var(--bg-surface)',
        'bg-surface-2': 'var(--bg-surface-2)',
        'bg-elevated': 'var(--bg-elevated)',
        'border-subtle': 'var(--border-subtle)',
        'border-strong': 'var(--border-strong)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
        accent: 'var(--accent)',
        'accent-dim': 'var(--accent-dim)',
        severity: {
          critical: 'var(--severity-critical)',
          high: 'var(--severity-high)',
          medium: 'var(--severity-medium)',
          low: 'var(--severity-low)',
          info: 'var(--severity-info)',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        body: ['"Inter Tight"', 'system-ui', 'sans-serif'],
      },
      borderRadius: { sm: '2px', DEFAULT: '4px' },
    },
  },
  plugins: [require('tailwindcss-animate')],
} satisfies Config;
```

Add `<html class="dark">` in `index.html`.

### 4. Document `lib/`

#### `frontend/src/lib/types.ts`

TypeScript mirrors of every Pydantic model from `backend/fai/core/models.py`.
Use the same field names. Generate them manually (do NOT add openapi-codegen
or similar tooling — keep it simple). Cover: `IocType`, `Confidence`,
`IocStatus`, `Severity`, `Reputation`, `Artifact`, `IoC`,
`MitreTechnique`, `ApprovalDecision`, `ApprovalRequest`, `Incident`,
`AuditEvent`, plus the matrix structure type and the settings summary
type.

#### `frontend/src/lib/api.ts`

Typed fetch wrapper.

```ts
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8080';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return res.json();
}

export const api = {
  // Incidents
  createIncident: (scenario: 'ransomware' | 'phishing') => ...,
  listIncidents: () => ...,
  getIncident: (id: string) => ...,
  verifyCoc: (id: string) => ...,

  // IoC
  listIocs: (incidentId: string) => ...,
  updateIoc: (incidentId: string, iocId: string, patch: ...) => ...,
  finalizeIocReview: (incidentId: string, operator: string) => ...,

  // Approvals
  listPendingApprovals: () => ...,
  decideApproval: (id: string, decision: ApprovalDecision, decidedBy: string) => ...,

  // MITRE
  getMitreMatrix: () => ...,
  getIncidentCoverage: (incidentId: string) => ...,
  getGlobalCoverage: () => ...,

  // Audit
  getAudit: (incidentId: string, filters?: AuditFilters) => ...,

  // Settings
  getSettings: () => ...,
};
```

#### `frontend/src/lib/sse.ts`

Hook `useIncidentStream(incidentId: string | null)`:

- Opens `EventSource` to `${API_BASE}/api/v1/incidents/${id}/stream`.
- Maintains a `lastEvent` state per event type.
- Invalidates relevant React Query keys on each event type
  (e.g. `pipeline_step` → invalidate `['incident', id]`;
  `ioc_extracted` → invalidate `['ioc', id]`).
- Returns `{ connected: boolean, lastEvent: Record<string, any> }`.
- Cleans up the EventSource on unmount.

#### `frontend/src/lib/utils.ts`

- `cn(...inputs)` using `clsx` + `tailwind-merge`.
- `formatUtcAsLocal(iso: string): string` — formats as `YYYY-MM-DD HH:mm:ss`
  in the browser's local zone, with a UTC tooltip-friendly source string.
- `formatDurationMs(ms: number): string` — `1.2s`, `45ms`, `1m 14s`.
- `truncateMiddle(s: string, length=12): string` — for incident IDs
  and SHA-256s in tables.
- `severityColor(severity): string` — returns Tailwind class.

#### `frontend/src/lib/labels.ts`

Polish label map for audit actions:

```ts
export const AUDIT_LABELS: Record<string, string> = {
  ARTIFACT_COLLECTED: 'Zebrano artefakt',
  COC_VERIFIED: 'Zweryfikowano łańcuch dowodów',
  LLM_CALL_STARTED: 'Rozpoczęto wywołanie LLM',
  LLM_CALL_COMPLETED: 'Zakończono wywołanie LLM',
  LLM_CALL_FAILED: 'Wywołanie LLM nieudane',
  IOC_FILTERED_PRIVATE_IP: 'Odfiltrowano prywatny IP',
  PROMPT_INJECTION_DETECTED: 'Wykryto próbę prompt injection',
  IOC_REVIEW_REQUESTED: 'Wstrzymanie na ocenę analityka',
  IOC_REVIEWED: 'Ocena IoC',
  IOC_REVIEW_FINALIZED: 'Zatwierdzono listę IoC',
  HALLUCINATION_REJECTED: 'Odrzucono halucynację MITRE',
  OTX_LOOKUP_RESULT: 'Wynik z OTX',
  OTX_TIMEOUT_FALLBACK_TO_MISP: 'Timeout OTX, fallback do MISP',
  TI_LOOKUP_CAP_REACHED: 'Osiągnięto limit zapytań TI',
  APPROVAL_REQUESTED: 'Zażądano zgody na izolację',
  APPROVAL_DECIDED: 'Decyzja w sprawie izolacji',
  SIEM_ALERT_RECEIVED: 'Odebrano alert z SIEM',
  PLAYBOOK_FAILED: 'Błąd playbooka',
};

export function auditLabel(code: string): string {
  return AUDIT_LABELS[code] ?? code;
}
```

Also a severity-label map.

### 5. React Query setup — `frontend/src/main.tsx`

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000, refetchOnWindowFocus: false },
  },
});
```

Wrap `<App />` in `<QueryClientProvider>` and `<BrowserRouter>`.

### 6. Routing — `frontend/src/App.tsx`

```tsx
<Routes>
  <Route element={<AppShell />}>
    <Route index element={<DashboardPage />} />
    <Route path="incidents" element={<IncidentsListPage />} />
    <Route path="incidents/:id" element={<IncidentDetailPage />} />
    <Route path="mitre" element={<MitreMatrixPage />} />
    <Route path="settings" element={<SettingsPage />} />
  </Route>
</Routes>
```

In **this** issue, the page components are stubs returning their name
in an `<h1>`. They will be implemented in Phase #6.

### 7. AppShell — `frontend/src/components/layout/AppShell.tsx`

Grid layout: 240px sidebar fixed left, topbar 48px high, main content
fills the rest. Background `bg-base`.

`<Outlet />` renders the page inside the main area.

`AppShell` also mounts the `ApprovalCard` (Phase #6) as a fixed
bottom-right card — but for this phase, mount a placeholder that shows
"no pending approvals" when the API returns none.

### 8. Sidebar — `frontend/src/components/layout/Sidebar.tsx`

- Top: brand block. Text `FAI` in JetBrains Mono 700 28px, with a 2px
  teal underline. Below it: small `text-muted` text `Forensics AI`.
- Middle: nav items rendered as `NavLink` (react-router):
  - `/` — icon `LayoutDashboard`, label "Pulpit"
  - `/incidents` — icon `ShieldAlert`, label "Incydenty"
  - `/mitre` — icon `Grid3x3`, label "MITRE ATT&CK"
  - `/settings` — icon `Settings`, label "Ustawienia"
- Active style: 2px teal left border, `bg-surface-2`, `text-primary`.
- Inactive: `text-secondary`, hover `bg-surface-2` and
  `text-primary`. 150ms transition on color/bg.
- Bottom: operator card showing initials `MD` in a 32px circle (1px
  teal border, no fill), name "M. Dobrowolski", role
  "QA Lead · Operator".

### 9. Topbar — `frontend/src/components/layout/Topbar.tsx`

- Left: breadcrumbs derived from current route.
- Right: connection indicator (small dot, green if SSE connected
  globally for any incident, gray otherwise) + a small badge if the
  app is running in stub-LLM mode. Pull this from
  `useQuery(['settings'])`.

### 10. Sanity component — `frontend/src/components/ui/SeverityBadge.tsx`

Reusable badge component:

```tsx
<Badge severity="critical">Critical</Badge>
```

Internally maps severity to colored 1px border with same-colored text
on `bg-surface-2`. No fill.

Build it now since multiple pages will use it in Phase #6.

### 11. Visual sanity check

Add `frontend/src/pages/_DesignProbe.tsx` (not in routing for prod,
mount temporarily as `/_probe` route during this phase) — a single page
that renders one of every shadcn component we installed plus our
`SeverityBadge` so we can eyeball that:
- Fonts are loading correctly.
- Colors map onto our tokens (no purple anywhere, no white-on-white).
- Buttons have the teal accent when primary.
- Dialogs render against the dark backdrop correctly.

Once verified visually, remove the `_probe` route before finishing the
phase (but keep the file in the repo, just not in routing). It's a useful
reference for future visual debugging.

## How to verify

- `cd frontend && npm ci && npm run dev` — opens at
  `http://localhost:5173`.
- All four nav items navigate to stub pages.
- Sidebar collapses correctly on viewport <1024px (responsive will
  be Phase #6's polish, but at least no overflow).
- Open Network panel: hitting `/api/v1/settings` returns 200 (after
  starting backend on 8080).
- Open `http://localhost:5173/_probe` (if you kept it during dev) —
  visual check passes.
- `npm run build` succeeds.
- `npm run typecheck` (add this script in package.json running
  `tsc --noEmit`) is clean.

## Out of scope for this phase

- Page implementations beyond stubs — Phase #6.
- ApprovalCard interactions — Phase #6.
- MITRE matrix component — Phase #6.
- IoC review panel — Phase #6.

## References

- AGENTS.md §5 (full UI design tokens spec), §6 (language conventions).
- The exact CSS variables are in AGENTS.md §5 — use them verbatim,
  do not "improve" the palette.
