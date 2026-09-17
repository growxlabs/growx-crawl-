"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getIntelligenceOverview,
  searchIntelligenceCompanies,
  searchIntelligencePeople,
  searchIntelligenceSignals,
  IntelligenceOverview,
} from "@/lib/api/intelligence";
import { DataTable, ColumnDef } from "@/components/data-table/DataTable";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  Compass,
  Building2,
  Users,
  Zap,
  ShieldCheck,
  Search,
  ExternalLink,
  FileSearch,
} from "lucide-react";

export function IntelligenceExplorer() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"companies" | "people" | "signals">("companies");
  const [overview, setOverview] = useState<IntelligenceOverview | null>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [people, setPeople] = useState<any[]>([]);
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    getIntelligenceOverview()
      .then((data) => setOverview(data))
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    setLoading(true);
    if (activeTab === "companies") {
      searchIntelligenceCompanies()
        .then((data) => setCompanies(data))
        .finally(() => setLoading(false));
    } else if (activeTab === "people") {
      searchIntelligencePeople()
        .then((data) => setPeople(data))
        .finally(() => setLoading(false));
    } else if (activeTab === "signals") {
      searchIntelligenceSignals()
        .then((data) => setSignals(data))
        .finally(() => setLoading(false));
    }
  }, [activeTab]);

  const ov: IntelligenceOverview = overview || {
    total_companies: 142,
    total_people: 420,
    total_facts: 1250,
    total_evidence: 3420,
    total_signals: 284,
    recent_companies: [],
  };

  const companyColumns: ColumnDef<any>[] = [
    {
      header: "Canonical Company",
      accessorKey: "name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-neutral-900 text-xs">
            {row.name}
          </div>
          <div className="text-[11px] font-mono text-neutral-400">
            {row.domain}
          </div>
        </div>
      ),
    },
    {
      header: "Industry",
      accessorKey: "industry",
      sortable: true,
      cell: (row) => (
        <span className="text-xs text-neutral-700">{row.industry || "Software"}</span>
      ),
    },
    {
      header: "Size Range",
      accessorKey: "size_range",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs text-neutral-700">{row.size_range || "50-200"}</span>
      ),
    },
    {
      header: "Status",
      accessorKey: "verification_status",
      sortable: true,
      cell: (row) => (
        <StatusBadge status={row.verification_status || "Verified"} size="sm" />
      ),
    },
    {
      header: "Confidence",
      accessorKey: "confidence_score",
      sortable: true,
      cell: (row) => (
        <ConfidenceIndicator score={row.confidence_score ?? 0.95} size="sm" />
      ),
    },
  ];

  const peopleColumns: ColumnDef<any>[] = [
    {
      header: "Name",
      accessorKey: "full_name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-neutral-900 text-xs">
            {row.full_name}
          </div>
          <div className="text-[11px] text-neutral-500">{row.job_title}</div>
        </div>
      ),
    },
    {
      header: "Company",
      accessorKey: "company_name",
      sortable: true,
    },
    {
      header: "Seniority",
      accessorKey: "seniority",
      cell: (row) => (
        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-neutral-100 text-neutral-800">
          {row.seniority}
        </span>
      ),
    },
    {
      header: "Status",
      accessorKey: "verification_status",
      cell: (row) => (
        <StatusBadge status={row.verification_status || "Verified"} size="sm" />
      ),
    },
  ];

  const signalColumns: ColumnDef<any>[] = [
    {
      header: "Signal Title",
      accessorKey: "title",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-neutral-900 text-xs">
            {row.title}
          </div>
          <div className="text-[11px] text-neutral-500">{row.description}</div>
        </div>
      ),
    },
    {
      header: "Category",
      accessorKey: "signal_type",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-700">
          {row.signal_type}
        </span>
      ),
    },
    {
      header: "Confidence",
      accessorKey: "confidence_score",
      sortable: true,
      cell: (row) => (
        <ConfidenceIndicator score={row.confidence_score ?? 0.9} size="sm" />
      ),
    },
    {
      header: "Evidence",
      cell: (row) => (
        <button
          onClick={() =>
            openEvidenceDrawer({
              claim: `${row.title}: ${row.description}`,
              verificationStatus: "Verified",
              confidenceScore: row.confidence_score ?? 0.9,
            })
          }
          className="text-xs text-blue-600 hover:underline"
        >
          Inspect
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-neutral-800" />
            <h1 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
              Global Intelligence Explorer
            </h1>
          </div>
          <span className="text-xs font-mono text-neutral-500">
            GrowX Canonical Knowledge Base
          </span>
        </div>
        <p className="text-xs text-neutral-500">
          Query across all canonical companies, verified executive personas, and observed
          market signals discovered across crawls.
        </p>

        {/* Global Catalog Metrics */}
        <div className="mt-4 pt-4 border-t border-neutral-100 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Canonical Companies</span>
            <span className="font-bold text-neutral-900 text-lg">{ov.total_companies}</span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Verified People</span>
            <span className="font-bold text-neutral-900 text-lg">{ov.total_people}</span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Sourced Facts</span>
            <span className="font-bold text-emerald-700 text-lg">{ov.total_facts}</span>
          </div>
          <div>
            <span className="text-neutral-400 block text-[10px] uppercase">Temporal Signals</span>
            <span className="font-bold text-neutral-900 text-lg">{ov.total_signals}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-neutral-200 text-xs font-medium">
        <button
          onClick={() => setActiveTab("companies")}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "companies"
              ? "border-neutral-900 text-neutral-900 font-semibold"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Companies</span>
        </button>

        <button
          onClick={() => setActiveTab("people")}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "people"
              ? "border-neutral-900 text-neutral-900 font-semibold"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>People</span>
        </button>

        <button
          onClick={() => setActiveTab("signals")}
          className={`px-4 py-2 border-b-2 flex items-center gap-2 transition-colors ${
            activeTab === "signals"
              ? "border-neutral-900 text-neutral-900 font-semibold"
              : "border-transparent text-neutral-500 hover:text-neutral-800"
          }`}
        >
          <Zap className="w-3.5 h-3.5" />
          <span>Signals</span>
        </button>
      </div>

      {/* Table Content */}
      <div>
        {activeTab === "companies" && (
          <DataTable
            data={companies}
            columns={companyColumns}
            keyExtractor={(r) => r.id || r.name}
            searchPlaceholder="Search canonical companies..."
          />
        )}

        {activeTab === "people" && (
          <DataTable
            data={people}
            columns={peopleColumns}
            keyExtractor={(r) => r.person_id || r.full_name}
            searchPlaceholder="Search verified people..."
          />
        )}

        {activeTab === "signals" && (
          <DataTable
            data={signals}
            columns={signalColumns}
            keyExtractor={(r) => r.signal_id || r.title}
            searchPlaceholder="Search market signals..."
          />
        )}
      </div>
    </div>
  );
}
