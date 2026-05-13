import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { Copy } from "lucide-react";

import { api } from "@/lib/api";
import { useIncidentStream } from "@/lib/sse";
import { truncateMiddle } from "@/lib/utils";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import Button from "@/components/ui/button";
import SeverityBadge from "@/components/ui/SeverityBadge";
import { toast } from "@/components/ui/toast";
import PipelineStepper from "@/components/pipeline/PipelineStepper";
import IoCReviewPanel from "@/components/ioc/IoCReviewPanel";
import MitreMatrix from "@/components/mitre/MitreMatrix";
import ReportViewer from "@/components/report/ReportViewer";
import AuditList from "@/components/audit/AuditList";

export default function IncidentDetailPage(): JSX.Element {
  const { id } = useParams();
  const stream = useIncidentStream(id ?? null);
  const incidentQuery = useQuery({
    queryKey: ["incident", id],
    queryFn: () => api.getIncident(id!),
    enabled: !!id,
  });

  const incident = incidentQuery.data;

  const handleCopyId = (): void => {
    if (id) {
      navigator.clipboard.writeText(id).then(() => toast({ title: "ID skopiowane do schowka" }));
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Szczegóły incydentu</h1>
        <div className="mt-2 flex items-center gap-2">
          {id ? <div className="font-mono text-sm text-text-secondary">{truncateMiddle(id, 24)}</div> : null}
          {id ? (
            <Button size="sm" variant="ghost" onClick={handleCopyId} aria-label="Skopiuj ID incydentu">
              <Copy size={14} />
            </Button>
          ) : null}
          {incident ? (
            <>
              <SeverityBadge severity={incident.severity}>{incident.severity}</SeverityBadge>
              <div className="text-xs text-text-muted">{incident.scenario}</div>
              <div className="text-xs text-text-muted">{incident.started_at_utc}</div>
              {incident.current_step !== "done" ? <div className="text-xs text-text-secondary">{incident.current_step}</div> : null}
            </>
          ) : null}
        </div>
        {id ? <div className="text-xs text-text-muted">SSE: {stream.connected ? "połączono" : "rozłączono"}</div> : null}
      </div>

      <Tabs defaultValue="pipeline" className="w-full">
        <TabsList>
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
          <TabsTrigger value="ioc">IoC</TabsTrigger>
          <TabsTrigger value="mitre">MITRE</TabsTrigger>
          <TabsTrigger value="report">Raport</TabsTrigger>
          <TabsTrigger value="audit">Audyt</TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline" className="mt-4">
          {id ? <PipelineStepper incidentId={id} /> : <div>Brak ID incydentu.</div>}
        </TabsContent>

        <TabsContent value="ioc" className="mt-4">
          {id && incident ? (
            <IoCReviewPanel incidentId={id} currentStep={incident.current_step} />
          ) : (
            <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie…</div>
          )}
        </TabsContent>

        <TabsContent value="mitre" className="mt-4">
          {id ? <MitreMatrix incidentId={id} /> : <div>Brak ID incydentu.</div>}
        </TabsContent>

        <TabsContent value="report" className="mt-4">
          {id ? <ReportViewer incidentId={id} /> : <div>Brak ID incydentu.</div>}
        </TabsContent>

        <TabsContent value="audit" className="mt-4">
          {id ? <AuditList incidentId={id} /> : <div>Brak ID incydentu.</div>}
        </TabsContent>
      </Tabs>
    </div>
  );
}

