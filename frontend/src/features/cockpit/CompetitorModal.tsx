"use client";

import React from "react";
import { useCockpit } from "./CockpitContext";
import { X, ExternalLink, ShieldCheck, CheckCircle2 } from "lucide-react";

export function CompetitorModal() {
  const { selectedCompetitor, setSelectedCompetitor } = useCockpit();

  if (!selectedCompetitor) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in-50 duration-150">
      <div className="bg-[#FFFFFF] border border-[#DDE2E8] rounded-xl max-w-lg w-full p-6 text-[#111318] shadow-xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#DDE2E8]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-[#F1F3F6] border border-[#DDE2E8] flex items-center justify-center font-bold text-xs text-[#111318]">
              {selectedCompetitor.name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="font-semibold text-[#111318] text-sm flex items-center gap-1.5">
                <span>{selectedCompetitor.name}</span>
                <span className="text-[#818A97] font-mono text-xs">({selectedCompetitor.domain})</span>
              </div>
              <div className="text-xs text-[#4D5663]">
                Market Overlap: {selectedCompetitor.overlap}
              </div>
            </div>
          </div>
          <button
            onClick={() => setSelectedCompetitor(null)}
            className="text-[#818A97] hover:text-[#111318] p-1 rounded hover:bg-[#F1F3F6] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Why GrowX Wins / Advantage */}
        <div className="bg-[#F6F7F9] border border-[#DDE2E8] rounded-lg p-3.5 space-y-1.5">
          <div className="text-[11px] uppercase font-semibold text-[#16825D] tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#16825D]" />
            <span>GrowX Advantage Over {selectedCompetitor.name}</span>
          </div>
          <p className="text-xs text-[#4D5663] leading-relaxed">
            {selectedCompetitor.ourAdvantage}
          </p>
        </div>

        {/* Shared capabilities */}
        <div className="space-y-2">
          <div className="text-[11px] uppercase font-semibold text-[#818A97] tracking-wider">
            Shared Capabilities
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCompetitor.sharedFeatures.map((feat) => (
              <div
                key={feat}
                className="px-2.5 py-1 bg-[#FFFFFF] border border-[#DDE2E8] rounded text-xs text-[#4D5663] flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3 h-3 text-[#16825D]" />
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-[#DDE2E8] flex items-center justify-between text-xs">
          <a
            href={`https://${selectedCompetitor.domain}`}
            target="_blank"
            rel="noreferrer"
            className="text-[#315EF5] hover:underline flex items-center gap-1 font-medium"
          >
            <span>Visit {selectedCompetitor.domain}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <button
            onClick={() => setSelectedCompetitor(null)}
            className="px-4 py-1.5 bg-[#F1F3F6] hover:bg-[#ECEFF3] border border-[#DDE2E8] text-[#111318] font-medium rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
