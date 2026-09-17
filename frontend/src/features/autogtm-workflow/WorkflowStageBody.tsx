"use client";

import React from "react";
import { WorkflowStageKey } from "./workflow-presenter";
import { CompanyStagePreview } from "./CompanyStagePreview";
import { CompetitorStagePreview } from "./CompetitorStagePreview";
import { CampaignStagePreview } from "./CampaignStagePreview";
import { useCockpit } from "@/features/cockpit/CockpitContext";

interface WorkflowStageBodyProps {
  stageKey: WorkflowStageKey;
  isExpanded: boolean;
}

export function WorkflowStageBody({
  stageKey,
  isExpanded,
}: WorkflowStageBodyProps) {
  const { setActiveTab } = useCockpit();

  if (!isExpanded) return null;

  return (
    <div className="pl-6 pb-1 animate-in fade-in-50 duration-150">
      {stageKey === "company_research" && <CompanyStagePreview />}
      {stageKey === "competitors" && <CompetitorStagePreview />}
      {stageKey === "campaigns" && <CampaignStagePreview />}

      {stageKey === "companies" && (
        <div className="mt-2 p-2.5 rounded-lg bg-[#F6F7F9] border border-[#DDE2E8] text-[11px] space-y-1">
          <div className="text-[#111318] font-medium">Prioritized Accounts</div>
          <p className="text-[#4D5663] leading-normal">
            Target companies filtered by verified buying momentum.
          </p>
          <button
            onClick={() => setActiveTab("companies")}
            className="text-[#315EF5] hover:text-[#244BD6] font-medium underline pt-0.5 inline-block"
          >
            Inspect accounts in workspace &rarr;
          </button>
        </div>
      )}

      {stageKey === "people" && (
        <div className="mt-2 p-2.5 rounded-lg bg-[#F6F7F9] border border-[#DDE2E8] text-[11px] space-y-1">
          <div className="text-[#111318] font-medium">Verified Decision Makers</div>
          <p className="text-[#4D5663] leading-normal">
            Identified Founders, CTOs, and Heads of Eng with direct emails.
          </p>
          <button
            onClick={() => setActiveTab("people")}
            className="text-[#315EF5] hover:text-[#244BD6] font-medium underline pt-0.5 inline-block"
          >
            Inspect personas in workspace &rarr;
          </button>
        </div>
      )}

      {stageKey === "emails" && (
        <div className="mt-2 p-2.5 rounded-lg bg-[#F6F7F9] border border-[#DDE2E8] text-[11px] space-y-1">
          <div className="text-[#111318] font-medium">Outreach Ready</div>
          <p className="text-[#4D5663] leading-normal">
            Personalized pitches prepared with live prospect proof points.
          </p>
          <button
            onClick={() => setActiveTab("emails")}
            className="text-[#315EF5] hover:text-[#244BD6] font-medium underline pt-0.5 inline-block"
          >
            Review drafts in workspace &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
