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
        <div className="mt-2.5 p-2 rounded-lg bg-[#141824] border border-[#212738] text-[11px] space-y-1">
          <div className="text-slate-300 font-medium">Prioritized Accounts</div>
          <p className="text-slate-400 leading-normal">
            Target companies filtered by verified buying momentum.
          </p>
          <button
            onClick={() => setActiveTab("companies")}
            className="text-emerald-400 hover:text-emerald-300 underline pt-0.5 inline-block"
          >
            Inspect accounts in workspace &rarr;
          </button>
        </div>
      )}

      {stageKey === "people" && (
        <div className="mt-2.5 p-2 rounded-lg bg-[#141824] border border-[#212738] text-[11px] space-y-1">
          <div className="text-slate-300 font-medium">Verified Decision Makers</div>
          <p className="text-slate-400 leading-normal">
            Identified Founders, CTOs, and Heads of Eng with direct emails.
          </p>
          <button
            onClick={() => setActiveTab("people")}
            className="text-emerald-400 hover:text-emerald-300 underline pt-0.5 inline-block"
          >
            Inspect personas in workspace &rarr;
          </button>
        </div>
      )}

      {stageKey === "emails" && (
        <div className="mt-2.5 p-2 rounded-lg bg-[#141824] border border-[#212738] text-[11px] space-y-1">
          <div className="text-slate-300 font-medium">Outreach Ready</div>
          <p className="text-slate-400 leading-normal">
            Personalized pitches prepared with live prospect proof points.
          </p>
          <button
            onClick={() => setActiveTab("emails")}
            className="text-emerald-400 hover:text-emerald-300 underline pt-0.5 inline-block"
          >
            Review drafts in workspace &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
