"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Rocket,
  Zap,
  Code2,
  FileText,
  Building,
  Settings,
  ExternalLink,
  ChevronDown,
  Check,
  Terminal,
  Layers,
} from "lucide-react";
import { useCockpit, CampaignItem } from "./CockpitContext";

export function CockpitSidebar() {
  const {
    company,
    competitors,
    setSelectedCompetitor,
    campaigns,
    activeCampaignId,
    setActiveCampaignId,
  } = useCockpit();

  const [isCompanyDropdownOpen, setIsCompanyDropdownOpen] = useState(false);
  const [showAllCompetitors, setShowAllCompetitors] = useState(false);

  // Icon mapping for campaign items
  const renderCampaignIcon = (type: CampaignItem["iconType"]) => {
    switch (type) {
      case "rocket":
        return <Rocket className="w-3.5 h-3.5 text-emerald-400" />;
      case "zap":
        return <Zap className="w-3.5 h-3.5 text-amber-400" />;
      case "code":
        return <Code2 className="w-3.5 h-3.5 text-blue-400" />;
      case "file":
        return <FileText className="w-3.5 h-3.5 text-slate-400" />;
      case "building":
        return <Building className="w-3.5 h-3.5 text-purple-400" />;
      case "settings":
        return <Settings className="w-3.5 h-3.5 text-rose-400" />;
    }
  };

  const visibleCompetitors = showAllCompetitors ? competitors : competitors.slice(0, 8);

  return (
    <aside className="w-72 bg-[#0d0f15] border-r border-[#1e2330] flex flex-col h-screen select-none text-slate-300 font-sans z-20">
      {/* Brand Header */}
      <div className="h-14 px-4 border-b border-[#1e2330] flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-emerald-400 rounded-sm"></span>
            <span className="w-2.5 h-2.5 bg-emerald-600 rounded-sm"></span>
          </div>
          <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
            growx <span className="text-[11px] font-normal text-slate-400 uppercase tracking-wider">AutoGTM</span>
          </span>
        </Link>
      </div>

      {/* Main Scrollable Workflow Steps */}
      <div className="flex-1 overflow-y-auto px-3.5 py-4 space-y-6">
        {/* Step 1: Research your company */}
        <div>
          <div className="text-[11px] font-medium text-slate-400 mb-2 flex items-center gap-1.5">
            <span className="text-emerald-400 font-semibold">&#10003;</span>
            <span>step 1 &middot; Research your company</span>
          </div>

          <div className="relative">
            <button
              onClick={() => setIsCompanyDropdownOpen(!isCompanyDropdownOpen)}
              className="w-full bg-[#151923] hover:bg-[#1a202c] border border-[#23293a] rounded-lg p-2.5 text-left flex items-center justify-between transition-colors shadow-sm"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded bg-white flex items-center justify-center text-slate-900 font-bold text-[11px] flex-shrink-0 tracking-tighter shadow">
                  GX
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-white truncate">
                    {company.name}
                  </div>
                  <div className="text-[11px] text-slate-400 truncate">
                    {company.domain}
                  </div>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0 ml-1" />
            </button>

            {isCompanyDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[#151923] border border-[#23293a] rounded-lg p-1.5 shadow-xl z-30 text-xs">
                <div className="px-2 py-1 text-[10px] text-slate-400 uppercase tracking-wider">
                  Configured Companies
                </div>
                <button
                  onClick={() => setIsCompanyDropdownOpen(false)}
                  className="w-full text-left px-2 py-1.5 rounded hover:bg-[#1f2638] text-white flex items-center justify-between"
                >
                  <span>GrowX Labs Tech</span>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Step 2: Explore competitors */}
        <div>
          <div className="flex items-center justify-between text-[11px] font-medium text-slate-400 mb-2">
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-400 font-semibold">&#10003;</span>
              <span>step 2 &middot; Explore competitors</span>
            </div>
          </div>

          <div className="flex items-center justify-between mb-2 px-0.5">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Competitors {competitors.length}
            </span>
            <button
              onClick={() => setShowAllCompetitors(!showAllCompetitors)}
              title="Competitor settings"
              className="text-slate-500 hover:text-slate-300"
            >
              <Settings className="w-3 h-3" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {visibleCompetitors.map((comp) => (
              <button
                key={comp.domain}
                onClick={() => setSelectedCompetitor(comp)}
                className="flex items-center justify-between px-2 py-1.5 bg-[#141822] hover:bg-[#1b2130] border border-[#222736] hover:border-slate-600 rounded text-[11px] text-slate-300 hover:text-white transition-colors group"
              >
                <div className="flex items-center gap-1.5 truncate">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-500 group-hover:bg-emerald-400"></span>
                  <span className="truncate">{comp.name}</span>
                </div>
                <ExternalLink className="w-2.5 h-2.5 text-slate-500 group-hover:text-slate-300 opacity-0 group-hover:opacity-100 flex-shrink-0" />
              </button>
            ))}

            {!showAllCompetitors && competitors.length > 8 && (
              <button
                onClick={() => setShowAllCompetitors(true)}
                className="col-span-2 text-center py-1 text-[11px] text-slate-400 hover:text-slate-200 bg-[#121620] border border-[#1e2433] rounded hover:bg-[#181d2a] transition-colors"
              >
                +{competitors.length - 8} more
              </button>
            )}
          </div>
        </div>

        {/* Step 3: Define campaigns */}
        <div>
          <div className="flex items-center justify-between text-[11px] font-medium text-slate-400 mb-2">
            <div className="flex items-center gap-1.5">
              <span className="text-emerald-400 font-semibold">&#10003;</span>
              <span>step 3 &middot; Define campaigns</span>
            </div>
          </div>

          <div className="flex items-center justify-between mb-2 px-0.5">
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Campaigns {campaigns.length}
            </span>
            <Settings className="w-3 h-3 text-slate-500" />
          </div>

          <div className="space-y-1.5">
            {campaigns.map((camp) => {
              const isActive = camp.id === activeCampaignId;
              return (
                <button
                  key={camp.id}
                  onClick={() => setActiveCampaignId(camp.id)}
                  className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs transition-all ${
                    isActive
                      ? "bg-[#181d29] text-white border border-[#2b3346] shadow-sm font-medium"
                      : "text-slate-300 hover:bg-[#141822] hover:text-white border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    {renderCampaignIcon(camp.iconType)}
                    <span className="truncate">{camp.name}</span>
                  </div>
                  <span
                    className={`text-[11px] px-1.5 py-0.5 rounded font-mono ${
                      isActive
                        ? "bg-[#22293b] text-slate-200"
                        : "text-slate-500"
                    }`}
                  >
                    {camp.countLabel}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Completed steps below */}
        <div className="pt-2 border-t border-[#1e2330] space-y-2 text-[11px] text-slate-400">
          <div className="flex items-center gap-2 px-1">
            <span className="text-emerald-400 font-semibold">&#10003;</span>
            <span>step 4 &middot; Find potential customers</span>
          </div>
          <div className="flex items-center gap-2 px-1">
            <span className="text-emerald-400 font-semibold">&#10003;</span>
            <span>step 5 &middot; Find decision makers</span>
          </div>
          <div className="flex items-center gap-2 px-1">
            <span className="text-emerald-400 font-semibold">&#10003;</span>
            <span>step 6 &middot; Write emails</span>
          </div>
        </div>
      </div>

      {/* Footer / Operations Console link */}
      <div className="p-3 border-t border-[#1e2330] bg-[#0b0d13]">
        <Link
          href="/ops"
          className="flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-slate-400 hover:text-white hover:bg-[#151923] transition-colors"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-slate-400" />
            <span>Operations Console</span>
          </div>
          <span className="text-[10px] font-mono text-slate-500">/ops</span>
        </Link>
      </div>
    </aside>
  );
}
