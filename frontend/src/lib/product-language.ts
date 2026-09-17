/**
 * GrowX AutoGTM — Product Language Registry
 * Translates backend schemas, canonical entities, predicates, and worker tasks
 * into calm, human, outcome-oriented GTM product language.
 */

export const PRODUCT_TERMS: Record<string, string> = {
  canonical_company: "Company",
  canonical_person: "Person",
  fact: "Information",
  predicate: "Field",
  observation: "Source finding",
  evidence: "Source",
  verification_run: "Verification",
  quality_gate: "Readiness",
  icp_specification: "Target profile",
  prospect_ranking: "Priority",
  signal_candidate: "Signal",
  temporal_intelligence: "Changes",
  campaign_execution: "Campaign",
  message_intent: "Email draft",
  employee_count_range: "Company size",
  competitor_graph: "Competitors",
  employment_state: "Current role",
};

/**
 * Maps internal rank tiers to human priority labels and visual variants
 */
export function formatPriority(rankTier: string = ""): {
  label: string;
  variant: "high" | "strong" | "potential" | "warning" | "neutral";
} {
  const norm = rankTier.toLowerCase().trim().replace(/_/g, " ");
  if (norm.includes("priority") || norm === "high") {
    return { label: "High", variant: "high" };
  }
  if (norm.includes("strong")) {
    return { label: "Strong", variant: "strong" };
  }
  if (norm.includes("possible") || norm.includes("potential")) {
    return { label: "Potential", variant: "potential" };
  }
  if (norm.includes("research")) {
    return { label: "Needs research", variant: "warning" };
  }
  if (norm.includes("reverify") || norm.includes("refresh") || norm.includes("sync")) {
    return { label: "Needs refresh", variant: "warning" };
  }
  return { label: "Potential", variant: "neutral" };
}

/**
 * Maps verification and quality states into human readiness labels
 */
export function formatReadiness(status: string = "", requiresReverify = false): {
  label: string;
  variant: "verified" | "supported" | "refresh" | "uncertain" | "blocked";
} {
  if (requiresReverify) {
    return { label: "Needs refresh", variant: "refresh" };
  }
  const s = status.toLowerCase().trim();
  if (s === "verified" || s === "passed") {
    return { label: "Verified", variant: "verified" };
  }
  if (s === "supported" || s === "high_confidence") {
    return { label: "Supported", variant: "supported" };
  }
  if (s.includes("reverify") || s.includes("sync") || s.includes("refresh")) {
    return { label: "Needs refresh", variant: "refresh" };
  }
  if (s === "blocked" || s === "failed" || s === "dealbreaker") {
    return { label: "Blocked", variant: "blocked" };
  }
  return { label: "Needs research", variant: "uncertain" };
}

/**
 * Maps internal predicate names to human field titles
 */
export function formatPredicate(predicate: string = ""): string {
  const known: Record<string, string> = {
    employee_count_range: "Company size",
    employee_count: "Employee headcount",
    competitor_graph: "Competitors",
    icp_specification: "Target customer profile",
    headquarters: "Headquarters",
    industry: "Industry",
    summary: "Company overview",
    pricing_tier: "Pricing model",
    pricing_model: "Pricing model",
    employment_state: "Current role",
    hiring_sales_roles: "Active sales hiring",
    crm_platform: "CRM deployment",
    tech_stack: "Technologies",
    revenue_range: "Annual revenue",
  };

  if (known[predicate]) return known[predicate];

  return predicate
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

/**
 * Formats decimal score into clean percentage string
 */
export function formatScorePercent(score: number): string {
  if (score === undefined || score === null) return "0%";
  return `${Math.round(score * 100)}%`;
}

/**
 * Formats confidence score into product-friendly confidence label
 */
export function formatConfidenceLabel(score: number): string {
  if (score >= 0.9) return "Verified";
  if (score >= 0.75) return "Supported";
  if (score >= 0.5) return "Needs research";
  return "Uncertain";
}

/**
 * Converts background job types into human product activity summaries
 */
export function formatActivityMessage(jobType: string, count?: number): string {
  const t = jobType.toLowerCase();
  if (t.includes("crawler") || t.includes("crawl")) {
    return count ? `Researching ${count} companies` : "Researching companies";
  }
  if (t.includes("browser") || t.includes("render")) {
    return count ? `Verifying ${count} company websites` : "Verifying company websites";
  }
  if (t.includes("intelligence") || t.includes("seller")) {
    return count ? `Analyzing ${count} accounts` : "Analyzing company accounts";
  }
  if (t.includes("verification") || t.includes("person") || t.includes("contact")) {
    return count ? `Verifying ${count} contacts` : "Verifying contacts & decision-makers";
  }
  if (t.includes("nightly")) {
    return count ? `Refreshing ${count} target accounts` : "Refreshing target accounts";
  }
  return count ? `Updating ${count} records` : "Updating records";
}
