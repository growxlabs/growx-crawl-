"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Terminal } from "lucide-react";
import { useCockpit } from "@/features/cockpit/CockpitContext";
import { buildWorkflowPresentation } from "./workflow-presenter";
import { WorkflowStage } from "./WorkflowStage";

export function AutoGTMWorkflowSidebar() {
  const {
    company,
    competitors,
    campaigns,
    activeCampaignId,
    companies,
    contacts,
  } = useCockpit();

  // Enforce single expanded stage: maximumExpandedStages = 1
  // Default to Stage 3 (Define campaigns) as active work stage
  const [expandedStageOrder, setExpandedStageOrder] = useState<number | null>(3);

  const activeCampaign = campaigns.find((c) => c.id === activeCampaignId) || campaigns[0];

  const workflowView = buildWorkflowPresentation({
    company: {
      name: company.name,
      domain: company.domain,
    },
    competitorsCount: competitors.length,
    campaignsCount: campaigns.length,
    activeCampaignName: activeCampaign.name,
    activeCampaignCountLabel: activeCampaign.countLabel,
    totalAudienceLabel: "15.4K",
    companiesCount: companies.length > 0 ? 8420 : 0,
    peopleCount: contacts.length > 0 ? 14206 : 0,
    emailsCount: contacts.length > 0 ? 9718 : 0,
    activeStageOrder: 3,
  });

  const handleToggleStage = (order: number) => {
    // If clicking currently expanded stage, collapse it; otherwise expand only this stage
    setExpandedStageOrder((prev) => (prev === order ? null : order));
  };

  return (
    <aside
      className="w-72 bg-[#0c0e14] border-r border-[#1b212f] flex flex-col h-screen select-none text-slate-300 font-sans z-20 flex-shrink-0"
      aria-label="Workflow Stages"
    >
      {/* 1. Fixed Brand Header */}
      <div className="h-14 px-4 border-b border-[#1b212f] flex items-center justify-between flex-shrink-0 bg-[#0c0e14]">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-emerald-400 rounded-xs"></span>
            <span className="w-2.5 h-2.5 bg-emerald-600 rounded-xs"></span>
          </div>
          <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            growx{" "}
            <span className="text-[10px] font-medium text-slate-400 uppercase tracking-widest px-1 py-0.2 rounded bg-[#161c28] border border-[#222a3b]">
              AutoGTM
            </span>
          </span>
        </Link>
      </div>

      {/* 2. Scrollable Workflow Stages Region */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-1">
        <div className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider mb-3 px-0.5">
          Workflow Stages
        </div>

        {workflowView.stages.map((stage, idx) => (
          <WorkflowStage
            key={stage.order}
            stage={stage}
            isExpanded={expandedStageOrder === stage.order}
            onToggle={() => handleToggleStage(stage.order)}
            isLast={idx === workflowView.stages.length - 1}
          />
        ))}
      </div>

      {/* 3. Fixed Operations Footer */}
      <div className="p-3 border-t border-[#1b212f] bg-[#090b10] flex-shrink-0">
        <Link
          href="/ops"
          className="flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-slate-400 hover:text-white hover:bg-[#141824] transition-colors group"
          title="Open engineering operations console"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300" />
            <span>Operations Console</span>
          </div>
          <span className="text-[10px] font-mono text-slate-500 group-hover:text-slate-400">
            /ops
          </span>
        </Link>
      </div>
    </aside>
  );
}
