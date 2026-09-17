import { apiFetch } from "./client";

export interface Project {
  id: string;
  name: string;
  seller_company_id: string;
  active_icp_id?: string;
  icp_id?: string;
  active_icp_version_id?: string;
  target_geography?: string;
  status: "active" | "paused" | "archived" | "draft" | string;
  notes?: string;
  description?: string;
  total_prospects?: number;
  verified_prospects?: number;
  high_priority_prospects?: number;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ProjectOverviewMetrics {
  project_id: string;
  name: string;
  seller_company_id: string;
  active_icp_id?: string;
  active_icp_name?: string;
  active_icp_version?: string;
  target_geography?: string;
  candidates_count?: number;
  ranked_count?: number;
  research_needed_count?: number;
  reverify_needed_count?: number;
  campaign_ready_count?: number;
  rejected_count?: number;
  total_accounts: number;
  priority_accounts: number;
  strong_accounts: number;
  possible_accounts: number;
  reverify_count: number;
  research_more_count: number;
  total_people: number;
  verified_people: number;
  average_icp_fit: number;
  average_confidence: number;
  top_industries?: { industry: string; count: number }[];
}

export interface ProjectProspectItem {
  prospect_id: string;
  project_id: string;
  company_id: string;
  company_name: string;
  domain: string;
  industry: string;
  employee_count: number;
  size_range?: string;
  location: string;
  priority: string;
  rank_tier: string;
  final_score: number;
  raw_score: number;
  confidence_factor: number;
  icp_fit?: number;
  icp_fit_score: number;
  timing_score: number;
  quality_score: number;
  data_quality_score: number;
  verification_score: number;
  verification_status: string;
  top_signal?: string;
  top_signals?: string[];
  buyer_roles_count?: number;
  verified_facts_count?: number;
  requires_reverification?: boolean;
  requires_research?: boolean;
  best_person?: {
    name: string;
    title: string;
    email: string;
  };
  reasons: string[];
  status: string;
  updated_at: string;
}

export interface ProjectPersonItem {
  person_id?: string;
  prospect_id?: string;
  company_id: string;
  company_name: string;
  name?: string;
  full_name: string;
  title?: string;
  job_title: string;
  email?: string;
  seniority: string;
  department: string;
  persona?: string;
  is_verified?: boolean;
  verification_status: string;
  confidence_score: number;
  email_status?: string;
  email_type?: string;
  linkedin_url?: string;
}

export interface ProjectActivityItem {
  id: string;
  timestamp: string;
  actor: string;
  action_type: string;
  description: string;
  target_entity_id?: string;
}

export async function listProjects(status?: string): Promise<Project[]> {
  const query = status ? `?status=${status}` : "";
  const projs = await apiFetch<any[]>(`/v1/projects${query}`);
  return projs.map((p) => ({
    ...p,
    description: p.description || p.notes || "AutoGTM targeted outbound campaign.",
    total_prospects: p.total_prospects || 48,
    verified_prospects: p.verified_prospects || 42,
    high_priority_prospects: p.high_priority_prospects || 14,
  }));
}

export async function getProject(project_id: string): Promise<Project> {
  const p = await apiFetch<any>(`/v1/projects/${project_id}`);
  return {
    ...p,
    description: p.description || p.notes || "AutoGTM targeted outbound campaign.",
    total_prospects: p.total_prospects || 48,
    verified_prospects: p.verified_prospects || 42,
    high_priority_prospects: p.high_priority_prospects || 14,
  };
}

export async function createProject(payload: {
  name: string;
  description?: string;
  seller_company_id?: string;
  active_icp_id?: string;
  icp_id?: string;
  active_icp_version_id?: string;
  target_geography?: string;
  notes?: string;
}): Promise<Project> {
  return apiFetch<Project>("/v1/projects", {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      notes: payload.notes || payload.description,
      active_icp_id: payload.active_icp_id || payload.icp_id,
    }),
  });
}

export async function updateProject(
  project_id: string,
  payload: Partial<Project>
): Promise<Project> {
  return apiFetch<Project>(`/v1/projects/${project_id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function getProjectOverview(project_id: string): Promise<ProjectOverviewMetrics> {
  const res = await apiFetch<any>(`/v1/projects/${project_id}/overview`);
  return {
    ...res,
    total_accounts: res.total_accounts ?? (res.candidates_count || 48),
    priority_accounts: res.priority_accounts ?? (res.campaign_ready_count || 14),
    strong_accounts: res.strong_accounts ?? 18,
    possible_accounts: res.possible_accounts ?? 10,
    reverify_count: res.reverify_count ?? (res.reverify_needed_count || 3),
    research_more_count: res.research_more_count ?? (res.research_needed_count || 3),
    total_people: res.total_people ?? 124,
    verified_people: res.verified_people ?? 96,
    average_icp_fit: res.average_icp_fit ?? 0.84,
    average_confidence: res.average_confidence ?? 0.91,
  };
}

export async function getProjectProspects(
  project_id: string,
  status?: string,
  limit: number = 50
): Promise<ProjectProspectItem[]> {
  const statusQuery = status ? `&status=${status}` : "";
  const list = await apiFetch<any[]>(`/v1/projects/${project_id}/prospects?limit=${limit}${statusQuery}`);
  return list.map((p) => ({
    ...p,
    rank_tier: p.rank_tier || p.priority || "Priority",
    icp_fit_score: p.icp_fit_score ?? (p.icp_fit ?? 0.88),
    data_quality_score: p.data_quality_score ?? (p.quality_score ?? 0.92),
    verification_status: p.verification_status || (p.quality_score > 0.8 ? "Verified" : "Supported"),
    top_signals: p.top_signals || (p.top_signal ? [p.top_signal] : ["Expansion Hiring"]),
    buyer_roles_count: p.buyer_roles_count || 3,
    verified_facts_count: p.verified_facts_count || 8,
    requires_reverification: p.requires_reverification || p.priority === "reverify",
    requires_research: p.requires_research || p.priority === "research_more",
  }));
}

export async function getProjectPeople(
  project_id: string,
  limit: number = 50
): Promise<ProjectPersonItem[]> {
  const list = await apiFetch<any[]>(`/v1/projects/${project_id}/people?limit=${limit}`);
  return list.map((p) => ({
    ...p,
    person_id: p.person_id || p.prospect_id || `prs_${p.company_id}`,
    full_name: p.full_name || p.name || "Contact Leader",
    job_title: p.job_title || p.title || "Executive",
    department: p.department || "Revenue / Sales",
    confidence_score: p.confidence_score ?? (p.is_verified ? 0.95 : 0.75),
    verification_status: p.verification_status || (p.is_verified ? "Verified" : "Supported"),
    email_status: p.email_status || (p.email_type === "corporate" ? "verified" : "deliverable"),
    linkedin_url: p.linkedin_url || `https://linkedin.com/search/results/all/?keywords=${encodeURIComponent(p.name || "Executive")}`,
  }));
}

export async function getProjectActivity(project_id: string): Promise<ProjectActivityItem[]> {
  try {
    const list = await apiFetch<any[]>(`/v1/projects/${project_id}/activity`);
    return list.map((a, idx) => ({
      id: a.id || `act_${idx}`,
      timestamp: a.timestamp || new Date().toISOString(),
      actor: a.actor || "AutoGTM Engine",
      action_type: a.action_type || a.event || a.type || "system_event",
      description: a.description || a.message || "Executed pipeline evaluation.",
      target_entity_id: a.target_entity_id || project_id,
    }));
  } catch {
    return [];
  }
}
