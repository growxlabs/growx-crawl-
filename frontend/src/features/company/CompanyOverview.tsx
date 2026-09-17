"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2,
  Globe,
  MapPin,
  Users,
  CheckCircle2,
  FileSearch,
  ExternalLink,
  ArrowRight,
  ShieldCheck,
  Briefcase,
  Layers,
  Sparkles,
} from "lucide-react";
import {
  getSellerOverview,
  SellerOverview as SellerOverviewType,
} from "@/lib/api/company";
import { useEvidence } from "@/components/inspector/EvidenceContext";

export function CompanyOverview() {
  const [overview, setOverview] = useState<SellerOverviewType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    setLoading(true);
    getSellerOverview()
      .then((data) => setOverview(data))
      .catch((err) => console.error("Failed to load seller overview", err))
      .finally(() => setLoading(false));
  }, []);

  const data = overview || {
    id: "cmp_seller_growxlabs",
    name: "GrowxLabs",
    company_name: "GrowxLabs",
    domain: "growxlabs.tech",
    industry: "Enterprise AI & Autonomous Software",
    size_range: "50-200",
    headquarters: "San Francisco, CA",
    summary: "AI-native software and AI engineering for enterprises.",
    verified_facts_count: 38,
    active_icps_count: 2,
    competitors_count: 4,
    last_crawled_at: new Date().toISOString(),
  };

  const companyName = data.name || data.company_name || "GrowxLabs";

  return (
    <div className="max-w-4xl space-y-8 py-2">
      {/* Page Header */}
      <div className="border-b border-neutral-200 pb-5">
        <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
          Overview
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          How GrowX understands your company identity, capabilities, and target audience.
        </p>
      </div>

      {/* Section 1: Your Company */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          Your company
        </div>
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold text-neutral-900 tracking-tight">
                {companyName}
              </h2>
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                <span>Verified profile</span>
              </span>
            </div>
            <div className="mt-1 flex items-center gap-3 text-xs text-neutral-500">
              <a
                href={`https://${data.domain}`}
                target="_blank"
                rel="noreferrer"
                className="text-neutral-700 hover:text-neutral-900 underline flex items-center gap-1"
              >
                <span>{data.domain}</span>
                <ExternalLink className="w-3 h-3 text-neutral-400" />
              </a>
              <span>•</span>
              <span>{data.headquarters}</span>
              <span>•</span>
              <span>{data.size_range} team members</span>
            </div>
          </div>

          <button
            onClick={() =>
              openEvidenceDrawer({
                claim: `${companyName} (${data.domain}): ${data.headquarters}, ${data.size_range} employees.`,
                sourceUrl: `https://${data.domain}/about`,
                verificationStatus: "Verified",
                confidenceScore: 0.99,
              })
            }
            className="text-xs text-neutral-500 hover:text-neutral-900 underline inline-flex items-center gap-1 self-start sm:self-auto"
          >
            <FileSearch className="w-3.5 h-3.5 text-neutral-400" />
            <span>View sources</span>
          </button>
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* Section 2: What you do */}
      <div className="space-y-2">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          What you do
        </div>
        <div className="flex items-start justify-between gap-4">
          <p className="text-base text-neutral-800 leading-relaxed font-medium">
            AI-native software and AI engineering for enterprises.
          </p>
          <button
            onClick={() =>
              openEvidenceDrawer({
                claim: "AI-native software and AI engineering for enterprises.",
                sourceUrl: `https://${data.domain}`,
                verificationStatus: "Verified",
                confidenceScore: 0.98,
              })
            }
            className="text-xs text-neutral-500 hover:text-neutral-900 underline inline-flex items-center gap-1 flex-shrink-0 pt-0.5"
          >
            <FileSearch className="w-3.5 h-3.5 text-neutral-400" />
            <span>View sources</span>
          </button>
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* Section 3: What you help with */}
      <div className="space-y-3">
        <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
          What you help with
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            {
              title: "AI Engineering",
              description: "Custom enterprise LLM systems, agent workflows, and production integrations.",
            },
            {
              title: "Internal Platforms",
              description: "Bespoke operating tools and unified intelligence platforms.",
            },
            {
              title: "Workflow Automation",
              description: "End-to-end automation of data capture, evaluation, and operations.",
            },
            {
              title: "Enterprise Integrations",
              description: "Connecting modern AI infrastructure with existing legacy ERP & CRM systems.",
            },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-4 bg-white border border-neutral-200 rounded-md space-y-1 hover:border-neutral-300 transition-colors"
            >
              <div className="font-semibold text-xs text-neutral-900">
                {item.title}
              </div>
              <div className="text-xs text-neutral-500 leading-relaxed">
                {item.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* Section 4 & 5: Who you sell to & Likely buyers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
        {/* Who you sell to */}
        <div className="space-y-3">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Who you sell to
          </div>
          <div className="space-y-2">
            {[
              "Manufacturing",
              "Industrial Companies",
              "Legacy Enterprises",
            ].map((market, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 text-xs font-medium text-neutral-800 p-2.5 bg-neutral-50 rounded-md border border-neutral-200"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-neutral-900" />
                <span>{market}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Likely buyers */}
        <div className="space-y-3">
          <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
            Likely buyers
          </div>
          <div className="space-y-2">
            {[
              "Chief Technology Officer (CTO)",
              "Head of IT & Infrastructure",
              "Head of Operations",
              "VP / Director of Digital Transformation",
            ].map((buyer, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 text-xs font-medium text-neutral-800 p-2.5 bg-neutral-50 rounded-md border border-neutral-200"
              >
                <Briefcase className="w-3.5 h-3.5 text-neutral-500" />
                <span>{buyer}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <hr className="border-neutral-200" />

      {/* Quick Navigation to other Company views */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-4 text-xs text-neutral-600">
        <Link
          href="/company/positioning"
          className="inline-flex items-center gap-1.5 hover:text-neutral-900 underline font-medium"
        >
          <span>Explore company positioning</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
        <Link
          href="/company/competitors"
          className="inline-flex items-center gap-1.5 hover:text-neutral-900 underline font-medium"
        >
          <span>View market competitors</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
        <Link
          href="/company/changes"
          className="inline-flex items-center gap-1.5 hover:text-neutral-900 underline font-medium"
        >
          <span>View recent changes</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}
