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
        className="w-full px-2.5 py-2 rounded-md bg-[#EDF2FF] border border-[#C9D5FF] text-left transition-colors flex items-center justify-between"
      >
        <div className="min-w-0 pr-2">
          <div className="text-xs font-semibold text-[#111318] truncate">
            {activeCampaign.name}
          </div>
          <div className="text-[11px] text-[#4D5663]">
            {activeCampaign.countLabel} target accounts
          </div>
        </div>
        <span className="text-[11px] font-mono font-semibold text-[#315EF5]">
          {activeCampaign.countLabel}
        </span>
      </button>

      {/* Secondary Campaign Row */}
      {secondaryCampaign && (
        <button
          onClick={() => setActiveCampaignId(secondaryCampaign.id)}
          data-selected="false"
          className="w-full px-2.5 py-2 rounded-md bg-transparent hover:bg-[#F1F3F6] border border-transparent text-left transition-colors flex items-center justify-between group"
        >
          <div className="min-w-0 pr-2">
            <div className="text-xs font-medium text-[#4D5663] group-hover:text-[#111318] truncate">
              {secondaryCampaign.name}
            </div>
            <div className="text-[11px] text-[#818A97]">
              {secondaryCampaign.countLabel} target accounts
            </div>
          </div>
          <span className="text-[11px] font-mono text-[#818A97]">
            {secondaryCampaign.countLabel}
          </span>
        </button>
      )}

      {/* Summary of remaining campaigns */}
      {remainingCount > 0 && (
        <div className="text-[11px] text-[#818A97] text-center py-1">
          +{remainingCount} more campaigns
        </div>
      )}
    </div>
  );
}
