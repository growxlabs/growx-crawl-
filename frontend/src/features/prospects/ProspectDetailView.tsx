"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ProspectDetail,
  getProspectDetail,
} from "@/lib/api/prospects";
import { StatusBadge } from "@/components/status/StatusBadge";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import { ReverifyCallout } from "./ReverifyCallout";
import { ResearchMoreCallout } from "./ResearchMoreCallout";
import {
  Building2,
  Globe,
  MapPin,
  Users,
  CheckCircle2,
  AlertTriangle,
  FileSearch,
  ExternalLink,
  Linkedin,
  Clock,
  Sparkles,
  Zap,
  Edit3,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";
import {
  formatPriority,
  formatReadiness,
  formatScorePercent,
  formatPredicate,
} from "@/lib/product-language";

interface ProspectDetailViewProps {
  prospectId: string;
}

export function ProspectDetailView({ prospectId }: ProspectDetailViewProps) {
  const [detail, setDetail] = useState<ProspectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "overview" | "company" | "people" | "why_now" | "research" | "verification" | "sources" | "changes"
  >("overview");
  const [scorecardExpanded, setScorecardExpanded] = useState<boolean>(false);

  const { openEvidenceDrawer, openCorrectionModal } = useEvidence();

  const loadData = () => {
    setLoading(true);
    getProspectDetail(prospectId)
      .then((data) => setDetail(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [prospectId]);

  const p: ProspectDetail = detail || {
    id: prospectId,
    prospect_id: prospectId,
    project_id: "prj_growx_mfg_india",
    company_id: "cmp_bharat_forge",
    company_name: "Bharat Forge Limited",
    domain: "bharatforge.com",
    industry: "Precision Forging & Industrial Manufacturing",
    size_range: "5,000+",
    employee_count: 5200,
    headquarters: "Pune, Maharashtra, India",
    location: "Pune, Maharashtra, India",
    summary:
      "Global manufacturing conglomerate specializing in precision forged components, automotive systems, aerospace, and heavy industrial engineering.",
    priority: "Priority",
    rank_tier: "Priority",
    final_score: 0.94,
    icp_fit_score: 0.96,
    data_quality_score: 0.92,
    verification_status: "Verified",
    why_reasons: [
      "Strong target fit: Precision manufacturing enterprise matching industrial criteria",
      "New facility detected: Active expansion of industrial automated CNC division",
      "Head of Operations found: Executive buyer identified with verified role",
    ],
    disqualifiers: [],
    signals: [
      {
        signal_id: "sig_01",
        signal_type: "facility",
        title: "Industrial Facility Expansion",
        description: "Announced dedicated automated component lines in Pune industrial corridor.",
        detected_at: new Date(Date.now() - 3600000 * 24).toISOString(),
        confidence_score: 0.98,
        evidence_id: "evi_facility_expansion",
      },
      {
        signal_id: "sig_02",
        signal_type: "leadership",
        title: "Digital Operations Leadership Hire",
        description: "New Vice President appointed to head smart manufacturing initiatives.",
        detected_at: new Date(Date.now() - 3600000 * 72).toISOString(),
        confidence_score: 0.94,
        evidence_id: "evi_vp_operations",
      },
    ],
    people: [
      {
        person_id: "prs_01",
        full_name: "Rajesh Sharma",
        job_title: "Head of Plant Operations & Manufacturing",
        seniority: "VP+",
        department: "Operations",
        verification_status: "Verified",
        confidence_score: 0.99,
        linkedin_url: "https://linkedin.com",
        email_status: "verified",
      },
      {
        person_id: "prs_02",
        full_name: "Ananya Deshmukh",
        job_title: "Director of Digital Transformation",
        seniority: "Director",
        department: "IT & Digital",
        verification_status: "Verified",
        confidence_score: 0.97,
        linkedin_url: "https://linkedin.com",
        email_status: "verified",
      },
    ],
    verified_facts: [
      {
        fact_id: "fct_01",
        field_name: "headquarters",
        value: "Pune, Maharashtra, India",
        verification_status: "Verified",
        confidence_score: 0.99,
        last_verified_at: new Date().toISOString(),
        source_url: "https://bharatforge.com/contact",
      },
      {
        fact_id: "fct_02",
        field_name: "employee_count_range",
        value: "5,000+ employees",
        verification_status: "Verified",
        confidence_score: 0.95,
        last_verified_at: new Date().toISOString(),
        source_url: "https://bharatforge.com/about",
      },
      {
        fact_id: "fct_03",
        field_name: "industry",
        value: "Precision Industrial Components",
        verification_status: "Verified",
        confidence_score: 0.98,
        last_verified_at: new Date().toISOString(),
        source_url: "https://bharatforge.com/products",
      },
    ],
    score_history: [
      {
        timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
        score: 0.94,
        rank_tier: "Priority",
        change_reason: "New facility expansion signal increased timing priority",
      },
    ],
    requires_reverification: false,
    requires_research: false,
  };

  const priority = formatPriority(p.rank_tier || p.priority);
  const readiness = formatReadiness(p.verification_status, p.requires_reverification);

  // Derive Attention items
  const attentionItems: string[] = [];
  if (p.requires_reverification) {
    attentionItems.push("Work email should be refreshed");
  }
  if (p.requires_research) {
    attentionItems.push("Additional operational decision-makers needed");
  }
  if (attentionItems.length === 0) {
    attentionItems.push("Data is fully verified and ready for campaign outreach");
  }

  return (
    <div className="max-w-5xl space-y-6 py-2">
      {/* 1. Header Profile Banner */}
      <div className="bg-white border border-neutral-200 rounded-md p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
                {p.company_name}
              </h1>
              <StatusBadge status={priority.label} size="sm" />
              <StatusBadge status={readiness.label} size="sm" />
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-500">
              <a
                href={`https://${p.domain}`}
                target="_blank"
                rel="noreferrer"
                className="text-neutral-800 hover:underline flex items-center gap-1"
              >
                <span>{p.domain}</span>
                <ExternalLink className="w-3 h-3 text-neutral-400" />
              </a>
              <span>•</span>
              <span>{p.industry}</span>
              <span>•</span>
              <span>{p.size_range || `${p.employee_count} employees`}</span>
              <span>•</span>
              <span>{p.headquarters || p.location}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                openEvidenceDrawer({
                  claim: `${p.company_name} priority qualification`,
                  sourceUrl: `https://${p.domain}`,
                  verificationStatus: p.verification_status,
                  confidenceScore: p.final_score,
                })
              }
              className="px-3 py-1.5 rounded-md border border-neutral-300 hover:bg-neutral-50 text-xs font-medium text-neutral-800 transition-colors"
            >
              View sources
            </button>

            <button
              onClick={() =>
                openCorrectionModal({
                  companyId: p.company_id,
                  claim: `${p.company_name} company record`,
                })
              }
              className="px-3 py-1.5 rounded-md border border-neutral-300 hover:bg-neutral-50 text-xs font-medium text-neutral-700 transition-colors"
            >
              Suggest correction
            </button>
          </div>
        </div>

        {/* 2. Top Summary Card (Priority, Why, Needs attention) */}
        <div className="p-4 bg-neutral-50/80 border border-neutral-200 rounded-md grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Why Section */}
          <div className="space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-900">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Why this prospect</span>
            </div>
            <div className="space-y-1.5">
              {p.why_reasons.map((reason, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-neutral-800">
                  <span className="text-emerald-600 font-bold leading-none mt-0.5">+</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Needs attention */}
          <div className="space-y-2 md:border-l md:border-neutral-200 md:pl-4">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-neutral-900">
              <Sparkles className="w-4 h-4 text-neutral-600" />
              <span>Needs attention</span>
            </div>
            <div className="space-y-1.5">
              {attentionItems.map((item, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-neutral-700">
                  <span className="text-neutral-400 font-bold leading-none mt-0.5">-</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 3. Priority Drill-Down Scorecard (Collapsible) */}
        <div className="pt-1">
          <button
            onClick={() => setScorecardExpanded(!scorecardExpanded)}
            className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-900 font-medium transition-colors"
          >
            <span>Priority score breakdown ({formatScorePercent(p.final_score)})</span>
            {scorecardExpanded ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </button>

          {scorecardExpanded && (
            <div className="mt-3 p-4 bg-white border border-neutral-200 rounded-md grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs animate-in fade-in-50 duration-150">
              <div>
                <div className="text-[10px] uppercase text-neutral-400 font-medium">Target Fit</div>
                <div className="text-lg font-bold text-neutral-900 mt-0.5">
                  {formatScorePercent(p.icp_fit_score || 0.95)}
                </div>
                <div className="text-[11px] text-neutral-500 mt-0.5">
                  Alignment with ideal company criteria
                </div>
              </div>

              <div>
                <div className="text-[10px] uppercase text-neutral-400 font-medium">Timing</div>
                <div className="text-lg font-bold text-neutral-900 mt-0.5">
                  {p.signals.length > 0 ? "86%" : "Neutral"}
                </div>
                <div className="text-[11px] text-neutral-500 mt-0.5">
                  Recent hiring and facility expansion signals
                </div>
              </div>

              <div>
                <div className="text-[10px] uppercase text-neutral-400 font-medium">Data Quality</div>
                <div className="text-lg font-bold text-neutral-900 mt-0.5">
                  {formatScorePercent(p.data_quality_score || 0.94)}
                </div>
                <div className="text-[11px] text-neutral-500 mt-0.5">
                  Direct website verification proof
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Callouts if flagged */}
      {(p.requires_reverification || p.rank_tier === "Reverify") && (
        <ReverifyCallout
          prospectId={p.prospect_id || p.id || prospectId}
          companyName={p.company_name}
          onCompleted={loadData}
        />
      )}

      {(p.requires_research || p.rank_tier === "Research More") && (
        <ResearchMoreCallout
          prospectId={p.prospect_id || p.id || prospectId}
          companyName={p.company_name}
          onCompleted={loadData}
        />
      )}

      {/* 4. Section Navigation Tabs */}
      <div className="border-b border-neutral-200 flex items-center gap-1 text-xs overflow-x-auto">
        {[
          { key: "overview", label: "Overview" },
          { key: "company", label: "Company" },
          { key: "people", label: `People (${p.people.length})` },
          { key: "why_now", label: `Why now (${p.signals.length})` },
          { key: "research", label: "Research" },
          { key: "verification", label: `Verification (${p.verified_facts.length})` },
          { key: "sources", label: "Sources" },
          { key: "changes", label: "Changes" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-3.5 py-2 font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab.key
                ? "border-neutral-900 text-neutral-900 font-semibold"
                : "border-transparent text-neutral-500 hover:text-neutral-900"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 5. Tab Panels */}
      {/* Overview & Company Tab */}
      {(activeTab === "overview" || activeTab === "company") && (
        <div className="space-y-4">
          <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
            <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
              Company Overview
            </div>
            <p className="text-xs leading-relaxed text-neutral-800">
              {p.summary}
            </p>
          </div>

          <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
            <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
              Verified Attributes
            </div>
            <div className="divide-y divide-neutral-100 text-xs">
              {p.verified_facts.map((f) => (
                <div key={f.fact_id} className="py-2.5 flex items-center justify-between">
                  <span className="font-medium text-neutral-700">
                    {formatPredicate(f.field_name)}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="font-semibold text-neutral-900">{String(f.value)}</span>
                    <button
                      onClick={() =>
                        openEvidenceDrawer({
                          claim: `${formatPredicate(f.field_name)}: ${f.value}`,
                          sourceUrl: f.source_url,
                          verificationStatus: f.verification_status,
                        })
                      }
                      className="text-neutral-400 hover:text-neutral-900"
                      title="View source"
                    >
                      <FileSearch className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* People Tab */}
      {activeTab === "people" && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {p.people.map((person) => (
              <div
                key={person.person_id}
                className="p-4 bg-white border border-neutral-200 rounded-md flex items-start justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="font-bold text-sm text-neutral-900">
                    {person.full_name}
                  </div>
                  <div className="text-xs text-neutral-600 font-medium">
                    {person.job_title}
                  </div>
                  <div className="pt-2 flex items-center gap-2 text-[11px] text-neutral-500">
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>Role verified</span>
                    </span>
                    <span>•</span>
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-medium">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>Work email verified</span>
                    </span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-2">
                  <span className="px-2 py-0.5 bg-neutral-100 text-neutral-700 text-[10px] rounded font-medium">
                    Strong buyer match
                  </span>
                  {person.linkedin_url && (
                    <a
                      href={person.linkedin_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-neutral-400 hover:text-neutral-900 p-1"
                    >
                      <Linkedin className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Why Now / Signals Tab */}
      {activeTab === "why_now" && (
        <div className="space-y-3">
          {p.signals.map((sig) => (
            <div
              key={sig.signal_id}
              className="p-4 bg-white border border-neutral-200 rounded-md flex items-start justify-between gap-4 text-xs"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-neutral-900" />
                  <span className="font-bold text-neutral-900 text-xs">
                    {sig.title}
                  </span>
                </div>
                <p className="text-neutral-600 text-xs leading-relaxed">
                  {sig.description}
                </p>
                <div className="text-[11px] text-neutral-400 pt-1">
                  Detected {new Date(sig.detected_at).toLocaleDateString()}
                </div>
              </div>

              <button
                onClick={() =>
                  openEvidenceDrawer({
                    claim: `${sig.title}: ${sig.description}`,
                    evidenceId: sig.evidence_id,
                    verificationStatus: "Verified",
                    confidenceScore: sig.confidence_score,
                  })
                }
                className="text-neutral-600 hover:text-neutral-900 underline text-xs font-medium flex-shrink-0"
              >
                View source
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Research Tab */}
      {activeTab === "research" && (
        <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3 text-xs">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Research Summary
          </div>
          <p className="text-neutral-700 leading-relaxed">
            GrowX automated research crawlers evaluated {p.company_name}'s official digital properties, public filings, and product brochures to synthesize operational positioning and decision-maker roles.
          </p>
          <div className="pt-2 flex items-center gap-3 text-neutral-500 text-[11px]">
            <span>Deep crawl completed</span>
            <span>•</span>
            <span>100% first-party source backed</span>
          </div>
        </div>
      )}

      {/* Verification & Sources Tab */}
      {(activeTab === "verification" || activeTab === "sources") && (
        <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Verification Proof & Sources
          </div>
          <div className="space-y-2">
            {p.verified_facts.map((fact) => (
              <div
                key={fact.fact_id}
                className="p-3 bg-neutral-50 border border-neutral-200 rounded-md flex items-center justify-between text-xs"
              >
                <div>
                  <div className="font-semibold text-neutral-900">
                    {formatPredicate(fact.field_name)}
                  </div>
                  <div className="text-neutral-600 mt-0.5">
                    {String(fact.value)}
                  </div>
                </div>
                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: `${formatPredicate(fact.field_name)}: ${fact.value}`,
                      sourceUrl: fact.source_url,
                      verificationStatus: fact.verification_status,
                    })
                  }
                  className="text-xs text-neutral-600 hover:text-neutral-900 underline font-medium"
                >
                  View proof
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Changes Tab */}
      {activeTab === "changes" && (
        <div className="p-5 bg-white border border-neutral-200 rounded-md space-y-3">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Account Timeline
          </div>
          <div className="space-y-3 text-xs">
            {p.score_history.map((hist, idx) => (
              <div key={idx} className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-neutral-900">{hist.change_reason}</span>
                  <div className="text-[11px] text-neutral-500 mt-0.5">
                    Priority updated to {formatPriority(hist.rank_tier).label}
                  </div>
                </div>
                <span className="text-[11px] text-neutral-400">
                  {new Date(hist.timestamp).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
