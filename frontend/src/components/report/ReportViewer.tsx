import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Download } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { severityLabel } from "@/lib/labels";
import Button from "@/components/ui/button";
import SeverityBadge from "@/components/ui/SeverityBadge";

export default function ReportViewer({ incidentId }: { incidentId: string }): JSX.Element {
  const incidentQuery = useQuery({ queryKey: ["incident", incidentId], queryFn: () => api.getIncident(incidentId) });
  const [markdown, setMarkdown] = useState<string>("");
  const [mdError, setMdError] = useState<string | null>(null);

  useEffect(() => {
    const load = async (): Promise<void> => {
      setMdError(null);
      setMarkdown("");
      if (!incidentQuery.data?.report_md_path) return;
      try {
        const res = await fetch(incidentQuery.data.report_md_path);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        setMarkdown(await res.text());
      } catch {
        setMdError("Nie udało się pobrać treści raportu z report_md_path.");
      }
    };
    void load();
  }, [incidentQuery.data?.report_md_path]);

  if (incidentQuery.isLoading) {
    return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie raportu...</div>;
  }
  if (incidentQuery.isError || !incidentQuery.data) {
    return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać incydentu.</div>;
  }

  const incident = incidentQuery.data;
  if (incident.current_step !== "done") {
    return (
      <div className="rounded-sm border border-border-subtle bg-bg-surface p-4">
        <div className="space-y-2 animate-pulse">
          <div className="h-4 w-1/2 bg-bg-surface-2" />
          <div className="h-4 w-full bg-bg-surface-2" />
          <div className="h-4 w-4/5 bg-bg-surface-2" />
        </div>
        <div className="mt-3 text-sm text-text-secondary">Raport będzie gotowy po zakończeniu pipeline'a.</div>
      </div>
    );
  }

  const content = markdown || "# Raport gotowy\n\nBrak podglądu treści z lokalnej ścieżki pliku.";

  return (
    <div className="max-w-[800px] space-y-3">
      <div className="flex flex-wrap items-center gap-2 rounded-sm border border-border-subtle bg-bg-surface p-3">
        <SeverityBadge severity={incident.severity}>{severityLabel(incident.severity)}</SeverityBadge>
        <div className="font-mono text-xs">{incident.id}</div>
        <div className="text-xs text-text-secondary">wygenerowano: {incident.completed_at_utc ?? "—"}</div>
        <Button
          size="sm"
          className="ml-auto"
          onClick={() => {
            const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${incident.id}.md`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          aria-label="Pobierz Markdown"
        >
          <Download size={14} /> Pobierz Markdown
        </Button>
      </div>

      {mdError ? <div className="rounded-sm border border-severity-high bg-bg-surface p-2 text-xs text-text-secondary">{mdError}</div> : null}

      <article className="rounded-sm border border-border-subtle bg-bg-surface p-4">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ ...props }) => <h1 className="mb-3 font-mono text-xl" {...props} />,
            h2: ({ ...props }) => <h2 className="mb-2 mt-4 font-mono text-lg" {...props} />,
            h3: ({ ...props }) => <h3 className="mb-2 mt-3 font-mono text-base" {...props} />,
            a: ({ ...props }) => <a className="text-accent underline" {...props} />,
            code: ({ ...props }) => <code className="rounded-sm border border-border-subtle bg-bg-surface-2 px-1 font-mono text-xs" {...props} />,
            pre: ({ ...props }) => <pre className="overflow-auto rounded-sm border border-border-subtle bg-bg-surface-2 p-3 font-mono text-xs" {...props} />,
            table: ({ ...props }) => <table className="w-full border border-border-subtle text-xs" {...props} />,
            th: ({ ...props }) => <th className="border border-border-subtle p-1 text-left" {...props} />,
            td: ({ ...props }) => <td className="border border-border-subtle p-1" {...props} />,
          }}
        >
          {content}
        </ReactMarkdown>
      </article>
    </div>
  );
}

