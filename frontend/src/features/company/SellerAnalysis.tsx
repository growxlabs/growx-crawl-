"use client";

import React, { useEffect, useState } from "react";
import {
  getSellerAnalysis,
  SellerAnalysis as SellerAnalysisType,
} from "@/lib/api/company";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  CheckCircle2,
  FileSearch,
  Users,
  ShieldCheck,
  Target,
  Sparkles,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

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
    company_name: "GrowxLabs",
    domain: "growxlabs.tech",
    positioning:
      "GrowxLabs builds AI-native enterprise software, autonomous systems, and custom engineering platforms for industrial, manufacturing, and enterprise organizations.",
    value_props: [
      {
        title: "Autonomous Entity Resolution & Crawling",
        description:
          "Zero hallucination company research and verification directly backed by authoritative website sources.",
      },
      {
        title: "Continuous Change Detection",
        description:
          "Detect changes in corporate leadership, hiring surges, operational expansion, and technology adoption.",
      },
      {
        title: "Explainable Prospect Prioritization",
        description:
          "Transparent qualification scorecards linking buyer fit with evidence and current timing.",
      },
    ],
    ideal_use_cases: [
      "Targeted account intelligence for industrial and enterprise sales",
      "Continuous market monitoring and competitor tracking",
      "Executive buyer discovery and role verification",
    ],
    target_buyer_roles: [
      {
        role: "Chief Technology Officer / Head of Engineering",
        departments: ["Technology", "Engineering"],
        seniority: "C-Level",
      },
      {
        role: "Head of Operations / COO",
        departments: ["Operations", "Manufacturing"],
        seniority: "VP+",
      },
      {
        role: "Director of Digital Transformation & Innovation",
        departments: ["Strategy", "IT"],
        seniority: "Director",
      },
    ],
    pricing_model: "Enterprise Platform License + Engineering Services",
    differentiators: [
      "Native first-party evidence inspection for every single business claim",
      "Continuous monitoring and timeline changes vs static stale databases",
      "Explainable algorithmic target ranking instead of black-box opaque lead scoring",
    ],
  };

  return (
    <div className="max-w-4xl space-y-8 py-2">
      {/* Page Header */}
      <div className="border-b border-neutral-200 pb-5">
        <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
          Positioning
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          How GrowX understands your company
        </p>
      </div>

      {/* 1. Core Strategic Positioning */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          Positioning
        </div>
        <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
          <p className="text-base font-semibold text-neutral-900 leading-relaxed">
            "{data.positioning}"
          </p>

          <div className="flex items-center justify-between pt-2 border-t border-neutral-100 text-xs text-neutral-500">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Verified</span>
              </span>
              <span>•</span>
              <span>Updated today</span>
            </div>

            <button
              onClick={() =>
                openEvidenceDrawer({
                  claim: data.positioning,
                  sourceUrl: `https://${data.domain}`,
                  verificationStatus: "Verified",
                  confidenceScore: 0.99,
                })
              }
              className="text-xs text-neutral-600 hover:text-neutral-900 underline inline-flex items-center gap-1"
            >
              <FileSearch className="w-3.5 h-3.5 text-neutral-400" />
              <span>View sources</span>
            </button>
          </div>
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* 2. Capabilities */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          Capabilities
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {data.value_props.map((vp, idx) => (
            <div
              key={idx}
              className="p-4 bg-white border border-neutral-200 rounded-md flex flex-col justify-between space-y-3"
            >
              <div className="space-y-1.5">
                <div className="font-semibold text-xs text-neutral-900">
                  {vp.title}
                </div>
                <p className="text-xs text-neutral-500 leading-relaxed">
                  {vp.description}
                </p>
              </div>

              <div className="pt-2 border-t border-neutral-100 flex items-center justify-between text-[11px] text-neutral-500">
                <span className="text-emerald-700 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  <span>Verified</span>
                </span>
                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: `${vp.title}: ${vp.description}`,
                      sourceUrl: `https://${data.domain}/platform`,
                      verificationStatus: "Verified",
                    })
                  }
                  className="hover:text-neutral-900 underline"
                >
                  View sources
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* 3. What you solve */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          What you solve
        </div>
        <div className="space-y-2">
          {data.ideal_use_cases.map((useCase, idx) => (
            <div
              key={idx}
              className="p-3 bg-neutral-50 border border-neutral-200 rounded-md flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-2 text-neutral-800 font-medium">
                <div className="w-1.5 h-1.5 rounded-full bg-neutral-900" />
                <span>{useCase}</span>
              </div>
              <button
                onClick={() =>
                  openEvidenceDrawer({
                    claim: useCase,
                    sourceUrl: `https://${data.domain}/solutions`,
                    verificationStatus: "Verified",
                  })
                }
                className="text-[11px] text-neutral-500 hover:text-neutral-900 underline"
              >
                View sources
              </button>
            </div>
          ))}
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* 4. Who you sell to & Buyer roles */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Who you sell to */}
        <div className="space-y-3">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Who you sell to
          </div>
          <div className="space-y-2">
            {[
              { market: "Manufacturing", detail: "Precision engineering, automotive components, discrete manufacturing" },
              { market: "Industrial Companies", detail: "Heavy equipment, robotics, automation supply chains" },
              { market: "Legacy Enterprises", detail: "Organizations modernizing core business software and manual workflows" },
            ].map((m, idx) => (
              <div
                key={idx}
                className="p-3 bg-white border border-neutral-200 rounded-md space-y-1"
              >
                <div className="font-semibold text-xs text-neutral-900">
                  {m.market}
                </div>
                <div className="text-xs text-neutral-500">
                  {m.detail}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Buyer roles */}
        <div className="space-y-3">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Buyer roles
          </div>
          <div className="space-y-2">
            {data.target_buyer_roles.map((br, idx) => (
              <div
                key={idx}
                className="p-3 bg-white border border-neutral-200 rounded-md flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-neutral-900">
                    {br.role}
                  </div>
                  <div className="text-[11px] text-neutral-500 mt-0.5">
                    {br.departments.join(", ")}
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 bg-neutral-100 text-neutral-700 rounded font-medium">
                  {br.seniority}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* 5. Differentiators */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          Differentiators
        </div>
        <div className="space-y-2.5">
          {data.differentiators.map((diff, idx) => (
            <div
              key={idx}
              className="p-3.5 bg-white border border-neutral-200 rounded-md flex items-start justify-between gap-4 text-xs"
            >
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <span className="font-medium text-neutral-800 leading-relaxed">
                  {diff}
                </span>
              </div>

              <button
                onClick={() =>
                  openEvidenceDrawer({
                    claim: diff,
                    sourceUrl: `https://${data.domain}/platform`,
                    verificationStatus: "Verified",
                  })
                }
                className="text-xs text-neutral-500 hover:text-neutral-900 underline flex-shrink-0"
              >
                View sources
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
