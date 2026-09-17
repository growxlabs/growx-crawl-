"use client";

import React, { useState } from "react";
import { apiFetch } from "@/lib/api/client";
import {
  Settings,
  Database,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Server,
} from "lucide-react";

export default function SettingsPage() {
  const [seeding, setSeeding] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSeed = async () => {
    setSeeding(true);
    setMessage(null);
    setError(null);
    try {
      const res = await apiFetch<any>("/v1/seed", { method: "POST" });
      setMessage(
        `Canonical environment successfully seeded: ${res.seller_company_id}, ${res.project_id}, ${res.prospects_count} prospects.`
      );
    } catch (err: any) {
      setError(err?.message || "Failed to seed environment.");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="space-y-6 text-xs text-neutral-800">
      {/* Header */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex items-center gap-2 mb-1">
          <Settings className="w-4 h-4 text-neutral-800" />
          <h1 className="text-base font-bold text-neutral-900">
            Platform Engine Settings
          </h1>
        </div>
        <p className="text-xs text-neutral-500">
          Configure backend API endpoints, crawler concurrency, and canonical environment state.
        </p>
      </div>

      {/* Backend Engine Status Card */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
          Authoritative Backend Engine
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 space-y-1">
            <span className="text-[10px] font-mono uppercase text-neutral-400">
              API Host URL
            </span>
            <div className="font-mono text-xs font-semibold text-neutral-900">
              http://127.0.0.1:7411
            </div>
            <div className="text-[11px] text-neutral-500">
              FastAPI authoritative REST & SSE endpoint.
            </div>
          </div>

          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 space-y-1">
            <span className="text-[10px] font-mono uppercase text-neutral-400">
              Database Persistence
            </span>
            <div className="font-mono text-xs font-semibold text-neutral-900">
              SQLite (GrowX Canonical DB)
            </div>
            <div className="text-[11px] text-neutral-500">
              Dual-dialect SQLite / PostgreSQL schema active.
            </div>
          </div>
        </div>
      </div>

      {/* Environment Reset & Demo Seed */}
      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
            Canonical Demonstration Environment
          </h2>
          <p className="text-xs text-neutral-500 mt-0.5">
            Populate company profiles, target customer profiles, and prioritized prospects.
          </p>
        </div>

        {message && (
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-emerald-800 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div>
          <button
            onClick={handleSeed}
            disabled={seeding}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 shadow-2xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${seeding ? "animate-spin" : ""}`} />
            <span>{seeding ? "Seeding Database..." : "Seed Canonical Data"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
