"use client";

import React from "react";
import { useCockpit } from "./CockpitContext";
import { X, ExternalLink, ShieldCheck, CheckCircle2, Zap } from "lucide-react";

export function CompetitorModal() {
  const { selectedCompetitor, setSelectedCompetitor } = useCockpit();

  if (!selectedCompetitor) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in-50 duration-150">
      <div className="bg-[#121622] border border-[#232a3c] rounded-xl max-w-lg w-full p-6 text-slate-200 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#1e2434]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-[#1a2030] border border-[#273249] flex items-center justify-center font-bold text-xs text-white">
              {selectedCompetitor.name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="font-semibold text-white text-sm flex items-center gap-1.5">
                <span>{selectedCompetitor.name}</span>
                <span className="text-slate-400 font-mono text-xs">({selectedCompetitor.domain})</span>
              </div>
              <div className="text-xs text-slate-400">
                Market Overlap: {selectedCompetitor.overlap}
              </div>
            </div>
          </div>
          <button
            onClick={() => setSelectedCompetitor(null)}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-[#1a2030]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Why GrowX Wins / Advantage */}
        <div className="bg-[#151c2a] border border-[#22314d] rounded-lg p-3.5 space-y-1.5">
          <div className="text-[11px] uppercase font-semibold text-emerald-400 tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>GrowX Advantage Over {selectedCompetitor.name}</span>
          </div>
          <p className="text-xs text-slate-200 leading-relaxed">
            {selectedCompetitor.ourAdvantage}
          </p>
        </div>

        {/* Shared capabilities */}
        <div className="space-y-2">
          <div className="text-[11px] uppercase font-semibold text-slate-400 tracking-wider">
            Shared Capabilities
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCompetitor.sharedFeatures.map((feat) => (
              <div
                key={feat}
                className="px-2.5 py-1 bg-[#171c28] border border-[#252c3c] rounded text-xs text-slate-300 flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3 h-3 text-slate-400" />
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-[#1e2434] flex items-center justify-between text-xs">
          <a
            href={`https://${selectedCompetitor.domain}`}
            target="_blank"
            rel="noreferrer"
            className="text-slate-400 hover:text-white flex items-center gap-1 underline"
          >
            <span>Visit {selectedCompetitor.domain}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <button
            onClick={() => setSelectedCompetitor(null)}
            className="px-4 py-1.5 bg-[#1e2436] hover:bg-[#283149] text-white font-medium rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
