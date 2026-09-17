"use client";

import React from "react";
import { useCockpit } from "@/features/cockpit/CockpitContext";

export function CampaignStagePreview() {
  const { campaigns, activeCampaignId, setActiveCampaignId } = useCockpit();

  const activeCampaign = campaigns.find((c) => c.id === activeCampaignId) || campaigns[0];
  const secondaryCampaign = campaigns.find((c) => c.id !== activeCampaignId) || campaigns[1];
  const remainingCount = Math.max(0, campaigns.length - 2);

  return (
    <div className="mt-2 space-y-1">
      {/* Selected Campaign Row */}
      <button
        onClick={() => setActiveCampaignId(activeCampaign.id)}
        data-selected="true"
        className="w-full px-2.5 py-2 rounded-md bg-gx-primary-soft border border-gx-primary-border text-left transition-colors flex items-center justify-between"
      >
        <div className="min-w-0 pr-2">
          <div className="text-xs font-semibold text-gx-ink truncate">
            {activeCampaign.name}
          </div>
          <div className="text-[11px] text-gx-ink-secondary">
            {activeCampaign.countLabel} target accounts
          </div>
        </div>
        <span className="text-[11px] font-mono font-semibold text-gx-primary">
          {activeCampaign.countLabel}
        </span>
      </button>

      {/* Secondary Campaign Row */}
      {secondaryCampaign && (
        <button
          onClick={() => setActiveCampaignId(secondaryCampaign.id)}
          data-selected="false"
          className="w-full px-2.5 py-2 rounded-md bg-transparent hover:bg-gx-surface-soft border border-transparent text-left transition-colors flex items-center justify-between group"
        >
          <div className="min-w-0 pr-2">
            <div className="text-xs font-medium text-gx-ink-secondary group-hover:text-gx-ink truncate">
              {secondaryCampaign.name}
            </div>
            <div className="text-[11px] text-gx-ink-muted">
              {secondaryCampaign.countLabel} target accounts
            </div>
          </div>
          <span className="text-[11px] font-mono text-gx-ink-muted">
            {secondaryCampaign.countLabel}
          </span>
        </button>
      )}

      {/* Summary of remaining campaigns */}
      {remainingCount > 0 && (
        <div className="text-[11px] text-gx-ink-muted text-center py-1">
          +{remainingCount} more campaigns
        </div>
      )}
    </div>
  );
}
