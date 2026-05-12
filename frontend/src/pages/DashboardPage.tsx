import { useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ShieldOff, Mail, Loader2 } from "lucide-react";

import Card, { CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import Button from "@/components/ui/button";
import Badge from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { api } from "@/lib/api";
import { formatUtcAsLocal, truncateMiddle } from "@/lib/utils";
import { toast } from "@/components/ui/toast";

export default function DashboardPage(): JSX.Element {
  const navigate = useNavigate();

  const incidentsQuery = useQuery({ queryKey: ["incidents"], queryFn: api.listIncidents, refetchInterval: 5_000 });
  const approvalsQuery = useQuery({ queryKey: ["approvals"], queryFn: api.listPendingApprovals, refetchInterval: 5_000 });

  const createIncident = useMutation({
    mutationFn: (scenario: "ransomware" | "phishing") => api.createIncident(scenario),
    onError(err) {
      toast({ title: "Nie udało się uruchomić scenariusza", description: String((err as Error).message), variant: "destructive" });
    },
    onSuccess(data) {
      navigate(`/incidents/${data.incident_id}`);
    },
  });

  const incidents = incidentsQuery.data ?? [];

  const kpis = useMemo(() => {
    const total = incidents.length;
    const inProgress = incidents.filter((i) => i.current_step !== "done").length;
    const pendingApprovals = approvalsQuery.data?.length ?? 0;
    const hallucinations = 0; // session-local / computed elsewhere; placeholder
    return { total, inProgress, pendingApprovals, hallucinations };
  }, [incidents, approvalsQuery.data]);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Forensics AI · Konsola Analityka</h1>
        <div className="text-sm text-text-secondary">Pulpit operatora · M. Dobrowolski</div>
      </div>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle className="text-base">Uruchom scenariusz</CardTitle>
          <CardDescription className="text-sm text-text-secondary">Symuluj pełny przebieg incydentu</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-4">
          <div className="flex-1">
            <Button
              size="lg"
              className="w-full flex items-start gap-3"
              onClick={() => createIncident.mutate("ransomware")}
              disabled={createIncident.status === "pending"}
              aria-label="Uruchom scenariusz ransomware"
            >
              {createIncident.status === "pending" ? <Loader2 className="h-5 w-5 animate-spin" /> : <ShieldOff className="h-5 w-5" />}
              <div className="text-left">
                <div className="font-medium">Uruchom scenariusz ransomware</div>
                <div className="text-xs text-text-secondary">Symuluje zaszyfrowanie hosta i pełną ścieżkę reakcji</div>
              </div>
            </Button>
          </div>

          <div className="flex-1">
            <Button
              size="lg"
              className="w-full flex items-start gap-3"
              onClick={() => createIncident.mutate("phishing")}
              disabled={createIncident.status === "pending"}
              aria-label="Uruchom scenariusz phishing"
            >
              {createIncident.status === "pending" ? <Loader2 className="h-5 w-5 animate-spin" /> : <Mail className="h-5 w-5" />}
              <div className="text-left">
                <div className="font-medium">Uruchom scenariusz phishing</div>
                <div className="text-xs text-text-secondary">Symuluje kliknięcie w link i kwarantannę poczty</div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <div className="flex w-full gap-3">
          <div className="flex-1 grid grid-cols-4 gap-3">
            <div className="rounded-sm border border-border-subtle bg-bg-surface p-4">
              <div className="text-2xl font-mono">{kpis.total}</div>
              <div className="text-xs text-text-secondary">Incydenty (łącznie)</div>
            </div>
            <div className="rounded-sm border border-border-subtle bg-bg-surface p-4">
              <div className="text-2xl font-mono">{kpis.inProgress}</div>
              <div className="text-xs text-text-secondary">W toku</div>
            </div>
            <div className="rounded-sm border border-border-subtle bg-bg-surface p-4">
              <div className="text-2xl font-mono">{kpis.pendingApprovals}</div>
              <div className="text-xs text-text-secondary">Oczekujące zgody</div>
            </div>
            <div className="rounded-sm border border-border-subtle bg-bg-surface p-4">
              <div className="text-2xl font-mono">{kpis.hallucinations}</div>
              <div className="text-xs text-text-secondary">Halucynacje MITRE odrzucone (sesja)</div>
            </div>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Ostatnie incydenty</CardTitle>
        </CardHeader>
        <CardContent>
          {incidentsQuery.isLoading ? (
            <div>Ładowanie…</div>
          ) : incidentsQuery.isError ? (
            <div className="text-sm text-text-secondary">Nie udało się pobrać incydentów.</div>
          ) : (
            <Table>
              <TableHeader>
                <tr>
                  <TableHead>ID</TableHead>
                  <TableHead>Scenariusz</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Krok</TableHead>
                  <TableHead>Start</TableHead>
                </tr>
              </TableHeader>
              <TableBody>
                {incidents
                  .slice()
                  .sort((a, b) => (a.started_at_utc < b.started_at_utc ? 1 : -1))
                  .slice(0, 5)
                  .map((inc) => (
                    <TableRow key={inc.id} onClick={() => navigate(`/incidents/${inc.id}`)} className="cursor-pointer">
                      <TableCell className="font-mono">{truncateMiddle(inc.id, 14)}</TableCell>
                      <TableCell>{inc.scenario}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{inc.severity}</Badge>
                      </TableCell>
                      <TableCell>{inc.current_step}</TableCell>
                      <TableCell>{formatUtcAsLocal(inc.started_at_utc)}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

