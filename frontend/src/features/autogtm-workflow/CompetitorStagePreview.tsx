"use client";

import React from "react";
import { useCockpit } from "@/features/cockpit/CockpitContext";
import { ExternalLink } from "lucide-react";

export function CompetitorStagePreview() {
  const { competitors, setSelectedCompetitor } = useCockpit();

  const previewCompetitors = competitors.slice(0, 4);
  const remainingCount = Math.max(0, competitors.length - 4);

  return (
    <div className="mt-2 space-y-1.5">
      <div className="space-y-1">
        {previewCompetitors.map((comp) => (
          <button
            key={comp.domain}
            onClick={() => setSelectedCompetitor(comp)}
            className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md bg-gx-surface hover:bg-gx-surface-hover border border-gx-border text-[11px] text-gx-ink transition-colors group"
          >
            <span className="truncate font-mono">{comp.name}</span>
            <span className="text-[10px] text-gx-ink-muted group-hover:text-gx-primary flex items-center gap-1">
              <span>View overlap</span>
              <ExternalLink className="w-2.5 h-2.5" />
            </span>
          </button>
        ))}
      </div>

      {remainingCount > 0 && (
        <button
          onClick={() => setSelectedCompetitor(competitors[0])}
          className="w-full text-center py-1 text-[11px] text-gx-ink-muted hover:text-gx-primary transition-colors font-medium"
        >
          +{remainingCount} more competitors &middot; View breakdown
        </button>
      )}
    </div>
  );
}
