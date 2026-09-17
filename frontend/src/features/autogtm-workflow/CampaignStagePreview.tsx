"use client";

import React from "react";
import { useCockpit } from "@/features/cockpit/CockpitContext";

export function CampaignStagePreview() {
  const { campaigns, activeCampaignId, setActiveCampaignId } = useCockpit();

  const activeCampaign = campaigns.find((c) => c.id === activeCampaignId) || campaigns[0];
  const secondaryCampaign = campaigns.find((c) => c.id !== activeCampaignId) || campaigns[1];
  const remainingCount = Math.max(0, campaigns.length - 2);

  return (
    <div className="mt-2.5 space-y-1.5">
      {/* Primary / Active Campaign */}
      <button
        onClick={() => setActiveCampaignId(activeCampaign.id)}
        className="w-full p-2 rounded-lg bg-[#181e2b] border border-[#2c374d] text-left transition-colors shadow-xs flex items-center justify-between"
      >
        <div className="min-w-0 pr-2">
          <div className="text-xs font-semibold text-white truncate">
            {activeCampaign.name}
          </div>
          <div className="text-[11px] text-slate-400">
            {activeCampaign.countLabel} target accounts
          </div>
        </div>
        <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" />
      </button>

      {/* Secondary Campaign (alternative segment) */}
      {secondaryCampaign && (
        <button
          onClick={() => setActiveCampaignId(secondaryCampaign.id)}
          className="w-full p-2 rounded-lg bg-[#121622] hover:bg-[#161b29] border border-[#1e2535] text-left transition-colors flex items-center justify-between group"
        >
          <div className="min-w-0 pr-2">
            <div className="text-xs font-medium text-slate-300 group-hover:text-white truncate">
              {secondaryCampaign.name}
            </div>
            <div className="text-[11px] text-slate-500">
              {secondaryCampaign.countLabel} target accounts
            </div>
          </div>
        </button>
      )}

      {/* Summary of remaining campaigns */}
      {remainingCount > 0 && (
        <div className="text-[11px] text-slate-400 text-center py-1">
          +{remainingCount} more targeted campaigns
        </div>
      )}
    </div>
  );
}
