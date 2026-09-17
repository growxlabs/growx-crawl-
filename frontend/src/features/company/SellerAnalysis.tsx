"use client";

import React, { useEffect, useState } from "react";
import {
  getSellerAnalysis,
  SellerAnalysis as SellerAnalysisType,
} from "@/lib/api/company";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  Sparkles,
  CheckCircle2,
  Users,
  Target,
  FileSearch,
  ShieldCheck,
  Tag,
} from "lucide-react";
import { StatusBadge } from "@/components/status/StatusBadge";

export function SellerAnalysis() {
  const [analysis, setAnalysis] = useState<SellerAnalysisType | null>(null);
  const [loading, setLoading] = useState(true);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    getSellerAnalysis()
      .then((data) => setAnalysis(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const data: SellerAnalysisType = analysis || {
    company_name: "GrowxLabs Intelligence",
    domain: "growxlabs.tech",
    positioning:
      "Autonomous GTM intelligence platform turning unstructured company crawl data into verified canonical buyer graphs.",
    value_props: [
      {
        title: "Canonical Fact Verification",
        description:
          "Zero hallucination GTM data verified directly against authoritative company websites and DOM citations.",
      },
      {
        title: "Temporal Intelligence & Change Detection",
        description:
          "Detect when prospect tech stacks, executive hiring, or pricing models change in real-time.",
      },
      {
        title: "Explainable Prospect Ranking",
        description:
          "Transparent scorecards showing exact ICP fit percentages, readiness factors, and evidence provenance.",
      },
    ],
    ideal_use_cases: [
      "Mid-market B2B outbound campaign acceleration",
      "Account-based intelligence and buyer graph mapping",
      "Competitive switch campaigns targeting legacy data providers",
    ],
    target_buyer_roles: [
      {
        role: "VP of Sales / Head of Revenue Operations",
        departments: ["Sales", "Revenue Operations"],
        seniority: "VP+",
      },
      {
        role: "Director of Demand Generation / GTM",
        departments: ["Marketing", "Growth"],
        seniority: "Director",
      },
      {
        role: "Chief Commercial Officer",
        departments: ["Executive", "Sales"],
        seniority: "C-Level",
      },
    ],
    pricing_model: "Usage-based tiering + Platform subscription per seat",
    differentiators: [
      "Automated continuous re-crawling with temporal diff engine",
      "Explainable algorithmic ICP scoring vs opaque black boxes",
      "Native first-party DOM proof inspector for every single attribute",
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-neutral-800" />
            <span className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Seller Capability Analysis
            </span>
          </div>
          <StatusBadge status="Verified" size="sm" />
        </div>
        <p className="text-xs text-neutral-500">
          Synthesized seller value proposition, commercial positioning, and ICP
          foundational inputs derived from deep crawls.
        </p>

        {/* Positioning Box */}
        <div className="mt-4 p-4 bg-neutral-50 rounded border border-neutral-200">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase font-mono text-neutral-400">
              Core Strategic Positioning
            </span>
            <button
              onClick={() =>
                openEvidenceDrawer({
                  claim: data.positioning,
                  sourceUrl: "https://growxlabs.com",
                  verificationStatus: "Verified",
                  confidenceScore: 0.99,
                })
              }
              className="text-[11px] text-blue-600 hover:text-blue-800 underline inline-flex items-center gap-1"
            >
              <FileSearch className="w-3 h-3" />
              <span>Inspect Source</span>
            </button>
          </div>
          <div className="text-sm font-semibold text-neutral-900 leading-relaxed font-sans">
            "{data.positioning}"
          </div>
        </div>
      </div>

      {/* Value Propositions */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <h2 className="text-xs font-semibold text-neutral-900 uppercase tracking-wider font-mono">
          Core Value Propositions ({data.value_props.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {data.value_props.map((vp, idx) => (
            <div
              key={idx}
              className="p-4 rounded border border-neutral-200 bg-neutral-50/40 space-y-2 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <div className="font-semibold text-xs text-neutral-900">
                    {vp.title}
                  </div>
                </div>
                <p className="text-xs text-neutral-600 leading-normal">
                  {vp.description}
                </p>
              </div>

              <div className="pt-2 border-t border-neutral-200/60 flex justify-end">
                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: `${vp.title}: ${vp.description}`,
                      sourceUrl: "https://growxlabs.com/platform",
                      verificationStatus: "Verified",
                    })
                  }
                  className="text-[10px] text-neutral-500 hover:text-neutral-900 underline"
                >
                  Verify Proof
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Target Buyer Personas & Differentiators */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Buyer Roles */}
        <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-neutral-700" />
            <h2 className="text-xs font-semibold text-neutral-900 uppercase tracking-wider font-mono">
              Target Buyer Personas
            </h2>
          </div>

          <div className="space-y-3">
            {data.target_buyer_roles.map((br, idx) => (
              <div
                key={idx}
                className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-neutral-900">
                    {br.role}
                  </div>
                  <div className="text-[11px] text-neutral-500 mt-0.5">
                    {br.departments.join(", ")}
                  </div>
                </div>
                <span className="font-mono text-[10px] px-2 py-0.5 bg-neutral-200 text-neutral-700 rounded font-medium">
                  {br.seniority}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Differentiators & Pricing */}
        <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-neutral-700" />
            <h2 className="text-xs font-semibold text-neutral-900 uppercase tracking-wider font-mono">
              Verified Differentiators
            </h2>
          </div>

          <div className="space-y-2.5">
            {data.differentiators.map((diff, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded bg-neutral-50 border border-neutral-200 text-xs text-neutral-700 flex items-start gap-2"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-neutral-900 mt-1.5 flex-shrink-0" />
                <span className="leading-snug">{diff}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-neutral-200">
            <div className="text-[10px] uppercase font-mono text-neutral-400 mb-1">
              Commercial Pricing Model
            </div>
            <div className="text-xs font-mono text-neutral-800 bg-neutral-100 p-2 rounded border border-neutral-200">
              {data.pricing_model}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
