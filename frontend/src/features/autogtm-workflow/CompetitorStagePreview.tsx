"use client";

import React from "react";
import { useCockpit } from "@/features/cockpit/CockpitContext";
import { ExternalLink } from "lucide-react";

export function CompetitorStagePreview() {
  const { competitors, setSelectedCompetitor } = useCockpit();

  const previewCompetitors = competitors.slice(0, 4);
  const remainingCount = Math.max(0, competitors.length - 4);

  return (
    <div className="mt-2.5 space-y-1.5">
      <div className="space-y-1">
        {previewCompetitors.map((comp) => (
          <button
            key={comp.domain}
            onClick={() => setSelectedCompetitor(comp)}
            className="w-full flex items-center justify-between px-2.5 py-1.5 rounded bg-[#141824] hover:bg-[#1b2130] border border-[#202738] text-[11px] text-slate-300 hover:text-white transition-colors group"
          >
            <span className="truncate font-mono">{comp.name}</span>
            <span className="text-[10px] text-slate-500 group-hover:text-slate-300 flex items-center gap-1">
              <span>View overlap</span>
              <ExternalLink className="w-2.5 h-2.5" />
            </span>
          </button>
        ))}
      </div>

      {remainingCount > 0 && (
        <button
          onClick={() => setSelectedCompetitor(competitors[0])}
          className="w-full text-center py-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
        >
          +{remainingCount} more competitors &middot; View breakdown
        </button>
      )}
    </div>
  );
}
