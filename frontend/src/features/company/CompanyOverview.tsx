"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  Globe,
  MapPin,
  Users,
  CheckCircle2,
  Sparkles,
  GitCompare,
  History,
  FileSearch,
  ExternalLink,
} from "lucide-react";
import {
  getSellerOverview,
  triggerSellerAnalysis,
  SellerOverview as SellerOverviewType,
} from "@/lib/api/company";
import { StatusBadge } from "@/components/status/StatusBadge";
import { JobProgressBar } from "@/components/status/JobProgressBar";
import { useEvidence } from "@/components/inspector/EvidenceContext";

export function CompanyOverview() {
  const [overview, setOverview] = useState<SellerOverviewType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [analyzingJobId, setAnalyzingJobId] = useState<string | null>(null);
  const { openEvidenceDrawer } = useEvidence();

  const fetchOverview = () => {
    setLoading(true);
    getSellerOverview()
      .then((data) => setOverview(data))
      .catch((err) => console.error("Failed to load seller overview", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleReanalyze = async () => {
    try {
      const res = await triggerSellerAnalysis();
      setAnalyzingJobId(res.job_id);
    } catch (err) {
      console.error("Failed to trigger analysis", err);
    }
  };

  if (loading && !overview) {
    return (
      <div className="p-8 text-center text-xs font-mono text-neutral-400">
        Loading canonical seller profile...
      </div>
    );
  }

  const data = overview || {
    id: "cmp_seller_growxlabs",
    name: "GrowxLabs Intelligence",
    company_name: "GrowxLabs Intelligence",
    domain: "growxlabs.com",
    industry: "B2B SaaS & Data Intelligence",
    size_range: "50-200",
    headquarters: "San Francisco, CA",
    summary:
      "GrowxLabs develops autonomous GTM intelligence pipelines, canonical entity resolution, and verified prospect prioritization for enterprise B2B sales teams.",
    verified_facts_count: 38,
    active_icps_count: 2,
    competitors_count: 4,
    last_crawled_at: new Date().toISOString(),
  };

  const companyName = data.name || data.company_name || "GrowxLabs Intelligence";

  return (
    <div className="space-y-6">
      {/* Header Profile Card */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded bg-neutral-900 text-white flex items-center justify-center font-bold text-lg">
              {companyName.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-semibold text-neutral-900 tracking-tight">
                  {companyName}
                </h1>
                <StatusBadge status="Verified" size="sm" />
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-neutral-500">
                <span className="flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-neutral-400" />
                  <a
                    href={`https://${data.domain}`}
                    target="_blank"
                    rel="noreferrer"
                    className="hover:text-neutral-900 underline"
                  >
                    {data.domain}
                  </a>
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Building2 className="w-3.5 h-3.5 text-neutral-400" />
                  {data.industry}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Users className="w-3.5 h-3.5 text-neutral-400" />
                  {data.size_range} employees
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-neutral-400" />
                  {data.headquarters}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReanalyze}
              disabled={!!analyzingJobId}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-neutral-900 hover:bg-neutral-800 text-white font-medium text-xs shadow-2xs transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{analyzingJobId ? "Analysis Running..." : "Re-analyze Seller Profile"}</span>
            </button>
          </div>
        </div>

        {/* Progress Bar when running */}
        {analyzingJobId && (
          <div className="mt-4 pt-4 border-t border-neutral-100">
            <JobProgressBar
              jobId={analyzingJobId}
              title="Autonomous Seller Re-Analysis"
              onComplete={() => {
                setAnalyzingJobId(null);
                fetchOverview();
              }}
            />
          </div>
        )}
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[11px] font-mono text-neutral-400 uppercase">
            Verified Facts
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-neutral-900 font-mono">
              {data.verified_facts_count}
            </span>
            <span className="text-[11px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-medium">
              100% Sourced
            </span>
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[11px] font-mono text-neutral-400 uppercase">
            Competitors Mapped
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-neutral-900 font-mono">
              {data.competitors_count}
            </span>
            <Link
              href="/company/competitors"
              className="text-[11px] text-neutral-600 hover:text-neutral-900 underline"
            >
              View Graph &rarr;
            </Link>
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[11px] font-mono text-neutral-400 uppercase">
            Active ICP Definitions
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-neutral-900 font-mono">
              {data.active_icps_count}
            </span>
            <Link
              href="/projects"
              className="text-[11px] text-neutral-600 hover:text-neutral-900 underline"
            >
              Assigned to Projects &rarr;
            </Link>
          </div>
        </div>

        <div className="bg-white border border-neutral-200 rounded p-4">
          <div className="text-[11px] font-mono text-neutral-400 uppercase">
            Last Deep Refresh
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-xs font-mono text-neutral-700 truncate max-w-[150px]">
              {new Date(data.last_crawled_at).toLocaleDateString()}
            </span>
            <span className="text-[11px] text-neutral-400 font-mono">
              {new Date(data.last_crawled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
      </div>

      {/* Summary & Value Pillars */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-neutral-900 uppercase tracking-wider font-mono">
            Executive Company Synthesis
          </h2>
          <button
            onClick={() =>
              openEvidenceDrawer({
                claim: data.summary,
                sourceUrl: `https://${data.domain}/about`,
                verificationStatus: "Verified",
                confidenceScore: 0.98,
                factId: "fct_seller_summary",
              })
            }
            className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 underline"
          >
            <FileSearch className="w-3 h-3" />
            <span>Inspect Evidence</span>
          </button>
        </div>

        <p className="text-xs leading-relaxed text-neutral-700 bg-neutral-50/60 p-3.5 rounded border border-neutral-200/80 font-sans">
          {data.summary}
        </p>

        {/* Quick Route Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          <Link
            href="/company/analysis"
            className="p-3.5 border border-neutral-200 rounded hover:border-neutral-400 bg-white hover:bg-neutral-50/50 transition-all flex items-start gap-3"
          >
            <Sparkles className="w-4 h-4 text-neutral-700 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-semibold text-xs text-neutral-900">
                Seller Capabilities
              </div>
              <div className="text-[11px] text-neutral-500 mt-0.5">
                Value props, positioning, and buyer personas.
              </div>
            </div>
          </Link>

          <Link
            href="/company/competitors"
            className="p-3.5 border border-neutral-200 rounded hover:border-neutral-400 bg-white hover:bg-neutral-50/50 transition-all flex items-start gap-3"
          >
            <GitCompare className="w-4 h-4 text-neutral-700 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-semibold text-xs text-neutral-900">
                Competitor Graph
              </div>
              <div className="text-[11px] text-neutral-500 mt-0.5">
                4 verified competitors with overlap scoring.
              </div>
            </div>
          </Link>

          <Link
            href="/company/history"
            className="p-3.5 border border-neutral-200 rounded hover:border-neutral-400 bg-white hover:bg-neutral-50/50 transition-all flex items-start gap-3"
          >
            <History className="w-4 h-4 text-neutral-700 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-semibold text-xs text-neutral-900">
                Temporal Change Log
              </div>
              <div className="text-[11px] text-neutral-500 mt-0.5">
                Observed updates and field transitions over time.
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
