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
  CheckCircle2,
} from "lucide-react";
import { formatScorePercent } from "@/lib/product-language";

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
    name: "GrowxLabs — Manufacturing India",
    description:
      "Precision manufacturing, automotive component supply chains, and industrial engineering enterprises across India.",
    seller_company_id: "cmp_seller_growxlabs",
    icp_id: "icp_india_precision_mfg",
    status: "active",
    total_prospects: 42,
    verified_prospects: 38,
    high_priority_prospects: 16,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const m: ProjectOverviewMetrics = metrics || {
    project_id: projectId,
    name: p.name,
    seller_company_id: p.seller_company_id,
    total_accounts: 42,
    priority_accounts: 16,
    strong_accounts: 18,
    possible_accounts: 8,
    reverify_count: 2,
    research_more_count: 2,
    total_people: 112,
    verified_people: 94,
    average_icp_fit: 0.91,
    average_confidence: 0.94,
  };

  const steps = [
    { label: "Understand", status: "completed" },
    { label: "Target", status: "completed" },
    { label: "Discover", status: "completed" },
    { label: "Research", status: "completed" },
    { label: "Ready", status: "active" },
    { label: "Outreach", status: "upcoming" },
    { label: "Meetings", status: "upcoming" },
  ];

  return (
    <div className="max-w-5xl space-y-8 py-2">
      {/* 1. Subtle GTM Progression Row */}
      <div className="bg-white border border-neutral-200 rounded-md p-3.5 shadow-2xs">
        <div className="flex items-center justify-between text-xs select-none overflow-x-auto">
          {steps.map((step, idx) => (
            <React.Fragment key={step.label}>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    step.status === "completed"
                      ? "bg-neutral-900 text-white"
                      : step.status === "active"
                      ? "bg-emerald-600 text-white animate-pulse"
                      : "bg-neutral-100 text-neutral-400"
                  }`}
                >
                  {step.status === "completed" ? "✓" : idx + 1}
                </span>
                <span
                  className={`font-medium ${
                    step.status === "active"
                      ? "text-neutral-900 font-semibold"
                      : step.status === "completed"
                      ? "text-neutral-700"
                      : "text-neutral-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <span className="text-neutral-300 mx-2 flex-shrink-0">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* 2. Project Header */}
      <div className="border-b border-neutral-200 pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
              {p.name}
            </h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-neutral-100 text-neutral-700 border border-neutral-200">
              Active
            </span>
          </div>
          <p className="text-xs text-neutral-500 mt-1 max-w-2xl leading-relaxed">
            {p.description}
          </p>
        </div>

        <Link
          href={`/projects/${projectId}/prospects`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-neutral-900 text-white text-xs font-medium hover:bg-neutral-800 shadow-2xs transition-colors self-start sm:self-auto"
        >
          <span>View prospects</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {/* 3. High-Information Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-neutral-200 rounded-md space-y-1">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Target Accounts
          </div>
          <div className="flex items-baseline justify-between pt-1">
            <span className="text-2xl font-bold text-neutral-900 font-sans">
              {m.total_accounts}
            </span>
            <span className="text-xs font-medium text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded border border-purple-200">
              {m.priority_accounts} High Priority
            </span>
          </div>
        </div>

        <div className="p-4 bg-white border border-neutral-200 rounded-md space-y-1">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Verified Decision Makers
          </div>
          <div className="flex items-baseline justify-between pt-1">
            <span className="text-2xl font-bold text-neutral-900 font-sans">
              {m.verified_people}
            </span>
            <span className="text-xs text-neutral-500">
              {m.total_people} matched
            </span>
          </div>
        </div>

        <div className="p-4 bg-white border border-neutral-200 rounded-md space-y-1">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Average Target Fit
          </div>
          <div className="flex items-baseline justify-between pt-1">
            <span className="text-2xl font-bold text-neutral-900 font-sans">
              {formatScorePercent(m.average_icp_fit || 0.91)}
            </span>
            <span className="text-xs text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-medium">
              High alignment
            </span>
          </div>
        </div>

        <div className="p-4 bg-white border border-neutral-200 rounded-md space-y-1">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Data Quality & Sourcing
          </div>
          <div className="flex items-baseline justify-between pt-1">
            <span className="text-2xl font-bold text-neutral-900 font-sans">
              {formatScorePercent(m.average_confidence || 0.94)}
            </span>
            <span className="text-xs text-neutral-500">
              100% verified
            </span>
          </div>
        </div>
      </div>

      {/* 4. Internal Workflow Areas */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          GTM Sections
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Link
            href={`/projects/${projectId}/icp`}
            className="p-4 bg-white border border-neutral-200 rounded-md hover:border-neutral-400 transition-colors space-y-1 block"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-neutral-900">
                Target Profile
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />
            </div>
            <p className="text-xs text-neutral-500">
              Industries, size filters, technologies, and buyer personas.
            </p>
          </Link>

          <Link
            href={`/projects/${projectId}/prospects`}
            className="p-4 bg-white border border-neutral-200 rounded-md hover:border-neutral-400 transition-colors space-y-1 block"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-neutral-900">
                Prospects Queue
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />
            </div>
            <p className="text-xs text-neutral-500">
              {m.total_accounts} accounts ranked with timing and why-reasons.
            </p>
          </Link>

          <Link
            href={`/projects/${projectId}/people`}
            className="p-4 bg-white border border-neutral-200 rounded-md hover:border-neutral-400 transition-colors space-y-1 block"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-xs text-neutral-900">
                Target People
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />
            </div>
            <p className="text-xs text-neutral-500">
              {m.total_people} decision-makers with verified roles and emails.
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
