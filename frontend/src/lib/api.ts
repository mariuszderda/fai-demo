import type {
  ApprovalDecideRequest,
  ApprovalRequest,
  AuditEvent,
  AuditFilters,
  IncidentCreateResponse,
  IncidentDetailResponse,
  IncidentSummary,
  IoC,
  IocFinalizeRequest,
  IocUpdateRequest,
  MitreCoverageResponse,
  MitreMatrixResponse,
  SettingsResponse,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

function queryString(filters: AuditFilters | undefined): string {
  if (!filters) {
    return "";
  }
  const params = new URLSearchParams();
  if (filters.action) {
    params.set("action", filters.action);
  }
  if (filters.actor) {
    params.set("actor", filters.actor);
  }
  if (filters.since) {
    params.set("since", filters.since);
  }
  const value = params.toString();
  return value ? `?${value}` : "";
}

export const api = {
  createIncident: (scenario: "ransomware" | "phishing") =>
    request<IncidentCreateResponse>("/api/v1/incidents", {
      method: "POST",
      body: JSON.stringify({ scenario }),
    }),
  listIncidents: () => request<IncidentSummary[]>("/api/v1/incidents"),
  getIncident: (id: string) => request<IncidentDetailResponse>(`/api/v1/incidents/${id}`),
  verifyCoc: (id: string) => request<Array<Record<string, unknown>>>(`/api/v1/incidents/${id}/verify-coc`, { method: "POST" }),

  listIocs: (incidentId: string) => request<IoC[]>(`/api/v1/incidents/${incidentId}/ioc`),
  updateIoc: (incidentId: string, iocId: string, patch: IocUpdateRequest) =>
    request<IoC>(`/api/v1/incidents/${incidentId}/ioc/${iocId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  finalizeIocReview: (incidentId: string, operator: string) =>
    request<{ accepted_count: number; rejected_count: number }>(`/api/v1/incidents/${incidentId}/ioc/finalize`, {
      method: "POST",
      body: JSON.stringify({ operator } satisfies IocFinalizeRequest),
    }),

  listPendingApprovals: () => request<ApprovalRequest[]>("/api/v1/approvals/pending"),
  decideApproval: (id: string, decision: ApprovalDecideRequest["decision"], decidedBy: string) =>
    request<ApprovalRequest>(`/api/v1/approvals/${id}/decide`, {
      method: "POST",
      body: JSON.stringify({ decision, decided_by: decidedBy } satisfies ApprovalDecideRequest),
    }),

  getMitreMatrix: () => request<MitreMatrixResponse>("/api/v1/mitre/techniques"),
  getIncidentCoverage: (incidentId: string) => request<MitreCoverageResponse>(`/api/v1/incidents/${incidentId}/mitre-coverage`),
  getGlobalCoverage: () => request<MitreCoverageResponse>("/api/v1/mitre-coverage/global"),

  getAudit: (incidentId: string, filters?: AuditFilters) =>
    request<AuditEvent[]>(`/api/v1/audit/${incidentId}${queryString(filters)}`),

    getReport: (incidentId: string) => request<{ markdown: string; html: string }>(`/api/v1/incidents/${incidentId}/report`),
    getSettings: () => request<SettingsResponse>("/api/v1/settings"),
};

