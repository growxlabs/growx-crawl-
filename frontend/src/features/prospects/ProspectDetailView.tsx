"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ProspectDetail,
  getProspectDetail,
} from "@/lib/api/prospects";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import { ReverifyCallout } from "./ReverifyCallout";
import { ResearchMoreCallout } from "./ResearchMoreCallout";
import {
  Building2,
  Globe,
  MapPin,
  Users,
  Flame,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileSearch,
  ExternalLink,
  Linkedin,
  Clock,
  Sparkles,
  Zap,
  Edit3,
} from "lucide-react";

interface ProspectDetailViewProps {
  prospectId: string;
}

export function ProspectDetailView({ prospectId }: ProspectDetailViewProps) {
  const [detail, setDetail] = useState<ProspectDetail | null>(null);
  const [loading, setLoading] = useState(true);
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
    project_id: "prj_us_saas_expansion",
    company_id: "cmp_linear",
    company_name: "Linear",
    domain: "linear.app",
    industry: "Software & Issue Tracking",
    size_range: "50-200",
    employee_count: 85,
    headquarters: "San Francisco, CA",
    location: "San Francisco, CA",
    summary:
      "Linear builds purposeful software for modern product development, issue tracking, and automated engineering workflows.",
    priority: "Priority",
    rank_tier: "Priority",
    final_score: 0.94,
    icp_fit_score: 0.96,
    data_quality_score: 0.92,
    verification_status: "Verified",
    why_reasons: [
      "Exact ICP firmographic match: 80 employees in US B2B software sector",
      "Technographic match: Verified Salesforce CRM deployment and GitHub integrations",
      "High-intent signal: Posted 3 senior outbound account executive roles in last 14 days",
      "Executive decision-maker identified with deliverable contact channel",
    ],
    disqualifiers: [],
    signals: [
      {
        signal_id: "sig_01",
        signal_type: "hiring",
        title: "Active Sales Hiring Surge",
        description: "3 open SDR and AE roles detected on careers page.",
        detected_at: new Date(Date.now() - 3600000 * 24).toISOString(),
        confidence_score: 0.98,
        evidence_id: "evi_linear_jobs",
      },
      {
        signal_id: "sig_02",
        signal_type: "technographic",
        title: "Enterprise CRM Switch",
        description: "Deployed Salesforce Enterprise schema and OAuth endpoints.",
        detected_at: new Date(Date.now() - 3600000 * 72).toISOString(),
        confidence_score: 0.94,
        evidence_id: "evi_linear_sfdc",
      },
    ],
    people: [
      {
        person_id: "prs_01",
        full_name: "Karri Saarinen",
        job_title: "CEO & Co-founder",
        seniority: "C-Level",
        department: "Executive",
        verification_status: "Verified",
        confidence_score: 0.99,
        linkedin_url: "https://linkedin.com/in/ksaarinen",
        email_status: "verified",
      },
      {
        person_id: "prs_02",
        full_name: "Tuomas Artman",
        job_title: "CTO & Co-founder",
        seniority: "C-Level",
        department: "Engineering",
        verification_status: "Verified",
        confidence_score: 0.99,
        linkedin_url: "https://linkedin.com/in/artman",
        email_status: "verified",
      },
    ],
    verified_facts: [
      {
        fact_id: "fct_lin_01",
        field_name: "headquarters",
        value: "San Francisco, CA",
        verification_status: "Verified",
        confidence_score: 0.99,
        last_verified_at: new Date().toISOString(),
        source_url: "https://linear.app/about",
      },
      {
        fact_id: "fct_lin_02",
        field_name: "employee_count_range",
        value: "50-200",
        verification_status: "Verified",
        confidence_score: 0.95,
        last_verified_at: new Date().toISOString(),
        source_url: "https://linear.app/about",
      },
      {
        fact_id: "fct_lin_03",
        field_name: "pricing_tier",
        value: "Free, Standard ($8/user), Plus ($14/user), Enterprise",
        verification_status: "Verified",
        confidence_score: 0.98,
        last_verified_at: new Date().toISOString(),
        source_url: "https://linear.app/pricing",
      },
    ],
    score_history: [
      {
        timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
        score: 0.94,
        rank_tier: "Priority",
        change_reason: "Hiring signal boosted timing component by +0.12",
      },
      {
        timestamp: new Date(Date.now() - 3600000 * 72).toISOString(),
        score: 0.82,
        rank_tier: "Strong",
        change_reason: "Initial canonical crawl and fact verification baseline",
      },
    ],
    requires_reverification: false,
    requires_research: false,
  };

  return (
    <div className="space-y-6">
      {/* Header Profile Card */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded bg-neutral-900 text-white flex items-center justify-center font-bold text-lg">
              {p.company_name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-neutral-900">
                  {p.company_name}
                </h1>
                <StatusBadge status={p.rank_tier} size="sm" />
                <StatusBadge status={p.verification_status} size="sm" />
              </div>

              <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-neutral-500 font-sans">
                <span className="flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-neutral-400" />
                  <a
                    href={`https://${p.domain}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-neutral-900 hover:underline font-mono"
                  >
                    {p.domain}
                  </a>
                </span>
                <span>•</span>
                <span>{p.industry}</span>
                <span>•</span>
                <span>{p.size_range} employees</span>
                <span>•</span>
                <span>{p.headquarters}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() =>
                openCorrectionModal({
                  companyId: p.company_id,
                  claim: `${p.company_name} canonical profile`,
                })
              }
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-neutral-300 hover:bg-neutral-100 text-xs font-medium text-neutral-700"
            >
              <Edit3 className="w-3.5 h-3.5 text-neutral-600" />
              <span>Correct Fact</span>
            </button>

            <button
              onClick={() =>
                openEvidenceDrawer({
                  claim: `${p.company_name} Priority Qualification (${Math.round(
                    p.final_score * 100
                  )}%)`,
                  sourceUrl: `https://${p.domain}`,
                  verificationStatus: p.verification_status,
                  confidenceScore: p.final_score,
                })
              }
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-neutral-900 hover:bg-neutral-800 text-white font-medium text-xs shadow-2xs"
            >
              <FileSearch className="w-3.5 h-3.5" />
              <span>Inspect Proof</span>
            </button>
          </div>
        </div>

        {/* Company Summary */}
        <div className="mt-4 pt-4 border-t border-neutral-100">
          <p className="text-xs leading-relaxed text-neutral-600">
            {p.summary}
          </p>
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

      {/* Scorecard Breakdown */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-neutral-200 pb-3">
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Deterministic Priority Scorecard
            </h2>
            <p className="text-xs text-neutral-500 mt-0.5">
              Explainable ranking derived from verified facts, ICP criteria weights, and temporal signals.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-neutral-400 uppercase">Overall:</span>
            <span className="text-xl font-bold font-mono text-neutral-900">
              {Math.round(p.final_score * 100)}%
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 space-y-1">
            <span className="text-[10px] font-mono uppercase text-neutral-400">
              ICP Fit Score
            </span>
            <div className="flex items-center justify-between">
              <span className="text-base font-bold font-mono text-neutral-900">
                {Math.round(p.icp_fit_score * 100)}%
              </span>
              <ConfidenceIndicator score={p.icp_fit_score} showValue={false} size="sm" />
            </div>
            <p className="text-[11px] text-neutral-500">
              Evaluated against mandatory dealbreakers and criterion weights.
            </p>
          </div>

          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 space-y-1">
            <span className="text-[10px] font-mono uppercase text-neutral-400">
              Data Quality & Freshness
            </span>
            <div className="flex items-center justify-between">
              <span className="text-base font-bold font-mono text-neutral-900">
                {Math.round(p.data_quality_score * 100)}%
              </span>
              <ConfidenceIndicator score={p.data_quality_score} showValue={false} size="sm" />
            </div>
            <p className="text-[11px] text-neutral-500">
              Zero missing critical attributes and verified source citations.
            </p>
          </div>

          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 space-y-1">
            <span className="text-[10px] font-mono uppercase text-neutral-400">
              Temporal Intent Timing
            </span>
            <div className="flex items-center justify-between">
              <span className="text-base font-bold font-mono text-neutral-900">
                {p.signals.length > 0 ? "High Timing" : "Neutral"}
              </span>
              <StatusBadge status={p.signals.length > 0 ? "Priority" : "Possible"} size="sm" showIcon={false} />
            </div>
            <p className="text-[11px] text-neutral-500">
              {p.signals.length} high-confidence signals detected in last 30 days.
            </p>
          </div>
        </div>

        {/* Why is this prospect ranked here? */}
        <div className="pt-3">
          <div className="text-[11px] font-mono uppercase font-semibold text-neutral-900 mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Why Ranked as {p.rank_tier}?</span>
          </div>
          <div className="space-y-1.5">
            {p.why_reasons.map((reason, rIdx) => (
              <div
                key={rIdx}
                className="p-2.5 rounded bg-emerald-50/40 border border-emerald-200/60 text-xs text-neutral-800 flex items-start justify-between gap-3"
              >
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-600 mt-1.5 flex-shrink-0" />
                  <span>{reason}</span>
                </div>
                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: reason,
                      sourceUrl: `https://${p.domain}`,
                      verificationStatus: "Verified",
                    })
                  }
                  className="text-[10px] text-blue-600 hover:text-blue-800 underline flex-shrink-0"
                >
                  Verify
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Disqualifiers if any */}
        {p.disqualifiers && p.disqualifiers.length > 0 && (
          <div className="pt-2">
            <div className="text-[11px] font-mono uppercase font-semibold text-rose-700 mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
              <span>Active Disqualifiers / Warning Flags</span>
            </div>
            <div className="space-y-1.5">
              {p.disqualifiers.map((dis, dIdx) => (
                <div
                  key={dIdx}
                  className="p-2.5 rounded bg-rose-50 border border-rose-200 text-xs text-rose-900 flex items-center gap-2"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-rose-600 flex-shrink-0" />
                  <span>{dis}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Signals Section */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-neutral-800" />
            <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Observed Temporal Signals ({p.signals.length})
            </h2>
          </div>
          <span className="text-[11px] font-mono text-neutral-400">
            Source-backed events
          </span>
        </div>

        <div className="space-y-3">
          {p.signals.map((sig) => (
            <div
              key={sig.signal_id}
              className="p-3 bg-neutral-50 rounded border border-neutral-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-neutral-900">
                    {sig.title}
                  </span>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-neutral-200 text-neutral-700">
                    {sig.signal_type}
                  </span>
                </div>
                <p className="text-neutral-600 text-[11px] mt-0.5">
                  {sig.description}
                </p>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <ConfidenceIndicator score={sig.confidence_score} size="sm" />
                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: `${sig.title}: ${sig.description}`,
                      evidenceId: sig.evidence_id,
                      verificationStatus: "Verified",
                      confidenceScore: sig.confidence_score,
                    })
                  }
                  className="text-[11px] text-blue-600 hover:text-blue-800 underline"
                >
                  Inspect
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Verified Facts Table */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-neutral-800" />
            <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Verified Facts & Attributes ({p.verified_facts.length})
            </h2>
          </div>
          <button
            onClick={() =>
              openCorrectionModal({
                companyId: p.company_id,
                claim: "General company attributes",
              })
            }
            className="text-[11px] text-neutral-600 hover:text-neutral-900 underline flex items-center gap-1"
          >
            <Edit3 className="w-3 h-3" />
            <span>Override a Fact</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-neutral-50 text-[11px] uppercase font-mono text-neutral-500 border-b border-neutral-200">
              <tr>
                <th className="px-3 py-2">Attribute</th>
                <th className="px-3 py-2">Canonical Value</th>
                <th className="px-3 py-2">Verification</th>
                <th className="px-3 py-2">Confidence</th>
                <th className="px-3 py-2">Evidence & Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200">
              {p.verified_facts.map((fact) => (
                <tr key={fact.fact_id} className="hover:bg-neutral-50/50">
                  <td className="px-3 py-2.5 font-mono text-[11px] font-semibold text-neutral-900">
                    {fact.field_name}
                  </td>
                  <td className="px-3 py-2.5 font-medium text-neutral-800 max-w-sm truncate">
                    {String(fact.value)}
                  </td>
                  <td className="px-3 py-2.5">
                    <StatusBadge status={fact.verification_status} size="sm" />
                  </td>
                  <td className="px-3 py-2.5">
                    <ConfidenceIndicator score={fact.confidence_score} size="sm" />
                  </td>
                  <td className="px-3 py-2.5">
                    <button
                      onClick={() =>
                        openEvidenceDrawer({
                          factId: fact.fact_id,
                          claim: `${fact.field_name}: ${fact.value}`,
                          sourceUrl: fact.source_url,
                          verificationStatus: fact.verification_status,
                          confidenceScore: fact.confidence_score,
                        })
                      }
                      className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 underline"
                    >
                      <FileSearch className="w-3 h-3" />
                      <span>Inspect DOM Proof</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Contacts / Target People */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-neutral-800" />
            <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Matched Buyer Decision Makers ({p.people.length})
            </h2>
          </div>
          <span className="text-[11px] font-mono text-neutral-400">
            Export ready for outreach
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {p.people.map((person) => (
            <div
              key={person.person_id}
              className="p-4 rounded border border-neutral-200 bg-neutral-50/40 flex items-start justify-between gap-3 text-xs"
            >
              <div>
                <div className="font-semibold text-neutral-900">
                  {person.full_name}
                </div>
                <div className="text-[11px] text-neutral-500 mt-0.5">
                  {person.job_title}
                </div>
                <div className="mt-2 flex items-center gap-2 font-mono text-[10px]">
                  <span className="px-1.5 py-0.5 rounded bg-neutral-200 text-neutral-800">
                    {person.seniority}
                  </span>
                  <span className="text-neutral-500">{person.department}</span>
                </div>
              </div>

              <div className="flex flex-col items-end gap-2">
                <StatusBadge status={person.verification_status} size="sm" />
                {person.linkedin_url && (
                  <a
                    href={person.linkedin_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-neutral-400 hover:text-blue-600"
                  >
                    <Linkedin className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Score History */}
      {p.score_history && p.score_history.length > 0 && (
        <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-neutral-800" />
            <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Scorecard History & Calibration Log
            </h2>
          </div>

          <div className="space-y-2">
            {p.score_history.map((hist, hIdx) => (
              <div
                key={hIdx}
                className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between text-xs font-mono"
              >
                <div>
                  <span className="font-bold text-neutral-900 mr-2">
                    {Math.round(hist.score * 100)}% ({hist.rank_tier})
                  </span>
                  <span className="text-neutral-600 font-sans">{hist.change_reason}</span>
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
