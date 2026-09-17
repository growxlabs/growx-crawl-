"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Project,
  ProjectOverviewMetrics,
  getProject,
  getProjectOverview,
} from "@/lib/api/projects";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import {
  FolderGit2,
  Users,
  Target,
  Flame,
  ShieldCheck,
  Search,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  Layers,
  Sparkles,
} from "lucide-react";

interface ProjectOverviewProps {
  projectId: string;
}

export function ProjectOverview({ projectId }: ProjectOverviewProps) {
  const [project, setProject] = useState<Project | null>(null);
  const [metrics, setMetrics] = useState<ProjectOverviewMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getProject(projectId).catch(() => null),
      getProjectOverview(projectId).catch(() => null),
    ])
      .then(([projData, metricsData]) => {
        if (projData) setProject(projData);
        if (metricsData) setMetrics(metricsData);
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  const p = project || {
    id: projectId,
    name: "US Mid-Market SaaS Expansion",
    description:
      "Targeting high-growth US B2B software companies between 50-1000 employees with active outbound SDR hiring and Salesforce/HubSpot CRMs.",
    seller_company_id: "cmp_seller_growxlabs",
    icp_id: "icp_us_midmarket_saas",
    status: "active",
    total_prospects: 48,
    verified_prospects: 42,
    high_priority_prospects: 14,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const m: ProjectOverviewMetrics = metrics || {
    project_id: projectId,
    name: p.name,
    seller_company_id: p.seller_company_id,
    total_accounts: 48,
    priority_accounts: 14,
    strong_accounts: 18,
    possible_accounts: 10,
    reverify_count: 3,
    research_more_count: 3,
    total_people: 124,
    verified_people: 96,
    average_icp_fit: 0.84,
    average_confidence: 0.91,
  };

  return (
    <div className="space-y-6">
      {/* Project Banner Card */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <FolderGit2 className="w-4 h-4 text-neutral-800" />
              <h1 className="text-base font-bold text-neutral-900">{p.name}</h1>
              <StatusBadge status={p.status} size="sm" />
            </div>
            <p className="text-xs text-neutral-500 mt-1 max-w-2xl leading-relaxed">
              {p.description}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/projects/${projectId}/prospects`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 shadow-2xs transition-colors"
            >
              <span>View Prospect Queue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Linked Entities Sub-row */}
        <div className="mt-4 pt-4 border-t border-neutral-100 flex flex-wrap items-center gap-4 text-xs font-mono text-neutral-500">
          <div>
            <span className="text-neutral-400">Seller Entity:</span>{" "}
            <Link
              href="/company/overview"
              className="text-neutral-900 underline font-semibold"
            >
              GrowxLabs Intelligence
            </Link>
          </div>
          <span>•</span>
          <div>
            <span className="text-neutral-400">Attached ICP:</span>{" "}
            <Link
              href={`/projects/${projectId}/icp`}
              className="text-neutral-900 underline font-semibold"
            >
              US Mid-Market B2B SaaS ICP (v1.0)
            </Link>
          </div>
          <span>•</span>
          <div>
            <span className="text-neutral-400">Project ID:</span>{" "}
            <span className="text-neutral-700">{p.id}</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[10px] font-mono text-neutral-400 uppercase">
            Total Target Accounts
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-neutral-900">
              {m.total_accounts}
            </span>
            <span className="text-xs font-mono text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200">
              {m.priority_accounts} Priority
            </span>
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[10px] font-mono text-neutral-400 uppercase">
            Verified Contacts
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-2xl font-bold font-mono text-neutral-900">
              {m.verified_people}
            </span>
            <span className="text-xs font-mono text-neutral-500">
              / {m.total_people} Total
            </span>
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[10px] font-mono text-neutral-400 uppercase">
            Average ICP Fit
          </div>
          <div className="mt-2">
            <ConfidenceIndicator score={m.average_icp_fit} size="md" />
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[10px] font-mono text-neutral-400 uppercase">
            Average Fact Confidence
          </div>
          <div className="mt-2">
            <ConfidenceIndicator score={m.average_confidence} size="md" />
          </div>
        </div>
      </div>

      {/* Rank Tier Distribution Bar */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
            Prospect Priority Segmentation
          </h2>
          <span className="text-[11px] font-mono text-neutral-400">
            Deterministic AutoGTM scoring tiers
          </span>
        </div>

        {/* Stacked Bar */}
        <div className="h-3 w-full bg-neutral-100 rounded-full overflow-hidden flex">
          <div
            style={{ width: `${(m.priority_accounts / m.total_accounts) * 100}%` }}
            className="bg-purple-600 h-full"
            title={`Priority: ${m.priority_accounts}`}
          />
          <div
            style={{ width: `${(m.strong_accounts / m.total_accounts) * 100}%` }}
            className="bg-blue-600 h-full"
            title={`Strong: ${m.strong_accounts}`}
          />
          <div
            style={{ width: `${(m.possible_accounts / m.total_accounts) * 100}%` }}
            className="bg-neutral-400 h-full"
            title={`Possible: ${m.possible_accounts}`}
          />
          <div
            style={{ width: `${(m.research_more_count / m.total_accounts) * 100}%` }}
            className="bg-amber-500 h-full"
            title={`Research More: ${m.research_more_count}`}
          />
          <div
            style={{ width: `${(m.reverify_count / m.total_accounts) * 100}%` }}
            className="bg-rose-500 h-full"
            title={`Reverify: ${m.reverify_count}`}
          />
        </div>

        {/* Tier Legend */}
        <div className="flex flex-wrap items-center gap-4 pt-2 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-purple-600" />
            <span className="text-neutral-700">Priority ({m.priority_accounts})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-blue-600" />
            <span className="text-neutral-700">Strong ({m.strong_accounts})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-neutral-400" />
            <span className="text-neutral-700">Possible ({m.possible_accounts})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-amber-500" />
            <span className="text-neutral-700">Research More ({m.research_more_count})</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-sm bg-rose-500" />
            <span className="text-neutral-700">Reverify ({m.reverify_count})</span>
          </div>
        </div>
      </div>

      {/* Sub-navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href={`/projects/${projectId}/prospects`}
          className="p-4 bg-white border border-neutral-200 rounded hover:border-neutral-400 transition-colors space-y-1 block"
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-xs text-neutral-900">
              Ranked Account Queue
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />
          </div>
          <p className="text-xs text-neutral-500">
            Interactive scorecard table with why-reasons and fact inspection.
          </p>
        </Link>

        <Link
          href={`/projects/${projectId}/people`}
          className="p-4 bg-white border border-neutral-200 rounded hover:border-neutral-400 transition-colors space-y-1 block"
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-xs text-neutral-900">
              Target Buyer Contacts
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />
          </div>
          <p className="text-xs text-neutral-500">
            {m.total_people} personas matched across target companies.
          </p>
        </Link>

        <Link
          href={`/projects/${projectId}/activity`}
          className="p-4 bg-white border border-neutral-200 rounded hover:border-neutral-400 transition-colors space-y-1 block"
        >
          <div className="flex items-center justify-between">
            <span className="font-semibold text-xs text-neutral-900">
              Activity & Job Log
            </span>
            <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />
          </div>
          <p className="text-xs text-neutral-500">
            Audit trail of scoring runs, crawler jobs, and human overrides.
          </p>
        </Link>
      </div>
    </div>
  );
}
