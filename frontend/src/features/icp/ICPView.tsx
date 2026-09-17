"use client";

import React, { useEffect, useState } from "react";
import {
  ICP,
  ICPVersion,
  getICP,
  getICPVersions,
} from "@/lib/api/icp";
import { StatusBadge } from "@/components/status/StatusBadge";
import {
  Target,
  Users,
  ShieldAlert,
  GitBranch,
  CheckCircle2,
  Building2,
  Globe,
  Briefcase,
  Zap,
  Edit,
  Cpu,
} from "lucide-react";
import { StructuredICPEditor } from "./StructuredICPEditor";
import { VersionComparison } from "./VersionComparison";

interface ICPViewProps {
  icpId?: string;
}

export function ICPView({ icpId = "icp_india_precision_mfg" }: ICPViewProps) {
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
    version_id: "ver_mfg_01",
    icp_id: icpId,
    version_number: 1,
    name: "India Precision Manufacturing Target Profile",
    status: "active",
    reasoning:
      "Targeting Tier 1 and Tier 2 precision engineering, automotive forging, and heavy machinery manufacturers with active facility expansion in India.",
    change_summary: "Initial baseline target profile.",
    created_at: new Date().toISOString(),
    criteria: [
      {
        criterion_id: "crit_01",
        category: "firmographic",
        dimension: "industry",
        operator: "in",
        target_value: "Precision Forging, Automotive Components, Industrial Machinery",
        weight: 0.9,
        is_dealbreaker: true,
        rationale: "Core manufacturing focus with high autonomous software adoption potential.",
      },
      {
        criterion_id: "crit_02",
        category: "firmographic",
        dimension: "company_size",
        operator: "between",
        target_value: "500 - 10,000+ employees",
        weight: 0.85,
        is_dealbreaker: true,
        rationale: "Requires established multi-plant operations and corporate procurement.",
      },
      {
        criterion_id: "crit_03",
        category: "geographic",
        dimension: "geography",
        operator: "in",
        target_value: "India (Pune, Chennai, NCR, Bengaluru, Ahmedabad)",
        weight: 0.8,
        is_dealbreaker: true,
        rationale: "Primary active sales territory and operating regions.",
      },
      {
        criterion_id: "crit_04",
        category: "operational",
        dimension: "operational_traits",
        operator: "contains",
        target_value: "In-house CNC machining, high-precision metallurgy, robotic lines",
        weight: 0.75,
        is_dealbreaker: false,
        rationale: "Indicates capital investment in smart factory modernization.",
      },
      {
        criterion_id: "crit_05",
        category: "technographic",
        dimension: "technology",
        operator: "in",
        target_value: "SAP ERP, Siemens PLM, Oracle Enterprise",
        weight: 0.7,
        is_dealbreaker: false,
        rationale: "Ensures established modern digital infrastructure.",
      },
      {
        criterion_id: "crit_06",
        category: "timing_signal",
        dimension: "signals",
        operator: "contains",
        target_value: "Facility expansion, plant director hiring, ESG modernization",
        weight: 0.8,
        is_dealbreaker: false,
        rationale: "High-intent operational triggers in the last 6 months.",
      },
    ],
    buyer_personas: [
      {
        persona_id: "per_01",
        title: "Head of Operations / Plant Operations VP",
        seniority: "VP+",
        departments: ["Operations", "Manufacturing"],
        priority: "Key Decision Maker",
      },
      {
        persona_id: "per_02",
        title: "Director of Digital Transformation / Smart Factory",
        seniority: "Director",
        departments: ["IT", "Innovation"],
        priority: "Executive Champion",
      },
      {
        persona_id: "per_03",
        title: "VP Supply Chain & Procurement",
        seniority: "VP",
        departments: ["Procurement", "Supply Chain"],
        priority: "Commercial Evaluator",
      },
    ],
    exclusions: [
      {
        exclusion_id: "ex_01",
        dimension: "business_model",
        rule: "Pure consumer goods packaging or trading companies",
        rationale: "Must have physical manufacturing plants and industrial equipment.",
      },
      {
        exclusion_id: "ex_02",
        dimension: "company_size",
        rule: "Under 100 employees (Small job shops)",
        rationale: "Insufficient budget for enterprise software deployment.",
      },
    ],
  };

  const v = activeVersion || defaultVersion;

  return (
    <div className="max-w-4xl space-y-8 py-2">
      {/* Page Header */}
      <div className="border-b border-neutral-200 pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
              Target Profile
            </h1>
            <span className="text-xs px-2 py-0.5 rounded bg-neutral-100 text-neutral-700 font-medium">
              v{v.version_number}.0 Active
            </span>
          </div>
          <p className="text-xs text-neutral-500 mt-1 max-w-2xl leading-relaxed">
            {v.reasoning}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap self-start sm:self-auto">
          <button
            onClick={() => setViewMode(viewMode === "compare" ? "view" : "compare")}
            className={`px-3 py-1.5 rounded-md border text-xs font-medium transition-colors ${
              viewMode === "compare"
                ? "bg-neutral-900 text-white border-neutral-900"
                : "bg-white border-neutral-300 text-neutral-700 hover:bg-neutral-50"
            }`}
          >
            {viewMode === "compare" ? "Close comparison" : "Compare versions"}
          </button>

          <button
            onClick={() => setViewMode(viewMode === "edit" ? "view" : "edit")}
            className="px-3 py-1.5 rounded-md bg-neutral-900 text-white hover:bg-neutral-800 text-xs font-medium shadow-2xs transition-colors"
          >
            {viewMode === "edit" ? "Cancel edit" : "Edit target profile"}
          </button>
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

      {/* Main View: Structured Controls matching Section 22 */}
      {viewMode === "view" && (
        <div className="space-y-8">
          {/* Section 1: Industries & Company Size */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-2">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-neutral-500" />
                <span>Industries</span>
              </div>
              <div className="text-sm font-semibold text-neutral-900">
                Precision Forging & Industrial Manufacturing
              </div>
              <div className="text-xs text-neutral-500">
                Automotive tier-1 suppliers, heavy equipment fabrication, precision metallurgy.
              </div>
            </div>

            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-2">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-neutral-500" />
                <span>Company Size</span>
              </div>
              <div className="text-sm font-semibold text-neutral-900">
                500 to 10,000+ employees
              </div>
              <div className="text-xs text-neutral-500">
                Multi-facility operations with dedicated industrial plant infrastructure.
              </div>
            </div>
          </div>

          {/* Section 2: Geography & Operational Traits */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-2">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-neutral-500" />
                <span>Geography</span>
              </div>
              <div className="text-sm font-semibold text-neutral-900">
                India & Regional Export Hubs
              </div>
              <div className="text-xs text-neutral-500">
                Key industrial corridors in Pune, Chennai, NCR, Bengaluru, and Gujarat.
              </div>
            </div>

            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-2">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-neutral-500" />
                <span>Operational Traits</span>
              </div>
              <div className="text-sm font-semibold text-neutral-900">
                Modern Automated Tooling
              </div>
              <div className="text-xs text-neutral-500">
                In-house CNC machinery, ISO quality certifications, high-volume production lines.
              </div>
            </div>
          </div>

          {/* Section 3: Technology & Signals */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-2">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Target className="w-3.5 h-3.5 text-neutral-500" />
                <span>Technology</span>
              </div>
              <div className="text-sm font-semibold text-neutral-900">
                Enterprise Core Stack
              </div>
              <div className="text-xs text-neutral-500">
                SAP ERP, Siemens PLM, Salesforce CRM, and automated industrial control systems.
              </div>
            </div>

            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-2">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-neutral-500" />
                <span>Signals</span>
              </div>
              <div className="text-sm font-semibold text-neutral-900">
                Expansion & Leadership Triggers
              </div>
              <div className="text-xs text-neutral-500">
                Announced facility expansions, smart factory hires, and equipment modernization.
              </div>
            </div>
          </div>

          {/* Section 4: Buyer Roles & Exclusions */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Buyer roles */}
            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
              <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-neutral-500" />
                <span>Buyer Roles</span>
              </div>
              <div className="space-y-2">
                {v.buyer_personas.map((bp) => (
                  <div
                    key={bp.persona_id}
                    className="p-2.5 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-semibold text-neutral-900">{bp.title}</div>
                      <div className="text-[11px] text-neutral-500">{bp.departments.join(", ")}</div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 bg-neutral-200 text-neutral-800 rounded font-medium">
                      {bp.priority}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Exclusions */}
            <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
              <div className="text-[11px] font-semibold text-rose-700 uppercase tracking-wider flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                <span>Exclusions</span>
              </div>
              <div className="space-y-2">
                {v.exclusions.map((ex) => (
                  <div
                    key={ex.exclusion_id}
                    className="p-2.5 bg-rose-50/50 rounded border border-rose-200 text-xs space-y-0.5"
                  >
                    <div className="font-semibold text-rose-950">{ex.rule}</div>
                    <div className="text-[11px] text-neutral-600">{ex.rationale}</div>
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
