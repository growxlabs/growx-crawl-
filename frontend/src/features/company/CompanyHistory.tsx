"use client";

import React, { useEffect, useState } from "react";
import { getSellerHistory, CompanyEvent } from "@/lib/api/company";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  History,
  ArrowRight,
  Clock,
  FileSearch,
  CheckCircle2,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { StatusBadge } from "@/components/status/StatusBadge";

export function CompanyHistory() {
  const [events, setEvents] = useState<CompanyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    getSellerHistory()
      .then((data) => setEvents(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const defaultEvents: CompanyEvent[] = [
    {
      event_id: "evt_001",
      timestamp: new Date(Date.now() - 3600000 * 4).toISOString(),
      event_type: "fact_verified",
      field_name: "headquarters",
      previous_value: null,
      current_value: "San Francisco, CA",
      summary: "Headquarters location canonicalized from official legal contact footer.",
      evidence_id: "evi_hq_sf",
    },
    {
      event_id: "evt_002",
      timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
      event_type: "fact_updated",
      field_name: "employee_count_range",
      previous_value: "10-50",
      current_value: "50-200",
      summary: "Employee count range updated after team page growth detection.",
      evidence_id: "evi_emp_growth",
    },
    {
      event_id: "evt_003",
      timestamp: new Date(Date.now() - 3600000 * 72).toISOString(),
      event_type: "competitor_added",
      field_name: "competitor_graph",
      previous_value: null,
      current_value: "Clay (clay.com)",
      summary: "Added adjacent competitor node based on enrichment workflow overlap.",
      evidence_id: "evi_comp_clay",
    },
    {
      event_id: "evt_004",
      timestamp: new Date(Date.now() - 3600000 * 120).toISOString(),
      event_type: "icp_version_published",
      field_name: "icp_specification",
      previous_value: "v1.0-draft",
      current_value: "v1.1-active",
      summary: "Activated US Mid-Market B2B SaaS ICP profile with stricter revenue filters.",
      evidence_id: "evi_icp_v11",
    },
  ];

  const list = events.length > 0 ? events : defaultEvents;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-neutral-800" />
            <h1 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Temporal Intelligence & Fact History
            </h1>
          </div>
          <span className="text-xs font-mono text-neutral-500">
            {list.length} Chronological Events Recorded
          </span>
        </div>
        <p className="text-xs text-neutral-500 mt-1">
          Auditable timeline of observed fact mutations, schema transitions, verified
          proof updates, and competitive relationship evolutions.
        </p>
      </div>

      {/* Timeline Stream */}
      <div className="bg-white border border-neutral-200 rounded p-6">
        <div className="relative border-l border-neutral-200 ml-3.5 pl-6 space-y-8">
          {list.map((evt, idx) => (
            <div key={evt.event_id || idx} className="relative group">
              {/* Timeline Bullet Node */}
              <div className="absolute -left-[31px] top-1.5 w-3 h-3 rounded-full bg-neutral-900 border-2 border-white shadow-xs group-hover:scale-125 transition-transform" />

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-neutral-900">
                    {evt.field_name || evt.event || "Fact Update"}
                  </span>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-600 border border-neutral-200">
                    {(evt.event_type || evt.event || "update").replace(/_/g, " ")}
                  </span>
                </div>
                <div className="flex items-center gap-1 text-[11px] font-mono text-neutral-400">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(evt.timestamp).toLocaleString()}</span>
                </div>
              </div>

              {/* Transition pill */}
              <div className="my-2 flex items-center gap-2 text-xs font-mono">
                {evt.previous_value && (
                  <>
                    <span className="px-2 py-0.5 rounded bg-neutral-100 text-neutral-500 line-through">
                      {String(evt.previous_value)}
                    </span>
                    <ArrowRight className="w-3 h-3 text-neutral-400 flex-shrink-0" />
                  </>
                )}
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                  {String(evt.current_value || evt.change || "Verified")}
                </span>
              </div>

              {/* Summary note */}
              <p className="text-xs text-neutral-600 leading-relaxed font-sans">
                {evt.summary || evt.change || "Canonical intelligence update recorded."}
              </p>

              {/* Evidence Inspector Link */}
              <div className="mt-2 flex items-center justify-between text-[11px]">
                <button
                  onClick={() =>
                    openEvidenceDrawer({
                      claim: evt.summary,
                      evidenceId: evt.evidence_id,
                      verificationStatus: "Verified",
                    })
                  }
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 underline"
                >
                  <FileSearch className="w-3 h-3" />
                  <span>Inspect Supporting Evidence</span>
                </button>
                <span className="font-mono text-[10px] text-neutral-400">
                  {evt.event_id}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
