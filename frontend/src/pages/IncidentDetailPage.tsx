import { useParams } from "react-router-dom";

import { useIncidentStream } from "@/lib/sse";
import { truncateMiddle } from "@/lib/utils";

export default function IncidentDetailPage(): JSX.Element {
  const { id } = useParams();
  const stream = useIncidentStream(id ?? null);
  return (
    <div className="space-y-2">
      <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Szczegóły incydentu</h1>
      {id ? <div className="text-sm text-text-secondary">{truncateMiddle(id, 18)}</div> : null}
      {id ? <div className="text-xs text-text-muted">SSE: {stream.connected ? "połączono" : "rozłączono"}</div> : null}
    </div>
  );
}

