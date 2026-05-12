import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { Confidence, IoC, IocStatus, IocType } from "@/lib/types";
import { truncateMiddle } from "@/lib/utils";
import { toast } from "@/components/ui/toast";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import Badge from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import IoCBadge from "@/components/ioc/IoCBadge";
import IoCTable from "@/components/ioc/IoCTable";

const CONFIDENCES: Confidence[] = ["high", "medium", "low"];
const TYPES: IocType[] = ["ipv4", "ipv6", "domain", "url", "md5", "sha1", "sha256", "file_path", "email"];

function chipClass(active: boolean): string {
  return active ? "border-accent text-accent" : "border-border-strong text-text-secondary";
}

export default function IoCReviewPanel({ incidentId, currentStep }: { incidentId: string; currentStep: string }): JSX.Element {
  const queryClient = useQueryClient();
  const [typeFilter, setTypeFilter] = useState<IocType | "all">("all");
  const [confidenceFilter, setConfidenceFilter] = useState<Confidence | "all">("all");
  const [confirmOpen, setConfirmOpen] = useState(false);

  const iocQuery = useQuery({ queryKey: ["ioc", incidentId], queryFn: () => api.listIocs(incidentId) });

  const updateMutation = useMutation({
    mutationFn: ({ iocId, status, analystNote }: { iocId: string; status: "accepted" | "rejected"; analystNote?: string | null }) =>
      api.updateIoc(incidentId, iocId, { status, analyst_note: analystNote }),
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ["ioc", incidentId] });
      const prev = queryClient.getQueryData<IoC[]>(["ioc", incidentId]);
      queryClient.setQueryData<IoC[]>(["ioc", incidentId], (current = []) =>
        current.map((ioc) =>
          ioc.id === payload.iocId
            ? { ...ioc, status: payload.status === "accepted" ? "accepted" : "rejected", analyst_note: payload.analystNote ?? ioc.analyst_note }
            : ioc,
        ),
      );
      return { prev };
    },
    onError: (_err, _payload, ctx) => {
      if (ctx?.prev) {
        queryClient.setQueryData(["ioc", incidentId], ctx.prev);
      }
      toast({ title: "Nie udało się zapisać IoC", variant: "destructive" });
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["ioc", incidentId] });
      void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
    },
  });

  const finalizeMutation = useMutation({
    mutationFn: () => api.finalizeIocReview(incidentId, "M. Dobrowolski"),
    onSuccess: () => {
      setConfirmOpen(false);
      toast({ title: "Przegląd IoC zakończony" });
      void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
      void queryClient.invalidateQueries({ queryKey: ["ioc", incidentId] });
    },
    onError: () => toast({ title: "Finalizacja nie powiodła się", variant: "destructive" }),
  });

  const iocs = iocQuery.data ?? [];
  const counts = useMemo(
    () => ({
      pending: iocs.filter((i) => i.status === "pending_review").length,
      accepted: iocs.filter((i) => i.status === "accepted").length,
      rejected: iocs.filter((i) => i.status === "rejected").length,
    }),
    [iocs],
  );

  if (iocQuery.isLoading) {
    return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie IoC...</div>;
  }
  if (iocQuery.isError) {
    return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać IoC.</div>;
  }

  if (currentStep !== "ioc_review") {
    const accepted = iocs.filter((i) => i.status === "accepted");
    if (accepted.length === 0) {
      return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Brak zaakceptowanych IoC.</div>;
    }
    return <IoCTable iocs={accepted} />;
  }

  const filtered = iocs.filter((ioc) => {
    if (typeFilter !== "all" && ioc.type !== typeFilter) return false;
    if (confidenceFilter !== "all" && ioc.confidence !== confidenceFilter) return false;
    return true;
  });

  const bulkAcceptAllPending = (): void => {
    iocs.filter((ioc) => ioc.status === "pending_review").forEach((ioc) => updateMutation.mutate({ iocId: ioc.id, status: "accepted" }));
  };

  const bulkRejectLowPending = (): void => {
    iocs
      .filter((ioc) => ioc.status === "pending_review" && ioc.confidence === "low")
      .forEach((ioc) => updateMutation.mutate({ iocId: ioc.id, status: "rejected" }));
  };

  return (
    <div className="space-y-3">
      <div className="rounded-sm border border-border-subtle bg-bg-surface p-3">
        <div className="text-sm">Przegląd IoC — wybierz, które wskaźniki przejść do mapowania MITRE i sprawdzenia reputacji.</div>
        <div className="mt-1 text-xs text-text-secondary">
          {counts.pending} pending / {counts.accepted} accepted / {counts.rejected} rejected
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" onClick={bulkAcceptAllPending}>Akceptuj wszystkie pending</Button>
        <Button size="sm" variant="outline" onClick={bulkRejectLowPending}>Odrzuć wszystkie pending o niskiej pewności</Button>
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge className={chipClass(typeFilter === "all")} onClick={() => setTypeFilter("all")}>Typ: wszystkie</Badge>
        {TYPES.map((type) => (
          <Badge key={type} className={chipClass(typeFilter === type)} onClick={() => setTypeFilter(type)}>{type}</Badge>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Badge className={chipClass(confidenceFilter === "all")} onClick={() => setConfidenceFilter("all")}>Pewność: wszystkie</Badge>
        {CONFIDENCES.map((confidence) => (
          <Badge key={confidence} className={chipClass(confidenceFilter === confidence)} onClick={() => setConfidenceFilter(confidence)}>{confidence}</Badge>
        ))}
      </div>

      <div className="rounded-sm border border-border-subtle bg-bg-surface">
        <Table>
          <TableHeader>
            <tr>
              <TableHead>Typ</TableHead>
              <TableHead>Wartość</TableHead>
              <TableHead>Pewność</TableHead>
              <TableHead>Źródło</TableHead>
              <TableHead>Rationale</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Notatka analityka</TableHead>
            </tr>
          </TableHeader>
          <TableBody>
            {filtered.map((ioc) => (
              <TableRow key={ioc.id}>
                <TableCell><IoCBadge type={ioc.type} /></TableCell>
                <TableCell className="font-mono" title={ioc.value}>{truncateMiddle(ioc.value, 28)}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={ioc.confidence === "high" ? "border-accent text-accent" : ioc.confidence === "medium" ? "border-severity-info text-severity-info" : "text-text-muted"}>
                    {ioc.confidence}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">{truncateMiddle(ioc.source_artifact_id, 16)}</TableCell>
                <TableCell className="text-xs">{ioc.rationale}</TableCell>
                <TableCell>
                  <select
                    className="h-8 rounded-sm border border-border-strong bg-bg-surface-2 px-2 text-xs"
                    value={ioc.status}
                    onChange={(e) => {
                      const value = e.target.value as IocStatus;
                      if (value === "pending_review") return;
                      updateMutation.mutate({ iocId: ioc.id, status: value === "accepted" ? "accepted" : "rejected" });
                    }}
                    aria-label={`Status IoC ${ioc.value}`}
                  >
                    <option value="pending_review">Oczekuje</option>
                    <option value="accepted">Akceptuj</option>
                    <option value="rejected">Odrzuć</option>
                  </select>
                </TableCell>
                <TableCell>
                  <Input
                    defaultValue={ioc.analyst_note ?? ""}
                    className="h-8 text-xs"
                    onBlur={(e) => {
                      const value = e.target.value.trim();
                      if ((ioc.analyst_note ?? "") === value) return;
                      updateMutation.mutate({
                        iocId: ioc.id,
                        status: ioc.status === "accepted" ? "accepted" : "rejected",
                        analystNote: value || null,
                      });
                    }}
                    aria-label={`Notatka analityka dla ${ioc.value}`}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="sticky bottom-0 flex items-center justify-between rounded-sm border border-border-subtle bg-bg-elevated p-3">
        <div className="text-sm text-text-secondary">Akceptowane: {counts.accepted} · Odrzucone: {counts.rejected} · Oczekujące: {counts.pending}</div>
        <Button disabled={counts.pending > 0 || finalizeMutation.status === "pending"} onClick={() => setConfirmOpen(true)}>
          Finalizuj i kontynuuj pipeline
        </Button>
      </div>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Potwierdzenie finalizacji</DialogTitle>
            <DialogDescription>
              Zatwierdzasz {counts.accepted} IoC, odrzucasz {counts.rejected}. Pipeline ruszy dalej. Kontynuować?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>Anuluj</Button>
            <Button onClick={() => finalizeMutation.mutate()} disabled={finalizeMutation.status === "pending"}>Kontynuuj</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

