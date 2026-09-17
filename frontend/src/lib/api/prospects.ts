import { apiFetch } from "./client";

export interface RankingExplanation {
  id: string;
  score_id: string;
  reason_code: string;
  component: string;
  contribution: number;
  direction: "positive" | "negative";
  evidence_refs: string[];
}

export interface ScoreHistoryItem {
  id?: string;
  timestamp: string;
  score: number;
  rank_tier: string;
  change_reason: string;
}

export interface ProspectPerson {
  person_id?: string;
  id?: string;
  full_name: string;
  name?: string;
  job_title: string;
  title?: string;
  email?: string;
  seniority: string;
  department?: string;
  persona?: string;
  fit_score?: number;
  is_best?: boolean;
  verification_status: string;
  confidence_score?: number;
  linkedin_url?: string;
  email_status?: string;
  employment?: string;
}

export interface ProspectSignal {
  signal_id?: string;
  signal_type: string;
  title?: string;
  description?: string;
  name?: string;
  confidence_score?: number;
  confidence?: number;
  detected_at: string;
  evidence_id?: string;
}

export interface ProspectFact {
  fact_id: string;
  field_name: string;
  value: any;
  verification_status: string;
  confidence_score: number;
  last_verified_at: string;
  source_url?: string;
  evidence_id?: string;
}

export interface ProspectDetail {
  id?: string;
  prospect_id?: string;
  project_id?: string;
  company_id: string;
  company_name: string;
  domain: string;
  industry: string;
  employee_count?: number;
  size_range?: string;
  headquarters?: string;
  location?: string;
  summary?: string;
  priority?: string;
  rank_tier: string;
  final_score: number;
  raw_score?: number;
  confidence_factor?: number;
  icp_fit_score: number;
  data_quality_score: number;
  verification_status: string;
  rank_position?: number;
  account_score?: number;
  person_score?: number;
  timing_score?: number;
  quality_score?: number;
  verification_score?: number;
  status?: string;
  is_reverify?: boolean;
  reverify_details?: {
    message: string;
    stale_fields: string[];
    recommended_action: string;
  };
  is_research_more?: boolean;
  research_more_details?: {
    message: string;
    missing_fields: string[];
    recommended_action: string;
  };
  why_reasons: string[];
  disqualifiers?: string[];
  verified_facts: ProspectFact[];
  people: ProspectPerson[];
  signals: ProspectSignal[];
  score_history: ScoreHistoryItem[];
  requires_reverification?: boolean;
  requires_research?: boolean;
  updated_at?: string;
}

export async function getProspectDetail(prospect_id: string): Promise<ProspectDetail> {
  return apiFetch<ProspectDetail>(`/v1/prospects/${prospect_id}/detail`);
}

export async function triggerReverify(
  prospect_id: string
): Promise<{ job_id: string; status: string; message: string }> {
  return apiFetch(`/v1/prospects/${prospect_id}/reverify`, {
    method: "POST",
  });
}

export const triggerProspectReverify = triggerReverify;

export async function triggerResearch(
  prospect_id: string
): Promise<{ job_id: string; status: string; message: string }> {
  return apiFetch(`/v1/prospects/${prospect_id}/research`, {
    method: "POST",
  });
}

export const triggerProspectResearch = triggerResearch;

export async function executeBulkProspectAction(
  prospect_ids: string[],
  action: string
): Promise<{ job_id: string; status: string; message: string }> {
  return apiFetch("/v1/prospects/bulk-action", {
    method: "POST",
    body: JSON.stringify({ prospect_ids, action }),
  });
}

export async function triggerBulkAction(payload: {
  action: string;
  prospect_ids: string[];
}): Promise<{ job_id: string; status: string; message: string }> {
  return executeBulkProspectAction(payload.prospect_ids, payload.action);
}
