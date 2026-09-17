import { apiFetch } from "./client";

export interface SellerOverview {
  id: string;
  name?: string;
  company_name: string;
  domain: string;
  industry: string;
  employee_count?: number;
  size_range?: string;
  location?: string;
  headquarters?: string;
  tagline?: string;
  description?: string;
  summary?: string;
  products?: string[];
  capabilities?: string[];
  verification_status?: string;
  quality_gate_passed?: boolean;
  freshness?: string;
  last_crawled_at: string;
  verified_facts_count: number;
  active_icps_count?: number;
  competitors_count?: number;
}

export interface ValueProp {
  title: string;
  description: string;
}

export interface BuyerRole {
  role: string;
  departments: string[];
  seniority: string;
}

export interface ProblemSolution {
  problem: string;
  solution: string;
}

export interface CapabilityEvidence {
  capability: string;
  evidence_ref: string;
  verified: boolean;
}

export interface SellerAnalysis {
  company_name: string;
  domain: string;
  positioning: string;
  tagline?: string;
  primary_offer?: string;
  value_proposition?: string;
  value_props: ValueProp[];
  ideal_use_cases: string[];
  target_buyer_roles: BuyerRole[];
  pricing_model: string;
  differentiators: string[];
  target_audience?: string[];
  target_problems?: ProblemSolution[];
  capabilities?: CapabilityEvidence[];
  tech_stack?: string[];
  recent_announcements?: string[];
}

export interface CompetitorRelationship {
  id?: string;
  competitor_id: string;
  competitor_name: string;
  competitor_domain: string;
  overlap_score: number;
  relationship_type: string;
  shared_features: string[];
  advantages: string[];
  disadvantages: string[];
  evidence_count: number;
  confidence?: number;
  notes?: string;
}

export interface CompanyEvent {
  event_id?: string;
  event?: string;
  change?: string;
  timestamp: string;
  significance?: "high" | "medium" | "low";
  event_type?: string;
  field_name?: string;
  previous_value?: any;
  current_value?: any;
  summary?: string;
  evidence_id?: string;
}

export async function getSellerOverview(): Promise<SellerOverview> {
  const res = await apiFetch<any>("/v1/seller/overview");
  return {
    ...res,
    name: res.name || res.company_name,
    summary: res.summary || res.description,
    size_range: res.size_range || `${res.employee_count || 50} employees`,
    headquarters: res.headquarters || res.location || "San Francisco, CA",
  };
}

export async function getSellerAnalysis(): Promise<SellerAnalysis> {
  return apiFetch<SellerAnalysis>("/v1/seller/analysis");
}

export async function triggerSellerAnalyze(
  domain_or_url: string = "growxlabs.tech"
): Promise<{ job_id: string; status: string; analysis?: any }> {
  return apiFetch("/v1/seller/analyze", {
    method: "POST",
    body: JSON.stringify({ domain_or_url }),
  });
}

export const triggerSellerAnalysis = triggerSellerAnalyze;

export async function getSellerCompetitors(): Promise<CompetitorRelationship[]> {
  return apiFetch<CompetitorRelationship[]>("/v1/seller/competitors");
}

export async function getSellerHistory(): Promise<CompanyEvent[]> {
  return apiFetch<CompanyEvent[]>("/v1/seller/history");
}
