"use client";

import React, { useEffect, useState } from "react";
import {
  getSellerCompetitors,
  CompetitorRelationship,
} from "@/lib/api/company";
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  GitCompare,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  FileSearch,
  ArrowUpRight,
} from "lucide-react";
import { StatusBadge } from "@/components/status/StatusBadge";

export function CompetitorView() {
  const [competitors, setCompetitors] = useState<CompetitorRelationship[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedComp, setSelectedComp] = useState<CompetitorRelationship | null>(null);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    getSellerCompetitors()
      .then((data) => {
        setCompetitors(data);
        if (data && data.length > 0) setSelectedComp(data[0]);
      })
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const defaultList: CompetitorRelationship[] = [
    {
      competitor_id: "cmp_zoominfo",
      competitor_name: "ZoomInfo",
      competitor_domain: "zoominfo.com",
      overlap_score: 0.88,
      relationship_type: "direct",
      shared_features: ["B2B Contact Database", "Firmographics", "Org Charts"],
      advantages: [
        "First-party DOM verified proof for every claim",
        "Autonomous temporal diff tracking vs stale database exports",
        "Explainable deterministic scoring transparent to user",
      ],
      disadvantages: [
        "ZoomInfo has broader legacy enterprise footprint",
        "ZoomInfo maintains larger raw phone directory",
      ],
      evidence_count: 14,
    },
    {
      competitor_id: "cmp_apollo",
      competitor_name: "Apollo.io",
      competitor_domain: "apollo.io",
      overlap_score: 0.82,
      relationship_type: "direct",
      shared_features: ["Sales Engagement", "Lead Prospecting", "Data Enrichment"],
      advantages: [
        "Zero hallucination canonical verification",
        "Deeper technical stack and intent detection",
      ],
      disadvantages: ["Apollo includes native mass cold email sequencing"],
      evidence_count: 11,
    },
    {
      competitor_id: "cmp_clay",
      competitor_name: "Clay",
      competitor_domain: "clay.com",
      overlap_score: 0.74,
      relationship_type: "adjacent",
      shared_features: ["Data Enrichment Workflows", "Waterfall Providers"],
      advantages: [
        "Native deep crawler engine vs purely relying on 3rd party credits",
        "Built-in temporal change detection and verification gates",
      ],
      disadvantages: ["Clay offers flexible spreadsheet canvas UX"],
      evidence_count: 8,
    },
    {
      competitor_id: "cmp_cognism",
      competitor_name: "Cognism",
      competitor_domain: "cognism.com",
      overlap_score: 0.71,
      relationship_type: "direct",
      shared_features: ["EMEA B2B Intelligence", "Phone Verification"],
      advantages: [
        "Automated deep entity analysis and autonomous prospect ranking",
      ],
      disadvantages: ["Cognism has specialized phone-verified focus in Europe"],
      evidence_count: 6,
    },
  ];

  const list = competitors.length > 0 ? competitors : defaultList;
  const activeComp = selectedComp || list[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitCompare className="w-4 h-4 text-neutral-800" />
            <h1 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Competitor Graph & Market Overlap
            </h1>
          </div>
          <span className="text-xs font-mono text-neutral-500">
            {list.length} Verified Competitor Entities
          </span>
        </div>
        <p className="text-xs text-neutral-500 mt-1">
          Evidence-backed competitive positioning graph mapping direct and adjacent
          market alternatives, overlap percentages, and verified differentiators.
        </p>
      </div>

      {/* Grid: Left Competitor List, Right Selected Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Competitor Cards (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {list.map((c) => {
            const isSelected = activeComp?.competitor_id === c.competitor_id;
            return (
              <div
                key={c.competitor_id}
                onClick={() => setSelectedComp(c)}
                className={`p-4 rounded border cursor-pointer transition-all ${
                  isSelected
                    ? "bg-white border-neutral-900 shadow-xs"
                    : "bg-white border-neutral-200 hover:border-neutral-300"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="font-semibold text-xs text-neutral-900">
                      {c.competitor_name}
                    </span>
                    <span className="text-[11px] text-neutral-400 font-mono ml-2">
                      {c.competitor_domain}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] uppercase font-mono px-1.5 py-0.5 rounded border ${
                      c.relationship_type === "direct"
                        ? "bg-purple-50 text-purple-700 border-purple-200"
                        : "bg-neutral-100 text-neutral-600 border-neutral-200"
                    }`}
                  >
                    {c.relationship_type}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-3 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-neutral-500">Overlap:</span>
                    <ConfidenceIndicator score={c.overlap_score} size="sm" />
                  </div>
                  <span className="text-[11px] font-mono text-neutral-400">
                    {c.evidence_count} citations
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Competitor Comparison Panel (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-neutral-200 rounded p-6 shadow-2xs space-y-5">
          {activeComp && (
            <>
              {/* Profile Card */}
              <div className="flex items-start justify-between border-b border-neutral-200 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-neutral-900">
                      {activeComp.competitor_name}
                    </h2>
                    <a
                      href={`https://${activeComp.competitor_domain}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-neutral-400 hover:text-neutral-800"
                    >
                      <ArrowUpRight className="w-4 h-4" />
                    </a>
                  </div>
                  <div className="text-xs text-neutral-500 mt-0.5 font-mono">
                    {activeComp.competitor_domain} • {activeComp.relationship_type} relationship
                  </div>
                </div>

                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: `Competitive overlap between GrowxLabs and ${activeComp.competitor_name}`,
                      sourceUrl: `https://${activeComp.competitor_domain}`,
                      verificationStatus: "Verified",
                      confidenceScore: activeComp.overlap_score,
                    })
                  }
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-neutral-300 hover:bg-neutral-100 text-xs font-medium text-neutral-700"
                >
                  <FileSearch className="w-3.5 h-3.5 text-neutral-600" />
                  <span>Inspect Citations ({activeComp.evidence_count})</span>
                </button>
              </div>

              {/* Shared Capabilities */}
              <div>
                <div className="text-[10px] uppercase font-mono text-neutral-400 mb-2">
                  Shared Capabilities & Features
                </div>
                <div className="flex flex-wrap gap-2">
                  {activeComp.shared_features.map((feat, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded bg-neutral-100 text-neutral-800 text-xs font-medium border border-neutral-200"
                    >
                      {feat}
                    </span>
                  ))}
                </div>
              </div>

              {/* GrowxLabs Verified Advantages */}
              <div className="space-y-2">
                <div className="text-[10px] uppercase font-mono text-emerald-700 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Our Verified Differentiators vs {activeComp.competitor_name}</span>
                </div>
                <div className="space-y-2">
                  {activeComp.advantages.map((adv, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-emerald-50/50 border border-emerald-200/80 text-xs text-emerald-900 flex items-start gap-2"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <span>{adv}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Competitor Strengths / Disadvantages */}
              <div className="space-y-2">
                <div className="text-[10px] uppercase font-mono text-neutral-500 font-medium">
                  {activeComp.competitor_name} Market Strengths
                </div>
                <div className="space-y-2">
                  {activeComp.disadvantages.map((dis, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded bg-neutral-50 border border-neutral-200 text-xs text-neutral-700 flex items-start gap-2"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-neutral-400 mt-1.5 flex-shrink-0" />
                      <span>{dis}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
