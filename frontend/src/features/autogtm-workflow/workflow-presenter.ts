export type WorkflowStageState =
  | "pending"
  | "running"
  | "completed"
  | "attention"
  | "failed";

export type WorkflowStageKey =
  | "company_research"
  | "competitors"
  | "campaigns"
  | "companies"
  | "people"
  | "emails";

export interface WorkflowPreviewItem {
  id: string;
  label: string;
  secondary?: string;
  selected?: boolean;
}

export interface AutoGTMWorkflowStageView {
  order: number;
  key: WorkflowStageKey;
  title: string;
  state: WorkflowStageState;
  summary?: string;
  count?: number;
  progressText?: string;
  items?: WorkflowPreviewItem[];
}

export interface AutoGTMWorkflowView {
  projectId: string;
  company: {
    name: string;
    domain: string;
  };
  currentStageOrder: number;
  stages: AutoGTMWorkflowStageView[];
}

interface BuildWorkflowStagesParams {
  company: {
    name: string;
    domain: string;
  };
  competitorsCount: number;
  campaignsCount: number;
  activeCampaignName: string;
  activeCampaignCountLabel: string;
  totalAudienceLabel: string;
  companiesCount: number;
  peopleCount: number;
  emailsCount: number;
  activeStageOrder?: number;
}

export function buildWorkflowPresentation(
  params: BuildWorkflowStagesParams
): AutoGTMWorkflowView {
  const currentStageOrder = params.activeStageOrder ?? 3;

  const stages: AutoGTMWorkflowStageView[] = [
    {
      order: 1,
      key: "company_research",
      title: "Research your company",
      state: "completed",
      summary: `${params.company.name} · ${params.company.domain}`,
    },
    {
      order: 2,
      key: "competitors",
      title: "Explore competitors",
      state: "completed",
      summary: `${params.competitorsCount} competitors found`,
      count: params.competitorsCount,
    },
    {
      order: 3,
      key: "campaigns",
      title: "Define campaigns",
      state: "completed",
      summary: `${params.campaignsCount} campaigns · ${params.totalAudienceLabel} companies`,
      count: params.campaignsCount,
    },
    {
      order: 4,
      key: "companies",
      title: "Find potential customers",
      state: "completed",
      summary: `${params.companiesCount.toLocaleString()} companies found`,
      count: params.companiesCount,
    },
    {
      order: 5,
      key: "decision_makers" as any,
      title: "Find decision makers",
      state: "completed",
      summary: `${params.peopleCount.toLocaleString()} people found`,
      count: params.peopleCount,
    },
    {
      order: 6,
      key: "emails",
      title: "Write emails",
      state: "completed",
      summary: `${params.emailsCount.toLocaleString()} emails prepared`,
      count: params.emailsCount,
    },
  ];

  return {
    projectId: "prj_active",
    company: params.company,
    currentStageOrder,
    stages,
  };
}
