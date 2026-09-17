import { apiFetch } from "./client";

export interface ICPCriterion {
  id?: string;
  criterion_id: string;
  category: "firmographic" | "technographic" | "geographic" | "timing_signal" | "intent" | string;
  dimension: string;
  field_name?: string;
  operator: string;
  target_value: any;
  value?: any;
  weight: number;
  is_dealbreaker?: boolean;
  mandatory?: boolean;
  rationale?: string;
}

export interface ICPPersona {
  id?: string;
  persona_id: string;
  title: string;
  seniority?: string;
  seniority_tier?: string;
  departments: string[];
  department?: string;
  priority?: string;
  weight?: number;
}

export interface ICPExclusion {
  id?: string;
  exclusion_id: string;
  rule?: string;
  rule_name?: string;
  dimension?: string;
  field_name?: string;
  operator?: string;
  value?: any;
  hard_block?: boolean;
  rationale?: string;
}

export interface ICPVersion {
  id?: string;
  version_id: string;
  icp_id: string;
  version_number: number;
  name: string;
  status: "draft" | "active" | "archived" | "superseded" | string;
  reasoning?: string;
  change_summary?: string;
  created_at: string;
  criteria: ICPCriterion[];
  buyer_personas: ICPPersona[];
  personas?: ICPPersona[];
  exclusions: ICPExclusion[];
}

export interface ICP {
  id: string;
  name: string;
  seller_company_id: string;
  description?: string;
  status: string;
  current_version?: string;
  active_version_id?: string;
  created_at: string;
  updated_at: string;
}

export async function listICPs(seller_company_id?: string): Promise<ICP[]> {
  const query = seller_company_id ? `?seller_company_id=${seller_company_id}` : "";
  return apiFetch<ICP[]>(`/v1/icps${query}`);
}

export async function getICP(icp_id: string): Promise<ICP> {
  return apiFetch<ICP>(`/v1/icps/${icp_id}`);
}

export async function listICPVersions(icp_id: string): Promise<ICPVersion[]> {
  try {
    const versions = await apiFetch<any[]>(`/v1/icps/${icp_id}/versions`);
    return versions.map((v) => ({
      version_id: v.id || v.version_id,
      icp_id: v.icp_id || icp_id,
      version_number: v.version_number || 1,
      name: v.name || "US Mid-Market B2B SaaS ICP",
      status: v.status || "active",
      reasoning: v.reasoning || "Targeting high-growth software accounts.",
      change_summary: v.change_summary || "Initial baseline specification.",
      created_at: v.created_at || new Date().toISOString(),
      criteria: (v.criteria || []).map((c: any) => ({
        criterion_id: c.id || c.criterion_id,
        category: c.category || "firmographic",
        dimension: c.dimension || c.field_name || "attribute",
        operator: c.operator || "equals",
        target_value: c.target_value || c.value || "target",
        weight: c.weight ?? 0.8,
        is_dealbreaker: c.is_dealbreaker ?? c.mandatory ?? false,
        rationale: c.rationale || "Mandatory qualification attribute.",
      })),
      buyer_personas: (v.buyer_personas || v.personas || []).map((p: any) => ({
        persona_id: p.id || p.persona_id,
        title: p.title || "Executive",
        seniority: p.seniority || p.seniority_tier || "VP",
        departments: p.departments || (p.department ? [p.department] : ["Sales"]),
        priority: p.priority || "Tier 1",
      })),
      exclusions: (v.exclusions || []).map((e: any) => ({
        exclusion_id: e.id || e.exclusion_id,
        dimension: e.dimension || e.field_name || "attribute",
        rule: e.rule || e.rule_name || "Strict disallow rule",
        rationale: e.rationale || "Instant disqualifier.",
      })),
    }));
  } catch {
    return [];
  }
}

export const getICPVersions = listICPVersions;

export async function createICPDraft(
  icp_id: string,
  payload: Partial<ICPVersion>
): Promise<ICPVersion> {
  return apiFetch<ICPVersion>(`/v1/icps/${icp_id}/draft`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function compareICPVersions(
  icp_id: string,
  base_version_id: string,
  target_version_id: string
): Promise<any> {
  return apiFetch(
    `/v1/icps/${icp_id}/versions/compare?base_version_id=${base_version_id}&target_version_id=${target_version_id}`
  );
}

export async function activateICPVersion(
  icp_id: string,
  version_id: string | number
): Promise<ICPVersion> {
  return apiFetch<ICPVersion>(`/v1/icps/${icp_id}/activate`, {
    method: "POST",
    body: JSON.stringify({ version_id: String(version_id) }),
  });
}
