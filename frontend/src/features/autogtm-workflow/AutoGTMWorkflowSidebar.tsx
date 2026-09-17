"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Check,
  ChevronDown,
  ExternalLink,
  Settings,
  Terminal,
  Target,
  Zap,
  Code2,
  FileText,
  Building,
  Wrench,
  Clock,
} from "lucide-react";
import { useCockpit, CampaignItem } from "@/features/cockpit/CockpitContext";

export function AutoGTMWorkflowSidebar() {
  const {
    company,
    competitors,
    setSelectedCompetitor,
    campaigns,
    activeCampaignId,
    setActiveCampaignId,
    activeTab,
    setActiveTab,
  } = useCockpit();

  const [isCompanyDropdownOpen, setIsCompanyDropdownOpen] = useState(false);
  const [showAllCompetitors, setShowAllCompetitors] = useState(false);

  // Render clean, non-rainbow icons for campaign items
  const renderCampaignIcon = (type: CampaignItem["iconType"], isSelected: boolean) => {
    const iconClass = `w-3.5 h-3.5 flex-shrink-0 ${
      isSelected ? "text-[#315EF5]" : "text-[#818A97]"
    }`;

    switch (type) {
      case "rocket":
        return <Target className={iconClass} />;
      case "zap":
        return <Zap className={iconClass} />;
      case "code":
        return <Code2 className={iconClass} />;
      case "file":
        return <FileText className={iconClass} />;
      case "building":
        return <Building className={iconClass} />;
      case "settings":
      default:
        return <Wrench className={iconClass} />;
    }
  };

  const visibleCompetitors = showAllCompetitors ? competitors : competitors.slice(0, 8);

  return (
    <aside
      className="w-72 bg-[#FFFFFF] border-r border-[#DDE2E8] flex flex-col h-screen select-none text-[#111318] font-sans z-20 flex-shrink-0"
      aria-label="GrowX AutoGTM Operating Panel"
    >
      {/* 1. Fixed Brand Header */}
      <div className="h-14 px-4 border-b border-[#DDE2E8] flex items-center justify-between flex-shrink-0 bg-[#FFFFFF]">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-[#315EF5] rounded-xs"></span>
            <span className="w-2.5 h-2.5 bg-[#5B80F7] rounded-xs"></span>
          </div>
          <span className="font-bold text-base tracking-tight text-[#111318] flex items-center gap-1.5">
            growx{" "}
            <span className="text-[10px] font-semibold text-[#4D5663] uppercase tracking-widest px-1.5 py-0.5 rounded bg-[#F1F3F6] border border-[#DDE2E8]">
              AutoGTM
            </span>
          </span>
        </Link>
      </div>

      {/* 2. Scrollable Operating Panel Region */}
      <div className="flex-1 overflow-y-auto px-3.5 py-3.5 space-y-4 bg-[#FFFFFF]">
        {/* Step 1: Research your company */}
        <div>
          <div className="text-[11px] font-medium text-[#4D5663] mb-1.5 flex items-center gap-1.5">
            <Check className="w-3 h-3 text-[#16825D] stroke-[2.5]" />
            <span>step 1 &middot; Research your company</span>
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setIsCompanyDropdownOpen(!isCompanyDropdownOpen)}
              className="w-full bg-[#FFFFFF] hover:bg-[#F6F7F9] border border-[#DDE2E8] rounded-lg p-2 text-left flex items-center justify-between transition-colors shadow-2xs"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-7 h-7 rounded bg-[#315EF5] flex items-center justify-center text-white font-bold text-xs flex-shrink-0 tracking-tighter shadow-2xs">
                  GX
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-[#111318] truncate">
                    {company.name}
                  </div>
                  <div className="text-[11px] text-[#818A97] font-mono truncate">
                    {company.domain}
                  </div>
                </div>
              </div>
              <ChevronDown
                className={`w-3.5 h-3.5 text-[#818A97] flex-shrink-0 ml-1 transition-transform ${
                  isCompanyDropdownOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {isCompanyDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[#FFFFFF] border border-[#DDE2E8] rounded-lg p-1.5 shadow-lg z-30 text-xs">
                <div className="px-2 py-1 text-[10px] text-[#818A97] uppercase tracking-wider font-semibold">
                  Configured Companies
                </div>
                <button
                  type="button"
                  onClick={() => setIsCompanyDropdownOpen(false)}
                  className="w-full text-left px-2 py-1.5 rounded hover:bg-[#F1F3F6] text-[#111318] flex items-center justify-between"
                >
                  <span className="font-medium">GrowX Labs Tech</span>
                  <Check className="w-3.5 h-3.5 text-[#16825D]" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Explore competitors */}
        <div>
          <div className="text-[11px] font-medium text-[#4D5663] mb-1 flex items-center gap-1.5">
            <Check className="w-3 h-3 text-[#16825D] stroke-[2.5]" />
            <span>step 2 &middot; Explore competitors</span>
          </div>

          <div className="flex items-center justify-between mb-1.5 px-0.5">
            <span className="text-[10px] uppercase font-semibold text-[#818A97] tracking-wider">
              Competitors {competitors.length}
            </span>
            <button
              type="button"
              onClick={() => setShowAllCompetitors(!showAllCompetitors)}
              title="Toggle competitor view"
              className="text-[#818A97] hover:text-[#111318] transition-colors"
            >
              <Settings className="w-3 h-3" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {visibleCompetitors.map((comp) => {
              const initial = comp.name.charAt(0).toUpperCase();
              return (
                <button
                  key={comp.domain}
                  type="button"
                  onClick={() => setSelectedCompetitor(comp)}
                  className="flex items-center justify-between px-2 py-1 bg-[#FFFFFF] hover:bg-[#F6F7F9] border border-[#DDE2E8] hover:border-[#BFC7D1] rounded text-[11px] text-[#111318] transition-colors group shadow-2xs text-left min-w-0"
                  title={`${comp.name} (${comp.domain})`}
                >
                  <div className="flex items-center gap-1.5 min-w-0 truncate">
                    <span className="w-3.5 h-3.5 rounded bg-[#F1F3F6] border border-[#DDE2E8] text-[9px] font-bold flex items-center justify-center text-[#4D5663] flex-shrink-0">
                      {initial}
                    </span>
                    <span className="truncate font-mono text-[11px]">{comp.name}</span>
                  </div>
                  <ExternalLink className="w-2.5 h-2.5 text-[#818A97] group-hover:text-[#315EF5] flex-shrink-0 ml-1 opacity-70 group-hover:opacity-100" />
                </button>
              );
            })}

            {!showAllCompetitors && competitors.length > 8 && (
              <button
                type="button"
                onClick={() => setShowAllCompetitors(true)}
                className="col-span-2 text-center py-1 text-[11px] text-[#4D5663] hover:text-[#111318] bg-[#F6F7F9] border border-[#DDE2E8] rounded hover:bg-[#ECEFF3] transition-colors font-medium"
              >
                +{competitors.length - 8} more
              </button>
            )}
          </div>
        </div>

        {/* Step 3: Define campaigns */}
        <div>
          <div className="text-[11px] font-medium text-[#4D5663] mb-1 flex items-center gap-1.5">
            <Check className="w-3 h-3 text-[#16825D] stroke-[2.5]" />
            <span>step 3 &middot; Define campaigns</span>
          </div>

          <div className="flex items-center justify-between mb-1.5 px-0.5">
            <span className="text-[10px] uppercase font-semibold text-[#818A97] tracking-wider">
              Campaigns {campaigns.length}
            </span>
            <Settings className="w-3 h-3 text-[#818A97]" />
          </div>

          <div className="space-y-1">
            {campaigns.map((camp) => {
              const isSelected = camp.id === activeCampaignId;
              return (
                <button
                  key={camp.id}
                  type="button"
                  data-selected={isSelected ? "true" : "false"}
                  onClick={() => setActiveCampaignId(camp.id)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-all ${
                    isSelected
                      ? "bg-[#EDF2FF] text-[#111318] border border-[#C9D5FF] font-semibold shadow-2xs"
                      : "text-[#4D5663] hover:text-[#111318] hover:bg-[#F1F3F6] border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate pr-2">
                    {renderCampaignIcon(camp.iconType, isSelected)}
                    <span className="truncate">{camp.name}</span>
                  </div>
                  <span
                    className={`text-[11px] font-mono flex-shrink-0 flex items-center gap-1 ${
                      isSelected
                        ? "text-[#315EF5] font-semibold"
                        : "text-[#818A97]"
                    }`}
                  >
                    {isSelected && <Clock className="w-2.5 h-2.5 text-[#315EF5]" />}
                    {camp.countLabel}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Completed Steps Below (4, 5, 6) - Clicking switches workspace tab dynamically */}
        <div className="pt-3 border-t border-[#E9ECF0] space-y-2 text-[11px]">
          <button
            type="button"
            onClick={() => setActiveTab("companies")}
            className={`w-full flex items-center gap-2 px-1 text-left transition-colors ${
              activeTab === "companies"
                ? "text-[#315EF5] font-semibold"
                : "text-[#4D5663] hover:text-[#111318]"
            }`}
          >
            <Check className="w-3 h-3 text-[#16825D] stroke-[2.5]" />
            <span>step 4 &middot; Find potential customers</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("people")}
            className={`w-full flex items-center gap-2 px-1 text-left transition-colors ${
              activeTab === "people"
                ? "text-[#315EF5] font-semibold"
                : "text-[#4D5663] hover:text-[#111318]"
            }`}
          >
            <Check className="w-3 h-3 text-[#16825D] stroke-[2.5]" />
            <span>step 5 &middot; Find decision makers</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("emails")}
            className={`w-full flex items-center gap-2 px-1 text-left transition-colors ${
              activeTab === "emails"
                ? "text-[#315EF5] font-semibold"
                : "text-[#4D5663] hover:text-[#111318]"
            }`}
          >
            <Check className="w-3 h-3 text-[#16825D] stroke-[2.5]" />
            <span>step 6 &middot; Write emails</span>
          </button>
        </div>
      </div>

      {/* 3. Fixed Operations Footer */}
      <div className="p-3 border-t border-[#DDE2E8] bg-[#F6F7F9] flex-shrink-0">
        <Link
          href="/ops"
          className="flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-[#4D5663] hover:text-[#111318] hover:bg-[#ECEFF3] transition-colors group"
          title="Open engineering operations console"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-[#818A97] group-hover:text-[#4D5663]" />
            <span className="font-medium">Operations Console</span>
          </div>
          <span className="text-[10px] font-mono text-[#818A97]">
            /ops
          </span>
        </Link>
      </div>
    </aside>
  );
}
