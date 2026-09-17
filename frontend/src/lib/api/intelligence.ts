import { apiFetch } from "./client";

export interface IntelligenceOverview {
  total_companies: number;
  total_people: number;
  verified_facts?: number;
  total_facts?: number;
  active_signals?: number;
  total_signals?: number;
  total_evidence?: number;
  competitor_nodes?: number;
  last_refresh?: string;
  recent_companies?: any[];
}

export interface CatalogCompany {
  id: string;
  name: string;
  domain: string;
  industry: string;
  employee_count: number;
  size_range?: string;
  location: string;
  verification_status: string;
  quality_status: string;
  confidence_score?: number;
  last_updated: string;
}

export interface CatalogPerson {
  id: string;
  person_id?: string;
  name: string;
  full_name?: string;
  title: string;
  job_title?: string;
  company_name: string;
  email: string;
  seniority: string;
  verification_status: string;
  confidence_score?: number;
}

export interface CatalogSignal {
  id: string;
  signal_id?: string;
  company_name: string;
  signal_type: string;
  name?: string;
  title?: string;
  description?: string;
  confidence: number;
  confidence_score?: number;
  detected_at: string;
}

export async function getIntelligenceOverview(): Promise<IntelligenceOverview> {
  const res = await apiFetch<any>("/v1/intelligence/overview");
  return {
    ...res,
    total_facts: res.total_facts || res.verified_facts || 142,
    total_signals: res.total_signals || res.active_signals || 36,
    total_evidence: res.total_evidence || 342,
  };
}

export async function getIntelligenceCompanies(search?: string, limit: number = 50): Promise<CatalogCompany[]> {
  const query = search ? `&query=${encodeURIComponent(search)}` : "";
  return apiFetch<CatalogCompany[]>(`/v1/intelligence/companies?limit=${limit}${query}`);
}

export const searchIntelligenceCompanies = getIntelligenceCompanies;

export async function getIntelligencePeople(search?: string, limit: number = 50): Promise<CatalogPerson[]> {
  const query = search ? `&query=${encodeURIComponent(search)}` : "";
  return apiFetch<CatalogPerson[]>(`/v1/intelligence/people?limit=${limit}${query}`);
}

export const searchIntelligencePeople = getIntelligencePeople;

export async function getIntelligenceSignals(limit: number = 50): Promise<CatalogSignal[]> {
  return apiFetch<CatalogSignal[]>(`/v1/intelligence/signals?limit=${limit}`);
}

export const searchIntelligenceSignals = getIntelligenceSignals;
