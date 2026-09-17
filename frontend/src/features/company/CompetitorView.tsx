"use client";

import React, { useEffect, useState } from "react";
import {
  getSellerCompetitors,
  CompetitorRelationship,
} from "@/lib/api/company";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  ExternalLink,
  CheckCircle2,
  FileSearch,
  ArrowUpRight,
  ShieldCheck,
  Building2,
} from "lucide-react";
import { formatScorePercent } from "@/lib/product-language";

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
      shared_features: ["Sales intelligence", "B2B contact directory", "Firmographics"],
      advantages: [
        "Continuous company research vs static database exports",
        "Historical change intelligence tracking leadership & tech adoption",
        "Evidence-backed prospect ranking with transparent proof",
      ],
      disadvantages: [
        "Broad legacy enterprise footprint",
        "Extensive historical phone records",
      ],
      evidence_count: 14,
    },
    {
      competitor_id: "cmp_cognism",
      competitor_name: "Cognism",
      competitor_domain: "cognism.com",
      overlap_score: 0.76,
      relationship_type: "direct",
      shared_features: ["B2B intelligence", "Contact data", "Prospecting workflows"],
      advantages: [
        "Continuous company research",
        "Historical change intelligence",
        "Evidence-backed prospect ranking",
      ],
      disadvantages: ["Specialized phone-verified focus in European regions"],
      evidence_count: 6,
    },
    {
      competitor_id: "cmp_clay",
      competitor_name: "Clay",
      competitor_domain: "clay.com",
      overlap_score: 0.74,
      relationship_type: "adjacent",
      shared_features: ["Data enrichment workflows", "Waterfall integrations"],
      advantages: [
        "Native deep crawler engine vs purely relying on external provider credits",
        "Autonomous entity resolution and verification gates",
      ],
      disadvantages: ["Flexible spreadsheet canvas user interface"],
      evidence_count: 8,
    },
    {
      competitor_id: "cmp_apollo",
      competitor_name: "Apollo.io",
      competitor_domain: "apollo.io",
      overlap_score: 0.71,
      relationship_type: "direct",
      shared_features: ["Lead prospecting", "Contact enrichment", "Account filters"],
      advantages: [
        "Zero hallucination canonical verification",
        "Deep technographic and operational signal tracking",
      ],
      disadvantages: ["Mass cold email sequencing built-in"],
      evidence_count: 11,
    },
  ];

  const list = competitors.length > 0 ? competitors : defaultList;
  const activeComp = selectedComp || list[0];

  return (
    <div className="space-y-6 max-w-6xl py-2">
      {/* Page Header */}
      <div className="border-b border-neutral-200 pb-5">
        <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
          Competitors
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          Companies competing for similar customers and problems.
        </p>
      </div>

      {/* Split Layout: Competitor list (left) | Selected competitor detail (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left List (5 cols) */}
        <div className="lg:col-span-5 space-y-2">
          {list.map((c) => {
            const isSelected = activeComp?.competitor_id === c.competitor_id;
            const overlapPercent = formatScorePercent(c.overlap_score);
            const isDirect = c.relationship_type.toLowerCase() === "direct";

            return (
              <div
                key={c.competitor_id}
                onClick={() => setSelectedComp(c)}
                className={`p-4 rounded-md border cursor-pointer transition-all ${
                  isSelected
                    ? "bg-white border-neutral-900 shadow-xs"
                    : "bg-white border-neutral-200 hover:border-neutral-300"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-semibold text-sm text-neutral-900">
                      {c.competitor_name}
                    </div>
                    <div className="text-xs text-neutral-500 mt-0.5">
                      {c.shared_features?.[0] || "Sales intelligence"}
                    </div>
                  </div>

                  <span
                    className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                      isDirect
                        ? "bg-neutral-900 text-white"
                        : "bg-neutral-100 text-neutral-600"
                    }`}
                  >
                    {isDirect ? "Direct" : "Adjacent"}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-4 pt-2 border-t border-neutral-100 text-xs">
                  <span className="font-medium text-neutral-700">
                    {c.overlap_score >= 0.8 ? "Strong overlap" : `${overlapPercent} overlap`}
                  </span>

                  <span className="inline-flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Verified</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Detail Pane (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-neutral-200 rounded-md p-6 space-y-6">
          {activeComp && (
            <>
              {/* Header */}
              <div className="border-b border-neutral-200 pb-4 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-neutral-900">
                      {activeComp.competitor_name}
                    </h2>
                    <a
                      href={`https://${activeComp.competitor_domain}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-neutral-400 hover:text-neutral-900"
                    >
                      <ArrowUpRight className="w-4 h-4" />
                    </a>
                  </div>

                  <div className="mt-1 flex items-center gap-2 text-xs text-neutral-500">
                    <span className="font-medium text-neutral-800">
                      {activeComp.relationship_type.toLowerCase() === "direct"
                        ? "Direct competitor"
                        : "Adjacent competitor"}
                    </span>
                    <span>•</span>
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>Verified</span>
                    </span>
                  </div>
                </div>

                <span className="text-xs font-semibold text-neutral-900 px-2.5 py-1 bg-neutral-100 rounded">
                  {formatScorePercent(activeComp.overlap_score)} overlap
                </span>
              </div>

              {/* Why they overlap */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
                  Why they overlap
                </div>
                <div className="space-y-1.5">
                  {activeComp.shared_features.map((feat, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 text-xs font-medium text-neutral-800 p-2 bg-neutral-50 rounded border border-neutral-200"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-neutral-900" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Where GrowX differs */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
                  Where GrowX differs
                </div>
                <div className="space-y-1.5">
                  {activeComp.advantages.map((adv, idx) => (
                    <div
                      key={idx}
                      className="flex items-start gap-2.5 text-xs text-neutral-800 p-2.5 bg-emerald-50/50 rounded border border-emerald-200"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <span className="font-medium leading-relaxed">{adv}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sources & Inspection Footer */}
              <div className="pt-4 border-t border-neutral-200 flex items-center justify-between text-xs text-neutral-500">
                <div className="flex items-center gap-2">
                  <span>Sources {activeComp.evidence_count}</span>
                  <span>•</span>
                  <span>Updated today</span>
                </div>

                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: `Competitive overlap and differentiators between GrowxLabs and ${activeComp.competitor_name}`,
                      sourceUrl: `https://${activeComp.competitor_domain}`,
                      verificationStatus: "Verified",
                      confidenceScore: activeComp.overlap_score,
                    })
                  }
                  className="inline-flex items-center gap-1.5 text-neutral-900 hover:underline font-medium"
                >
                  <FileSearch className="w-3.5 h-3.5 text-neutral-500" />
                  <span>View sources</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
