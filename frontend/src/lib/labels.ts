import type { Severity } from "./types";

export const AUDIT_LABELS: Record<string, string> = {
  ARTIFACT_COLLECTED: "Zebrano artefakt",
  COC_VERIFIED: "Zweryfikowano łańcuch dowodów",
  LLM_CALL_STARTED: "Rozpoczęto wywołanie LLM",
  LLM_CALL_COMPLETED: "Zakończono wywołanie LLM",
  LLM_CALL_FAILED: "Wywołanie LLM nieudane",
  IOC_FILTERED_PRIVATE_IP: "Odfiltrowano prywatny IP",
  PROMPT_INJECTION_DETECTED: "Wykryto próbę prompt injection",
  IOC_REVIEW_REQUESTED: "Wstrzymanie na ocenę analityka",
  IOC_REVIEWED: "Ocena IoC",
  IOC_REVIEW_FINALIZED: "Zatwierdzono listę IoC",
  HALLUCINATION_REJECTED: "Odrzucono halucynację MITRE",
  OTX_LOOKUP_RESULT: "Wynik z OTX",
  OTX_TIMEOUT_FALLBACK_TO_MISP: "Timeout OTX, fallback do MISP",
  TI_LOOKUP_CAP_REACHED: "Osiągnięto limit zapytań TI",
  APPROVAL_REQUESTED: "Zażądano zgody na izolację",
  APPROVAL_DECIDED: "Decyzja w sprawie izolacji",
  SIEM_ALERT_RECEIVED: "Odebrano alert z SIEM",
  PLAYBOOK_FAILED: "Błąd playbooka",
};

export const SEVERITY_LABELS: Record<Severity, string> = {
  critical: "Krytyczny",
  high: "Wysoki",
  medium: "Średni",
  low: "Niski",
  info: "Informacyjny",
};

export const STEP_LABELS: Record<string, string> = {
  ingest: "Pobranie alertu",
  collect: "Zebranie artefaktów",
  coc: "Chain of custody",
  ioc_extraction: "Ekstrakcja IoC (LLM)",
  ioc_review: "Ocena IoC (analityk)",
  mitre_mapping: "Mapowanie MITRE",
  ti_lookup: "Wyszukanie w Threat Intel",
  approval: "Zgoda na izolację",
  report: "Generowanie raportu",
  done: "Zakończono",
};

export const APPROVAL_DECISION_LABELS: Record<string, string> = {
  pending: "Oczekuje",
  approved: "Zaakceptowano",
  denied: "Odrzucono",
  killswitch: "Kill switch",
  timeout: "Przekroczono czas",
};

export function auditLabel(code: string): string {
  return AUDIT_LABELS[code] ?? code;
}

export function severityLabel(severity: Severity): string {
  return SEVERITY_LABELS[severity];
}

export function stepLabel(step: string): string {
  return STEP_LABELS[step] ?? step;
}

export function approvalDecisionLabel(decision: string): string {
  return APPROVAL_DECISION_LABELS[decision] ?? decision;
}

