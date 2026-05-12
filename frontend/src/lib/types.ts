export type IocType =
  | "ipv4"
  | "ipv6"
  | "domain"
  | "url"
  | "md5"
  | "sha1"
  | "sha256"
  | "file_path"
  | "email";

export type Confidence = "low" | "medium" | "high";
export type IocStatus = "pending_review" | "accepted" | "rejected";
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Reputation = "malicious" | "clean" | "unknown";
export type ApprovalDecision = "pending" | "approved" | "denied" | "killswitch" | "timeout";

export interface Artifact {
  id: string;
  incident_id: string;
  filename: string;
  source: string;
  size_bytes: number;
  sha256: string;
  collected_at_utc: string;
  collector_version: string;
}

export interface IoC {
  id: string;
  incident_id: string;
  type: IocType;
  value: string;
  confidence: Confidence;
  source_artifact_id: string;
  rationale: string;
  status: IocStatus;
  analyst_note: string | null;
  reputation: Reputation | null;
  reputation_source: string | null;
  mitre_technique_ids: string[];
}

export interface MitreTechnique {
  technique_id: string;
  name: string;
  tactic: string;
}

export interface ApprovalRequest {
  id: string;
  incident_id: string;
  host_id: string;
  reason: string;
  created_at_utc: string;
  ttl_seconds: number;
  decision: ApprovalDecision;
  decided_at_utc: string | null;
  decided_by: string | null;
  isolation_target: "host_network" | "mail_relay_quarantine";
  isolation_token: string | null;
}

export interface Incident {
  id: string;
  scenario: "ransomware" | "phishing";
  siem_alert_id: string;
  started_at_utc: string;
  severity: Severity;
  current_step: string;
  completed_at_utc: string | null;
  host_id: string | null;
  alert_summary: string | null;
  approval_id: string | null;
  isolation_target: string | null;
  isolation_decision: ApprovalDecision | null;
  report_path: string | null;
  report_md_path: string | null;
  report_html_path: string | null;
  artifact_count: number;
  ioc_count: number;
  technique_count: number;
}

export interface AuditEvent {
  id: string;
  incident_id: string;
  ts_utc: string;
  actor: string;
  action: string;
  object: string;
  sha256: string | null;
  details: Record<string, unknown>;
}

export interface IncidentSummary {
  id: string;
  scenario: "ransomware" | "phishing";
  severity: Severity;
  current_step: string;
  started_at_utc: string;
  completed_at_utc: string | null;
  ioc_count: number;
  technique_count: number;
  isolation_decision: string | null;
}

export interface IncidentCreateResponse {
  incident_id: string;
  status: "ingesting";
}

export interface IncidentDetailResponse extends Incident {
  iocs: IoC[];
}

export interface IocUpdateRequest {
  status: "accepted" | "rejected";
  analyst_note?: string | null;
}

export interface IocFinalizeRequest {
  operator: string;
}

export interface ApprovalDecideRequest {
  decision: "APPROVE" | "DENY" | "KILLSWITCH";
  decided_by: string;
}

export interface MitreMatrixTechnique {
  id: string;
  name: string;
  sub_techniques: MitreMatrixTechnique[];
}

export interface MitreMatrixTactic {
  id: string;
  name: string;
  key: string;
  techniques: MitreMatrixTechnique[];
}

export interface MitreMatrixResponse {
  tactics: MitreMatrixTactic[];
}

export interface MitreDetectedTechnique {
  technique_id: string;
  ioc_ids: string[];
  confidence: Confidence;
}

export interface MitreCoverageResponse {
  detected: MitreDetectedTechnique[];
}

export interface SettingsLlmSummary {
  provider: "anthropic" | "stub";
  model: string;
  stub_active: boolean;
}

export interface SettingsOtxSummary {
  key_present: boolean;
}

export interface SettingsMitreSummary {
  version: string;
  path: string;
  techniques_count: number;
}

export interface SettingsDirectoriesSummary {
  audit: string;
  artifacts: string;
  reports: string;
}

export interface SettingsResponse {
  llm: SettingsLlmSummary;
  otx: SettingsOtxSummary;
  mitre: SettingsMitreSummary;
  approval_ttl_seconds: number;
  directories: SettingsDirectoriesSummary;
}

export interface AuditFilters {
  action?: string;
  actor?: string;
  since?: string;
}

