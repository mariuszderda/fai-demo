import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ChevronDown, ChevronUp } from "lucide-react";

import { api } from "@/lib/api";
import { severityLabel, stepLabel } from "@/lib/labels";
import { formatUtcAsLocal, formatDurationMs, truncateMiddle, cn } from "@/lib/utils";
import Badge from "@/components/ui/badge";
import Input from "@/components/ui/input";
import SeverityBadge from "@/components/ui/SeverityBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type SortKey = "id" | "scenario" | "severity" | "current_step" | "started_at_utc" | "duration" | "ioc_count" | "technique_count" | "isolation_decision";
type SortDirection = "asc" | "desc";

export default function IncidentsListPage(): JSX.Element {
  const navigate = useNavigate();
  const [searchId, setSearchId] = useState("");
  const [scenario, setScenario] = useState<"all" | "ransomware" | "phishing">("all");
  const [severity, setSeverity] = useState<"all" | "critical" | "high" | "medium" | "low" | "info">("all");
  const [sort, setSort] = useState<{ key: SortKey; direction: SortDirection }>({ key: "started_at_utc", direction: "desc" });

  const incidentsQuery = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents, refetchInterval: 5000 });

  const filtered = useMemo(() => {
    let items = incidentsQuery.data ?? [];

    if (searchId) {
      items = items.filter((i) => i.id.toLowerCase().includes(searchId.toLowerCase()));
    }
    if (scenario !== "all") {
      items = items.filter((i) => i.scenario === scenario);
    }
    if (severity !== "all") {
      items = items.filter((i) => i.severity === severity);
    }

    // Sort
    items.sort((a, b) => {
      let aVal: number | string;
      let bVal: number | string;

      switch (sort.key) {
        case "id":
          aVal = a.id;
          bVal = b.id;
          break;
        case "scenario":
          aVal = a.scenario;
          bVal = b.scenario;
          break;
        case "severity":
          const severityOrder: Record<string, number> = { critical: 5, high: 4, medium: 3, low: 2, info: 1 };
          aVal = severityOrder[a.severity] ?? 0;
          bVal = severityOrder[b.severity] ?? 0;
          break;
        case "current_step":
          aVal = a.current_step;
          bVal = b.current_step;
          break;
        case "started_at_utc":
          aVal = new Date(a.started_at_utc).getTime();
          bVal = new Date(b.started_at_utc).getTime();
          break;
        case "duration":
          aVal = a.completed_at_utc ? new Date(a.completed_at_utc).getTime() - new Date(a.started_at_utc).getTime() : 0;
          bVal = b.completed_at_utc ? new Date(b.completed_at_utc).getTime() - new Date(b.started_at_utc).getTime() : 0;
          break;
        case "ioc_count":
          aVal = a.ioc_count;
          bVal = b.ioc_count;
          break;
        case "technique_count":
          aVal = a.technique_count;
          bVal = b.technique_count;
          break;
        case "isolation_decision":
          aVal = a.isolation_decision ?? "";
          bVal = b.isolation_decision ?? "";
          break;
      }

      if (aVal === bVal) return 0;
      const cmp = aVal < bVal ? -1 : 1;
      return sort.direction === "asc" ? cmp : -cmp;
    });

    return items;
  }, [incidentsQuery.data, searchId, scenario, severity, sort]);

  const handleSort = (key: SortKey): void => {
    if (sort.key === key) {
      setSort({ key, direction: sort.direction === "asc" ? "desc" : "asc" });
    } else {
      setSort({ key, direction: "asc" });
    }
  };

  const SortIcon = ({ active, direction }: { active: boolean; direction?: SortDirection }): JSX.Element | null => {
    if (!active) return null;
    return direction === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  const HeaderCell = ({ label, sortKey }: { label: string; sortKey: SortKey }): JSX.Element => (
    <button
      onClick={() => handleSort(sortKey)}
      className="flex items-center gap-1 text-xs font-semibold"
      aria-sort={sort.key === sortKey ? (sort.direction === "asc" ? "ascending" : "descending") : "none"}
    >
      {label}
      <SortIcon active={sort.key === sortKey} direction={sort.direction} />
    </button>
  );

  if (incidentsQuery.isLoading) {
    return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie incydentów…</div>;
  }

  if (incidentsQuery.isError) {
    return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać incydentów.</div>;
  }

  return (
    <div className="space-y-3">
      <div>
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Incydenty</h1>
      </div>

      <div className="rounded-sm border border-border-subtle bg-bg-surface p-3">
        <div className="flex flex-wrap gap-2 mb-3">
          <div className="flex gap-1">
            {(["all", "ransomware", "phishing"] as const).map((s) => (
              <Badge
                key={s}
                className={cn("cursor-pointer", scenario === s ? "border-accent text-accent" : "border-border-strong text-text-secondary")}
                onClick={() => setScenario(s)}
              >
                {s === "all" ? "Wszystkie scenariusze" : s}
              </Badge>
            ))}
          </div>
          <div className="flex gap-1">
            {(["all", "critical", "high", "medium", "low", "info"] as const).map((sev) => (
              <Badge
                key={sev}
                className={cn("cursor-pointer", severity === sev ? "border-accent text-accent" : "border-border-strong text-text-secondary")}
                onClick={() => setSeverity(sev)}
              >
                {sev === "all" ? "Wszystkie stopnie" : severityLabel(sev as any)}
              </Badge>
            ))}
          </div>
        </div>

        <Input placeholder="Szukaj ID…" className="text-xs" value={searchId} onChange={(e) => setSearchId(e.target.value)} />
      </div>

      <div className="rounded-sm border border-border-subtle bg-bg-surface overflow-x-auto">
        <Table>
          <TableHeader>
            <tr>
              <TableHead className="cursor-pointer" onClick={() => handleSort("id")}>
                <HeaderCell label="ID" sortKey="id" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("scenario")}>
                <HeaderCell label="Scenariusz" sortKey="scenario" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("severity")}>
                <HeaderCell label="Severity" sortKey="severity" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("current_step")}>
                <HeaderCell label="Krok" sortKey="current_step" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("started_at_utc")}>
                <HeaderCell label="Start" sortKey="started_at_utc" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("duration")}>
                <HeaderCell label="Czas trwania" sortKey="duration" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("ioc_count")}>
                <HeaderCell label="IoC" sortKey="ioc_count" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("technique_count")}>
                <HeaderCell label="MITRE" sortKey="technique_count" />
              </TableHead>
              <TableHead className="cursor-pointer" onClick={() => handleSort("isolation_decision")}>
                <HeaderCell label="Izolacja" sortKey="isolation_decision" />
              </TableHead>
            </tr>
          </TableHeader>
          <TableBody>
            {filtered.map((incident) => (
              <TableRow key={incident.id} className="cursor-pointer hover:bg-bg-surface-2" onClick={() => navigate(`/incidents/${incident.id}`)}>
                <TableCell className="font-mono text-xs">{truncateMiddle(incident.id, 16)}</TableCell>
                <TableCell className="text-xs">{incident.scenario}</TableCell>
                <TableCell>
                  <SeverityBadge severity={incident.severity}>{severityLabel(incident.severity)}</SeverityBadge>
                </TableCell>
                <TableCell className="text-xs">{stepLabel(incident.current_step)}</TableCell>
                <TableCell className="text-xs" title={incident.started_at_utc}>
                  {formatUtcAsLocal(incident.started_at_utc)}
                </TableCell>
                <TableCell className="text-xs">
                  {incident.completed_at_utc
                    ? formatDurationMs(new Date(incident.completed_at_utc).getTime() - new Date(incident.started_at_utc).getTime())
                    : "w toku"}
                </TableCell>
                <TableCell className="text-xs text-center">{incident.ioc_count}</TableCell>
                <TableCell className="text-xs text-center">{incident.technique_count}</TableCell>
                <TableCell className="text-xs">{incident.isolation_decision ? <Badge variant="outline">{incident.isolation_decision}</Badge> : "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {filtered.length === 0 ? <div className="text-sm text-text-secondary text-center py-4">Brak incydentów spełniających kryteria.</div> : null}
    </div>
  );
}

