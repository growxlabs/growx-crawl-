"use client";

import React from "react";
import { useCockpit } from "./CockpitContext";
import { X, ExternalLink, ShieldCheck, CheckCircle2 } from "lucide-react";

export function CompetitorModal() {
  const { selectedCompetitor, setSelectedCompetitor } = useCockpit();

  if (!selectedCompetitor) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in-50 duration-150">
      <div className="bg-gx-surface border border-gx-border rounded-xl max-w-lg w-full p-6 text-gx-ink shadow-xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-gx-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-gx-surface-soft border border-gx-border flex items-center justify-center font-bold text-xs text-gx-ink">
              {selectedCompetitor.name.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div className="font-semibold text-gx-ink text-sm flex items-center gap-1.5">
                <span>{selectedCompetitor.name}</span>
                <span className="text-gx-ink-muted font-mono text-xs">({selectedCompetitor.domain})</span>
              </div>
              <div className="text-xs text-gx-ink-secondary">
                Market Overlap: {selectedCompetitor.overlap}
              </div>
            </div>
          </div>
          <button
            onClick={() => setSelectedCompetitor(null)}
            className="text-gx-ink-muted hover:text-gx-ink p-1 rounded hover:bg-gx-surface-soft transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Why GrowX Wins / Advantage */}
        <div className="bg-gx-surface-soft border border-gx-border rounded-lg p-3.5 space-y-1.5">
          <div className="text-[11px] uppercase font-semibold text-gx-success tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-gx-success" />
            <span>GrowX Advantage Over {selectedCompetitor.name}</span>
          </div>
          <p className="text-xs text-gx-ink-secondary leading-relaxed">
            {selectedCompetitor.ourAdvantage}
          </p>
        </div>

        {/* Shared capabilities */}
        <div className="space-y-2">
          <div className="text-[11px] uppercase font-semibold text-gx-ink-muted tracking-wider">
            Shared Capabilities
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedCompetitor.sharedFeatures.map((feat) => (
              <div
                key={feat}
                className="px-2.5 py-1 bg-gx-surface border border-gx-border rounded text-xs text-gx-ink-secondary flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-3 h-3 text-gx-success" />
                <span>{feat}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="pt-3 border-t border-gx-border flex items-center justify-between text-xs">
          <a
            href={`https://${selectedCompetitor.domain}`}
            target="_blank"
            rel="noreferrer"
            className="text-gx-primary hover:underline flex items-center gap-1 font-medium"
          >
            <span>Visit {selectedCompetitor.domain}</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <button
            onClick={() => setSelectedCompetitor(null)}
            className="px-4 py-1.5 bg-gx-surface-soft hover:bg-gx-surface-hover border border-gx-border text-gx-ink font-medium rounded-md transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
