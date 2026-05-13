import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Confidence, IoC, MitreMatrixTechnique } from "@/lib/types";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import Badge from "@/components/ui/badge";

interface TechniqueDetails {
  techniqueId: string;
  name: string;
  tactic: string;
  confidence: Confidence;
  iocIds: string[];
}

function flattenTechniques(techniques: MitreMatrixTechnique[], prefix = ""): Array<{ id: string; name: string }> {
  const rows: Array<{ id: string; name: string }> = [];
  for (const technique of techniques) {
    rows.push({ id: technique.id, name: `${prefix}${technique.name}` });
    if ((technique.sub_techniques ?? []).length > 0) {
      rows.push(...flattenTechniques(technique.sub_techniques ?? [], "└ "));
    }
  }
  return rows;
}

export default function MitreMatrix({ incidentId, global = false }: { incidentId?: string; global?: boolean }): JSX.Element {
  const [selected, setSelected] = useState<TechniqueDetails | null>(null);

  const matrixQuery = useQuery({ queryKey: ["mitre-matrix"], queryFn: api.getMitreMatrix });
  const coverageQuery = useQuery({
    queryKey: global ? ["mitre-global-coverage"] : ["mitre-incident-coverage", incidentId],
    queryFn: () => (global ? api.getGlobalCoverage() : api.getIncidentCoverage(incidentId as string)),
    enabled: global || Boolean(incidentId),
  });
  const iocQuery = useQuery({
    queryKey: ["ioc", incidentId],
    queryFn: () => api.listIocs(incidentId as string),
    enabled: Boolean(incidentId) && !global,
  });

  const covered = useMemo(() => {
    const map = new Map<string, { confidence: Confidence; iocIds: string[] }>();
    for (const item of coverageQuery.data?.detected ?? []) {
      map.set(item.technique_id, { confidence: item.confidence, iocIds: item.ioc_ids });
    }
    return map;
  }, [coverageQuery.data]);

  const iocById = useMemo(() => {
    const map = new Map<string, IoC>();
    for (const ioc of iocQuery.data ?? []) {
      map.set(ioc.id, ioc);
    }
    return map;
  }, [iocQuery.data]);

  if (matrixQuery.isLoading || coverageQuery.isLoading) {
    return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie macierzy MITRE...</div>;
  }
  if (matrixQuery.isError || coverageQuery.isError || !matrixQuery.data) {
    return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać danych MITRE.</div>;
  }

  return (
    <Sheet open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
      <div className="overflow-x-auto rounded-sm border border-border-subtle bg-bg-surface p-3">
        <div className="flex min-w-max gap-3">
          {matrixQuery.data.tactics.map((tactic) => (
            <div key={tactic.id} className="min-w-[180px] max-w-[220px]">
              <div className="sticky top-0 z-10 border border-border-subtle bg-bg-elevated p-2">
                <div className="text-xs font-semibold">{tactic.name}</div>
                <div className="text-[11px] text-text-secondary">{flattenTechniques(tactic.techniques).length} technik</div>
              </div>

              <div className="mt-2 space-y-1">
                {flattenTechniques(tactic.techniques).map((technique) => {
                  const hit = covered.get(technique.id);
                  const interactive = Boolean(hit);
                  return (
                    <button
                      key={technique.id}
                      type="button"
                      className={`w-full border bg-bg-surface-2 px-2 py-1 text-left transition-colors ${interactive ? "cursor-pointer border-border-subtle border-l-2 border-l-accent text-text-primary hover:bg-bg-elevated" : "cursor-default border-border-subtle text-text-muted"}`}
                      onClick={() => {
                        if (!hit) return;
                        setSelected({
                          techniqueId: technique.id,
                          name: technique.name,
                          tactic: tactic.name,
                          confidence: hit.confidence,
                          iocIds: hit.iocIds,
                        });
                      }}
                      aria-label={`Technika ${technique.id}`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-[11px]">{technique.id}</span>
                        {global && hit ? <Badge className="h-4 px-1 text-[10px]">{hit.iocIds.length}</Badge> : null}
                      </div>
                      <div className="truncate text-xs">{technique.name}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      <SheetContent side="right" className="w-[28rem] border-l border-border-subtle">
        {selected ? (
          <div>
            <SheetHeader>
              <SheetTitle className="font-mono text-xl">{selected.techniqueId}</SheetTitle>
              <SheetDescription>{selected.name}</SheetDescription>
            </SheetHeader>
            <div className="mt-4 space-y-3 text-sm">
              <div><span className="text-text-secondary">Taktyka:</span> {selected.tactic}</div>
              <div><span className="text-text-secondary">Pewność:</span> {selected.confidence}</div>
              <div className="text-text-secondary">Wykryte w tym incydencie na podstawie:</div>
              <div className="space-y-2">
                {selected.iocIds.map((iocId) => (
                  <div key={iocId} className="rounded-sm border border-border-subtle bg-bg-surface p-2 font-mono text-xs">
                    {iocById.get(iocId)?.value ?? iocId}
                  </div>
                ))}
                {selected.iocIds.length === 0 ? <div className="text-xs text-text-muted">Brak źródłowych IoC.</div> : null}
                {global ? <div className="text-xs text-text-muted">Widok globalny: API zwraca agregację po IoC, bez listy incydentów per technika.</div> : null}
              </div>
            </div>
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

