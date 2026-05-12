# Phase 5 · Frontend shell · session summary

## What was built
- Wired the frontend shell around React Router + TanStack Query: `AppShell`, sidebar, topbar, and stub pages for dashboard/incidents/detail/mitre/settings.
- Added dark-only design token mapping in `frontend/src/styles/globals.css` (FAI palette + shadcn variable bridge), typography rules, selection styling, and custom subtle scrollbars.
- Extended Tailwind config with tokenized colors, severity palette, body/mono font families, required radii, and `tailwindcss-animate` plugin.
- Added frontend runtime libs in `frontend/src/lib/`: strict TS model mirrors (`types.ts`), typed API client (`api.ts`), SSE hook with query invalidation (`sse.ts`), utility formatters (`utils.ts`), and Polish label maps (`labels.ts`).
- Added `frontend/components.json` aliases for UI utilities and built the requested UI component set under `frontend/src/components/ui/` plus reusable `SeverityBadge`.
- Added the temporary development route `/_probe` (`frontend/src/pages/_DesignProbe.tsx`) to visually verify tokens/fonts/component styling in a single screen.

## How to verify
```bash
cd /home/mario/dev/fai/frontend
npm install
npm run typecheck
npm run build
npm run dev -- --host 0.0.0.0 --port 5173
```

Then open in browser:
- `http://localhost:5173/` (dashboard shell)
- `http://localhost:5173/_probe` (design probe in dev mode)

Optional quick terminal checks used in this session:
```bash
curl -sSf http://127.0.0.1:5173 | head -n 20
curl -sSf http://127.0.0.1:5173/_probe | head -n 20
```

## Decisions taken during the phase
- Kept all page implementations as stubs per scope, and mounted `_probe` only in development (`import.meta.env.DEV`) so production routes stay clean.
- Implemented shell-ready UI primitives locally in `src/components/ui` with the required visual constraints and tokens, while keeping `components.json` aligned to `@/components/ui` aliases for follow-up shadcn expansion.
- Bound global SSE indicator to active incident stream connections (`useAnyIncidentStreamConnected`) and activated stream hook from the incident detail page.

## Known gaps / follow-ups for later phases
- Stub pages intentionally do not implement incident workflows, matrix rendering, audit tables, or settings details yet (Phase 6 scope).
- Approval card currently shows a placeholder/list state only; decision interactions remain for Phase 6.
- `_DesignProbe` file is retained for debugging reference; route is dev-only.

## Files created or modified
- `frontend/components.json`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tailwind.config.ts`
- `frontend/src/styles/globals.css`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/lib/types.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/sse.ts`
- `frontend/src/lib/utils.ts`
- `frontend/src/lib/labels.ts`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Topbar.tsx`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/src/components/ui/tabs.tsx`
- `frontend/src/components/ui/table.tsx`
- `frontend/src/components/ui/dialog.tsx`
- `frontend/src/components/ui/sheet.tsx`
- `frontend/src/components/ui/badge.tsx`
- `frontend/src/components/ui/tooltip.tsx`
- `frontend/src/components/ui/toast.tsx`
- `frontend/src/components/ui/scroll-area.tsx`
- `frontend/src/components/ui/separator.tsx`
- `frontend/src/components/ui/input.tsx`
- `frontend/src/components/ui/textarea.tsx`
- `frontend/src/components/ui/label.tsx`
- `frontend/src/components/ui/dropdown-menu.tsx`
- `frontend/src/components/ui/SeverityBadge.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/IncidentsListPage.tsx`
- `frontend/src/pages/IncidentDetailPage.tsx`
- `frontend/src/pages/MitreMatrixPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/pages/_DesignProbe.tsx`

