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

export function auditLabel(code: string): string {
  return AUDIT_LABELS[code] ?? code;
}

export function severityLabel(severity: Severity): string {
  return SEVERITY_LABELS[severity];
}

