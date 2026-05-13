import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, Copy } from "lucide-react";

import { api } from "@/lib/api";
import { auditLabel } from "@/lib/labels";
import { formatUtcAsLocal, truncateMiddle } from "@/lib/utils";
import { toast } from "@/components/ui/toast";
import Button from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import AuditFilter from "./AuditFilter";

export default function AuditList({ incidentId }: { incidentId: string }): JSX.Element {
  const [filters, setFilters] = useState({ action: "", actor: "", since: "" });
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [limit, setLimit] = useState(200);

  const auditQuery = useQuery({
    queryKey: ["audit", incidentId, filters],
    queryFn: () =>
      api.getAudit(incidentId, {
        action: filters.action || undefined,
        actor: filters.actor || undefined,
        since: filters.since || undefined,
      }),
  });

  const events = useMemo(() => {
    const all = auditQuery.data ?? [];
    return all.slice(0, limit);
  }, [auditQuery.data, limit]);

  if (auditQuery.isLoading) {
    return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie audytu…</div>;
  }

  if (auditQuery.isError) {
    return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać audytu.</div>;
  }

  const toggleExpanded = (id: string): void => {
    const next = new Set(expanded);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setExpanded(next);
  };

  return (
    <div className="space-y-3">
      <AuditFilter filters={filters} setFilters={setFilters} />

      <div className="rounded-sm border border-border-subtle bg-bg-surface overflow-x-auto">
        <Table>
          <TableHeader>
            <tr>
              <TableHead className="w-12" />
              <TableHead>Czas</TableHead>
              <TableHead>Aktor</TableHead>
              <TableHead>Akcja</TableHead>
              <TableHead>Obiekt</TableHead>
              <TableHead className="w-32">SHA-256</TableHead>
            </tr>
          </TableHeader>
          <TableBody>
            {events.map((event) => (
              <tbody key={event.id}>
                <TableRow className="cursor-pointer hover:bg-bg-surface-2" onClick={() => toggleExpanded(event.id)}>
                  <TableCell>
                    <ChevronDown size={16} className={expanded.has(event.id) ? "rotate-180" : ""} />
                  </TableCell>
                  <TableCell className="text-xs text-text-secondary">{formatUtcAsLocal(event.ts_utc)}</TableCell>
                  <TableCell className="text-xs">{event.actor}</TableCell>
                  <TableCell>
                    <div className="text-xs text-text-primary">{auditLabel(event.action)}</div>
                    <div className="font-mono text-[11px] text-text-muted">{event.action}</div>
                  </TableCell>
                  <TableCell className="font-mono text-xs" title={event.object}>
                    {truncateMiddle(event.object, 20)}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <span className="font-mono text-[10px]">{event.sha256 ? truncateMiddle(event.sha256, 14) : "—"}</span>
                      {event.sha256 ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(event.sha256!).then(() => toast({ title: "SHA-256 skopiowany" }));
                          }}
                          aria-label="Skopiuj SHA-256"
                        >
                          <Copy size={12} />
                        </Button>
                      ) : null}
                    </div>
                  </TableCell>
                </TableRow>
                {expanded.has(event.id) ? (
                  <TableRow>
                    <td colSpan={6} className="p-3 border border-border-subtle">
                      <div className="rounded-sm border border-border-subtle bg-bg-surface-2 p-3 font-mono text-xs">
                        <pre>{JSON.stringify(event.details, null, 2)}</pre>
                      </div>
                    </td>
                  </TableRow>
                ) : null}
              </tbody>
            ))}
          </TableBody>
        </Table>
      </div>

      {(auditQuery.data?.length ?? 0) > limit ? (
        <Button size="sm" variant="outline" onClick={() => setLimit((prev) => prev + 200)} className="w-full">
          Pokaż więcej
        </Button>
      ) : null}
    </div>
  );
}

