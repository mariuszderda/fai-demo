import { Check, Pause, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { stepLabel } from "@/lib/labels";
import { formatDurationMs } from "@/lib/utils";

const STEPS = ["ingest", "collect", "coc", "ioc_extraction", "ioc_review", "mitre_mapping", "ti_lookup", "approval", "report"] as const;

type StepState = "pending" | "running" | "done" | "failed" | "awaiting";

function resolveStepState(step: string, currentStep: string): StepState {
  const currentIndex = STEPS.indexOf(currentStep as (typeof STEPS)[number]);
  const stepIndex = STEPS.indexOf(step as (typeof STEPS)[number]);

  if (currentStep.endsWith("_failed") && currentStep.startsWith(step)) return "failed";
  if (currentStep === step) return step === "ioc_review" || step === "approval" ? "awaiting" : "running";
  if (currentStep === "done") return "done";
  if (currentIndex > stepIndex && stepIndex !== -1) return "done";
  return "pending";
}

function StepIcon({ state }: { state: StepState }): JSX.Element {
  if (state === "done") return <Check size={14} />;
  if (state === "failed") return <X size={14} />;
  if (state === "awaiting") return <Pause size={14} />;
  return <div className="h-1.5 w-1.5 rounded-full bg-current" />;
}

export default function PipelineStepper({ incidentId }: { incidentId: string }): JSX.Element {
  const incidentQuery = useQuery({ queryKey: ["incident", incidentId], queryFn: () => api.getIncident(incidentId) });
  if (incidentQuery.isLoading) return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie pipeline...</div>;
  if (incidentQuery.isError || !incidentQuery.data) return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać stanu pipeline.</div>;

  const incident = incidentQuery.data;
  const totalDurationMs = incident.completed_at_utc ? new Date(incident.completed_at_utc).getTime() - new Date(incident.started_at_utc).getTime() : Date.now() - new Date(incident.started_at_utc).getTime();
  const avgDoneStepMs = Math.max(1, Math.round(totalDurationMs / STEPS.length));

  return (
    <div className="rounded-sm border border-border-subtle bg-bg-surface p-4">
      {STEPS.map((step, index) => {
        const state = resolveStepState(step, incident.current_step);
        const iconClass = state === "running" ? "border-accent text-accent animate-pulse-border" : state === "done" ? "border-accent text-accent" : state === "failed" ? "border-severity-critical text-severity-critical" : state === "awaiting" ? "border-severity-high text-severity-high" : "border-border-subtle text-text-muted";

        const meta = state === "done" ? step === "ioc_extraction" ? `${incident.ioc_count} IoC` : step === "mitre_mapping" ? `${incident.technique_count} technik` : step === "approval" && incident.isolation_decision ? incident.isolation_decision : formatDurationMs(avgDoneStepMs) : null;

        return (
          <div key={step} className="relative pl-8">
            <div className={`absolute left-0 top-0 flex h-5 w-5 items-center justify-center rounded-sm border bg-bg-surface-2 ${iconClass}`}>
              <StepIcon state={state} />
            </div>
            {index < STEPS.length - 1 ? <div className="absolute left-[9px] top-5 h-[calc(100%-4px)] w-px bg-border-subtle" /> : null}
            <div className="flex min-h-8 items-start justify-between pb-4">
              <div>
                <div className="text-sm text-text-primary">{stepLabel(step)}</div>
                <div className="text-xs text-text-muted">{state === "running" ? "W toku" : state === "awaiting" ? "Oczekuje" : state === "failed" ? "Błąd" : state === "done" ? "Zakończono" : "Oczekuje"}</div>
              </div>
              {meta ? <div className="font-mono text-xs text-text-secondary">{meta}</div> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}

