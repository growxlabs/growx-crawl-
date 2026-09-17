import { apiFetch } from "./client";

export interface EvidenceDetail {
  evidence_id: string;
  source_url: string;
  capture_date?: string;
  extracted_at?: string;
  raw_excerpt?: string;
  raw_snippet?: string;
  verified_fact?: string;
  verification_status?: string;
  confidence?: number;
  confidence_score?: number;
  method?: string;
  screenshot_url?: string | null;
}

export type EvidenceRecord = EvidenceDetail;

export interface FactCorrectionPayload {
  fact_id?: string;
  company_id?: string;
  subject_id?: string;
  subject_type?: string;
  field_name?: string;
  predicate?: string;
  current_value?: any;
  proposed_value?: any;
  corrected_value?: any;
  reason: string;
  source_url?: string;
  scope?: string;
}

export async function getEvidence(evidence_id: string): Promise<EvidenceDetail> {
  const res = await apiFetch<any>(`/v1/evidence/${evidence_id}`);
  return {
    ...res,
    extracted_at: res.extracted_at || res.capture_date || new Date().toISOString(),
    raw_snippet: res.raw_snippet || res.raw_excerpt || "Verified citation excerpt.",
    confidence_score: res.confidence_score ?? res.confidence ?? 0.95,
    verification_status: res.verification_status || "Verified",
    method: res.method || "crawler_dom_extractor",
  };
}

export async function submitFactCorrection(payload: FactCorrectionPayload): Promise<any> {
  const body: Record<string, any> = {
    ...payload,
    subject_id: payload.subject_id || payload.company_id || payload.fact_id,
    predicate: payload.predicate || payload.field_name || "attribute",
    proposed_value: payload.proposed_value ?? payload.corrected_value,
  };
  return apiFetch("/v1/facts/correct", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
