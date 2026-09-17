"use client";

import React, { useEffect, useState } from "react";
import {
  ICP,
  ICPVersion,
  getICP,
  getICPVersions,
  activateICPVersion,
} from "@/lib/api/icp";
import { StatusBadge } from "@/components/status/StatusBadge";
import {
  Target,
  Users,
  ShieldAlert,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  ArrowUpDown,
  History,
  Edit,
  Plus,
} from "lucide-react";
import { StructuredICPEditor } from "./StructuredICPEditor";
import { VersionComparison } from "./VersionComparison";

interface ICPViewProps {
  icpId?: string;
}

export function ICPView({ icpId = "icp_us_midmarket_saas" }: ICPViewProps) {
  const [icp, setIcp] = useState<ICP | null>(null);
  const [activeVersion, setActiveVersion] = useState<ICPVersion | null>(null);
  const [allVersions, setAllVersions] = useState<ICPVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"view" | "edit" | "compare">("view");

  const loadData = () => {
    setLoading(true);
    getICP(icpId)
      .then((data) => {
        setIcp(data);
      })
      .catch((err) => console.error(err));

    getICPVersions(icpId)
      .then((versions) => {
        setAllVersions(versions);
        const active =
          versions.find((v) => v.status === "active") || versions[0];
        setActiveVersion(active);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [icpId]);

  const defaultVersion: ICPVersion = {
    version_id: "ver_001",
    icp_id: icpId,
    version_number: 1,
    name: "US Mid-Market B2B SaaS ICP",
    status: "active",
    reasoning:
      "Targeting post-Series A through C enterprise B2B SaaS organizations with outbound SDR/BDR teams requiring canonical fact-verified prospect intelligence.",
    change_summary: "Initial baseline ICP specification.",
    created_at: new Date().toISOString(),
    criteria: [
      {
        criterion_id: "crit_01",
        category: "firmographic",
        dimension: "employee_count",
        operator: "between",
        target_value: "50 - 1000",
        weight: 0.85,
        is_dealbreaker: true,
        rationale: "Must have dedicated sales engineering or outbound reps.",
      },
      {
        criterion_id: "crit_02",
        category: "geographic",
        dimension: "country",
        operator: "in",
        target_value: "United States, Canada",
        weight: 0.8,
        is_dealbreaker: true,
        rationale: "Core seller market coverage and timezone alignment.",
      },
      {
        criterion_id: "crit_03",
        category: "technographic",
        dimension: "crm_platform",
        operator: "in",
        target_value: "Salesforce, HubSpot",
        weight: 0.75,
        is_dealbreaker: false,
        rationale: "Ensures seamless integration for outbound workflow sync.",
      },
      {
        criterion_id: "crit_04",
        category: "firmographic",
        dimension: "industry",
        operator: "equals",
        target_value: "Software / Enterprise SaaS / Cloud",
        weight: 0.9,
        is_dealbreaker: true,
        rationale: "Primary target industry with maximum product-market fit.",
      },
      {
        criterion_id: "crit_05",
        category: "timing_signal",
        dimension: "hiring_sales_roles",
        operator: "greater_than",
        target_value: "2 active SDR/AE postings",
        weight: 0.7,
        is_dealbreaker: false,
        rationale: "Signal of active outbound team expansion and tooling demand.",
      },
    ],
    buyer_personas: [
      {
        persona_id: "per_01",
        title: "VP of Sales / VP Revenue Operations",
        seniority: "VP",
        departments: ["Sales", "RevOps"],
        priority: "Tier 1 (Decision Maker)",
      },
      {
        persona_id: "per_02",
        title: "Director of Demand Generation",
        seniority: "Director",
        departments: ["Marketing", "Growth"],
        priority: "Tier 2 (Champion)",
      },
      {
        persona_id: "per_03",
        title: "Sales Operations Manager",
        seniority: "Manager",
        departments: ["Sales Ops"],
        priority: "Tier 2 (Evaluator)",
      },
    ],
    exclusions: [
      {
        exclusion_id: "ex_01",
        dimension: "business_model",
        rule: "B2C only or physical goods marketplace",
        rationale: "Zero value proposition for non-B2B enterprise sellers.",
      },
      {
        exclusion_id: "ex_02",
        dimension: "employee_count",
        rule: "Under 15 employees (Seed / Pre-seed)",
        rationale: "Lacks budget and established outbound reps.",
      },
    ],
  };

  const v = activeVersion || defaultVersion;

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-neutral-800" />
              <h1 className="text-base font-bold text-neutral-900">
                {v.name}
              </h1>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-neutral-900 text-white font-semibold">
                v{v.version_number}.0
              </span>
              <StatusBadge status={v.status} size="sm" />
            </div>
            <p className="text-xs text-neutral-500 mt-1 max-w-2xl leading-relaxed">
              {v.reasoning}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setViewMode(viewMode === "compare" ? "view" : "compare")}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded border text-xs font-medium transition-colors ${
                viewMode === "compare"
                  ? "bg-neutral-900 text-white border-neutral-900"
                  : "bg-white border-neutral-300 text-neutral-700 hover:bg-neutral-100"
              }`}
            >
              <GitBranch className="w-3.5 h-3.5" />
              <span>{viewMode === "compare" ? "Close Comparison" : "Compare Versions"}</span>
            </button>

            <button
              onClick={() => setViewMode(viewMode === "edit" ? "view" : "edit")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-neutral-900 text-white hover:bg-neutral-800 text-xs font-medium shadow-2xs transition-colors"
            >
              <Edit className="w-3.5 h-3.5" />
              <span>{viewMode === "edit" ? "Cancel Edit" : "Create New Version Draft"}</span>
            </button>
          </div>
        </div>

        {/* Quick Stats Banner */}
        <div className="mt-4 pt-4 border-t border-neutral-100 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Criteria Total</span>
            <span className="font-bold text-neutral-900 text-sm">{v.criteria.length}</span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Dealbreakers</span>
            <span className="font-bold text-rose-600 text-sm">
              {v.criteria.filter((c) => c.is_dealbreaker).length} Mandatory
            </span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Buyer Personas</span>
            <span className="font-bold text-neutral-900 text-sm">{v.buyer_personas.length}</span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Negative Exclusions</span>
            <span className="font-bold text-neutral-700 text-sm">{v.exclusions.length} Rules</span>
          </div>
        </div>
      </div>

      {/* Subviews */}
      {viewMode === "edit" && (
        <StructuredICPEditor
          icpId={icpId}
          initialData={v}
          onSaved={() => {
            setViewMode("view");
            loadData();
          }}
          onCancel={() => setViewMode("view")}
        />
      )}

      {viewMode === "compare" && (
        <VersionComparison
          icpId={icpId}
          versions={allVersions.length > 0 ? allVersions : [defaultVersion]}
          onActivated={() => {
            loadData();
          }}
        />
      )}

      {/* Primary Detail View */}
      {viewMode === "view" && (
        <div className="space-y-6">
          {/* Target Criteria Table */}
          <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
                Evaluation Criteria & Scoring Weights
              </h2>
              <span className="text-[11px] font-mono text-neutral-400">
                Weights aggregate to prospect fit score
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-neutral-50 text-[11px] uppercase font-mono text-neutral-500 border-b border-neutral-200">
                  <tr>
                    <th className="px-3 py-2">Category</th>
                    <th className="px-3 py-2">Dimension</th>
                    <th className="px-3 py-2">Rule / Condition</th>
                    <th className="px-3 py-2">Target Value</th>
                    <th className="px-3 py-2">Scoring Weight</th>
                    <th className="px-3 py-2">Mandatory?</th>
                    <th className="px-3 py-2">Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  {v.criteria.map((c) => (
                    <tr key={c.criterion_id} className="hover:bg-neutral-50/50">
                      <td className="px-3 py-2.5 font-mono text-[11px] text-neutral-600">
                        {c.category}
                      </td>
                      <td className="px-3 py-2.5 font-semibold text-neutral-900">
                        {c.dimension}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-[11px] text-neutral-500">
                        {c.operator}
                      </td>
                      <td className="px-3 py-2.5 font-mono font-medium text-neutral-800">
                        {c.target_value}
                      </td>
                      <td className="px-3 py-2.5 font-mono font-bold text-neutral-900">
                        {Math.round(c.weight * 100)}%
                      </td>
                      <td className="px-3 py-2.5">
                        {c.is_dealbreaker ? (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                            Dealbreaker
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-neutral-100 text-neutral-600">
                            Flexible
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 text-neutral-500 max-w-xs truncate">
                        {c.rationale}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Buyer Personas & Negative Exclusions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Buyer Personas */}
            <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-neutral-800" />
                <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
                  Target Buyer Personas
                </h2>
              </div>

              <div className="space-y-3">
                {v.buyer_personas.map((bp) => (
                  <div
                    key={bp.persona_id}
                    className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-neutral-900">
                        {bp.title}
                      </div>
                      <div className="text-[11px] text-neutral-500 mt-0.5">
                        Departments: {bp.departments.join(", ")}
                      </div>
                    </div>
                    <span className="font-mono text-[10px] px-2 py-0.5 bg-neutral-200 text-neutral-800 rounded font-medium">
                      {bp.priority}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Negative Exclusions */}
            <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
              <div className="flex items-center gap-2 text-rose-700">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
                  Strict Exclusions & Disqualifiers
                </h2>
              </div>

              <div className="space-y-3">
                {v.exclusions.map((ex) => (
                  <div
                    key={ex.exclusion_id}
                    className="p-3 bg-rose-50/40 rounded border border-rose-200/80 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-rose-900 font-mono text-[11px]">
                        {ex.dimension}
                      </span>
                      <span className="text-[10px] text-rose-600 font-semibold uppercase">
                        Instant Drop
                      </span>
                    </div>
                    <div className="text-rose-950 font-medium">
                      Rule: {ex.rule}
                    </div>
                    <div className="text-neutral-500 text-[11px]">
                      {ex.rationale}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
