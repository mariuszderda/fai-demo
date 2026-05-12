import { useParams } from "react-router-dom";

import { useIncidentStream } from "@/lib/sse";
import { truncateMiddle } from "@/lib/utils";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import PipelineStepper from "@/components/pipeline/PipelineStepper";

export default function IncidentDetailPage(): JSX.Element {
  const { id } = useParams();
  const stream = useIncidentStream(id ?? null);
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Szczegóły incydentu</h1>
        {id ? <div className="text-sm text-text-secondary">{truncateMiddle(id, 18)}</div> : null}
        {id ? <div className="text-xs text-text-muted">SSE: {stream.connected ? "połączono" : "rozłączono"}</div> : null}
      </div>

      <Tabs defaultValue="pipeline">
        <TabsList>
          <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
          <TabsTrigger value="ioc">IoC</TabsTrigger>
          <TabsTrigger value="mitre">MITRE</TabsTrigger>
          <TabsTrigger value="report">Raport</TabsTrigger>
          <TabsTrigger value="audit">Audyt</TabsTrigger>
        </TabsList>

        <TabsContent value="pipeline">
          {id ? <PipelineStepper incidentId={id} /> : <div>Brak ID incydentu.</div>}
        </TabsContent>

        <TabsContent value="ioc">
          <div>IoC — implementacja w toku...</div>
        </TabsContent>

        <TabsContent value="mitre">
          <div>MITRE — implementacja w toku...</div>
        </TabsContent>

        <TabsContent value="report">
          <div>Raport — implementacja w toku...</div>
        </TabsContent>

        <TabsContent value="audit">
          <div>Audyt — implementacja w toku...</div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

