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
  Plus,
} from "lucide-react";
import { useCockpit, CampaignItem } from "@/features/cockpit/CockpitContext";
import { AccountPopover } from "@/features/account/AccountPopover";

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
    projects,
    activeProjectId,
    selectProject,
  } = useCockpit();

  const [isCompanyDropdownOpen, setIsCompanyDropdownOpen] = useState(false);
  const [showAllCompetitors, setShowAllCompetitors] = useState(false);

  // Render clean, non-rainbow icons for campaign items
  const renderCampaignIcon = (type: CampaignItem["iconType"], isSelected: boolean) => {
    const iconClass = `w-3.5 h-3.5 flex-shrink-0 ${
      isSelected ? "text-gx-primary" : "text-gx-ink-muted"
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
      className="w-72 bg-gx-surface border-r border-gx-border flex flex-col h-screen select-none text-gx-ink font-sans z-20 flex-shrink-0"
      aria-label="GrowX AutoGTM Operating Panel"
    >
      {/* 1. Fixed Brand Header */}
      <div className="h-14 px-4 border-b border-gx-border flex items-center justify-between flex-shrink-0 bg-gx-surface">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-gx-primary rounded-xs"></span>
            <span className="w-2.5 h-2.5 bg-gx-primary/70 rounded-xs"></span>
          </div>
          <span className="font-bold text-base tracking-tight text-gx-ink flex items-center gap-1.5">
            growx{" "}
            <span className="text-[10px] font-semibold text-gx-ink-secondary uppercase tracking-widest px-1.5 py-0.5 rounded bg-gx-surface-soft border border-gx-border">
              AutoGTM
            </span>
          </span>
        </Link>
      </div>

      {/* 2. Scrollable Operating Panel Region */}
      <div className="flex-1 overflow-y-auto px-3.5 py-3.5 space-y-4 bg-gx-surface">
        {/* Step 1: Research your company */}
        <div>
          <div className="text-[11px] font-medium text-gx-ink-secondary mb-1.5 flex items-center gap-1.5">
            <Check className="w-3 h-3 text-gx-success stroke-[2.5]" />
            <span>step 1 &middot; Research your company</span>
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => setIsCompanyDropdownOpen(!isCompanyDropdownOpen)}
              className="w-full bg-gx-surface hover:bg-gx-surface-hover border border-gx-border rounded-lg p-2 text-left flex items-center justify-between transition-colors shadow-2xs"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-7 h-7 rounded bg-gx-primary flex items-center justify-center text-white font-bold text-xs flex-shrink-0 tracking-tighter shadow-2xs">
                  GX
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-gx-ink truncate">
                    {company.name}
                  </div>
                  <div className="text-[11px] text-gx-ink-muted font-mono truncate">
                    {company.domain}
                  </div>
                </div>
              </div>
              <ChevronDown
                className={`w-3.5 h-3.5 text-gx-ink-muted flex-shrink-0 ml-1 transition-transform ${
                  isCompanyDropdownOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {isCompanyDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-30"
                  onClick={() => setIsCompanyDropdownOpen(false)}
                />
                <div className="absolute top-full left-0 right-0 mt-1 bg-gx-surface border border-gx-border rounded-xl p-1.5 shadow-lg z-40 text-xs text-gx-ink space-y-1">
                  <div className="px-2 py-1 text-[10px] text-gx-ink-muted uppercase tracking-wider font-semibold">
                    Projects
                  </div>
                  {projects.map((proj) => {
                    const isSelected = proj.id === activeProjectId;
                    return (
                      <button
                        key={proj.id}
                        type="button"
                        onClick={() => {
                          selectProject(proj.id);
                          setIsCompanyDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2 py-1.5 rounded text-xs flex items-center justify-between transition-colors ${
                          isSelected
                            ? "bg-gx-primary-soft text-gx-primary font-semibold"
                            : "hover:bg-gx-surface-soft text-gx-ink"
                        }`}
                      >
                        <span className="font-medium truncate">{proj.name}</span>
                        {isSelected && (
                          <Check className="w-3.5 h-3.5 text-gx-primary flex-shrink-0" />
                        )}
                      </button>
                    );
                  })}
                  <div className="pt-1 border-t border-gx-border-soft">
                    <button
                      type="button"
                      onClick={() => {
                        selectProject(null);
                        setIsCompanyDropdownOpen(false);
                      }}
                      className="w-full text-left px-2 py-1.5 rounded hover:bg-gx-surface-soft text-gx-ink flex items-center gap-1.5 font-medium"
                    >
                      <Plus className="w-3.5 h-3.5 text-gx-ink-muted" />
                      <span>New project</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Step 2: Explore competitors */}
        <div>
          <div className="text-[11px] font-medium text-gx-ink-secondary mb-1 flex items-center gap-1.5">
            <Check className="w-3 h-3 text-gx-success stroke-[2.5]" />
            <span>step 2 &middot; Explore competitors</span>
          </div>

          <div className="flex items-center justify-between mb-1.5 px-0.5">
            <span className="text-[10px] uppercase font-semibold text-gx-ink-muted tracking-wider">
              Competitors {competitors.length}
            </span>
            <button
              type="button"
              onClick={() => setShowAllCompetitors(!showAllCompetitors)}
              title="Toggle competitor view"
              className="text-gx-ink-muted hover:text-gx-ink transition-colors"
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
                  className="flex items-center justify-between px-2 py-1 bg-gx-surface hover:bg-gx-surface-hover border border-gx-border hover:border-gx-border-strong rounded text-[11px] text-gx-ink transition-colors group shadow-2xs text-left min-w-0"
                  title={`${comp.name} (${comp.domain})`}
                >
                  <div className="flex items-center gap-1.5 min-w-0 truncate">
                    <span className="w-3.5 h-3.5 rounded bg-gx-surface-soft border border-gx-border text-[9px] font-bold flex items-center justify-center text-gx-ink-secondary flex-shrink-0">
                      {initial}
                    </span>
                    <span className="truncate font-mono text-[11px]">{comp.name}</span>
                  </div>
                  <ExternalLink className="w-2.5 h-2.5 text-gx-ink-muted group-hover:text-gx-primary flex-shrink-0 ml-1 opacity-70 group-hover:opacity-100" />
                </button>
              );
            })}

            {!showAllCompetitors && competitors.length > 8 && (
              <button
                type="button"
                onClick={() => setShowAllCompetitors(true)}
                className="col-span-2 text-center py-1 text-[11px] text-gx-ink-secondary hover:text-gx-ink bg-gx-surface-soft border border-gx-border rounded hover:bg-gx-surface-hover transition-colors font-medium"
              >
                +{competitors.length - 8} more
              </button>
            )}
          </div>
        </div>

        {/* Step 3: Define campaigns */}
        <div>
          <div className="text-[11px] font-medium text-gx-ink-secondary mb-1 flex items-center gap-1.5">
            <Check className="w-3 h-3 text-gx-success stroke-[2.5]" />
            <span>step 3 &middot; Define campaigns</span>
          </div>

          <div className="flex items-center justify-between mb-1.5 px-0.5">
            <span className="text-[10px] uppercase font-semibold text-gx-ink-muted tracking-wider">
              Campaigns {campaigns.length}
            </span>
            <Settings className="w-3 h-3 text-gx-ink-muted" />
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
                      ? "bg-gx-primary-soft text-gx-ink border border-gx-primary-border font-semibold shadow-2xs"
                      : "text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-soft border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate pr-2">
                    {renderCampaignIcon(camp.iconType, isSelected)}
                    <span className="truncate">{camp.name}</span>
                  </div>
                  <span
                    className={`text-[11px] font-mono flex-shrink-0 flex items-center gap-1 ${
                      isSelected
                        ? "text-gx-primary font-semibold"
                        : "text-gx-ink-muted"
                    }`}
                  >
                    {isSelected && <Clock className="w-2.5 h-2.5 text-gx-primary" />}
                    {camp.countLabel}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Completed Steps Below (4, 5, 6) - Clicking switches workspace tab dynamically */}
        <div className="pt-3 border-t border-gx-border-soft space-y-2 text-[11px]">
          <button
            type="button"
            onClick={() => setActiveTab("companies")}
            className={`w-full flex items-center gap-2 px-1 text-left transition-colors ${
              activeTab === "companies"
                ? "text-gx-primary font-semibold"
                : "text-gx-ink-secondary hover:text-gx-ink"
            }`}
          >
            <Check className="w-3 h-3 text-gx-success stroke-[2.5]" />
            <span>step 4 &middot; Find potential customers</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("people")}
            className={`w-full flex items-center gap-2 px-1 text-left transition-colors ${
              activeTab === "people"
                ? "text-gx-primary font-semibold"
                : "text-gx-ink-secondary hover:text-gx-ink"
            }`}
          >
            <Check className="w-3 h-3 text-gx-success stroke-[2.5]" />
            <span>step 5 &middot; Find decision makers</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("emails")}
            className={`w-full flex items-center gap-2 px-1 text-left transition-colors ${
              activeTab === "emails"
                ? "text-gx-primary font-semibold"
                : "text-gx-ink-secondary hover:text-gx-ink"
            }`}
          >
            <Check className="w-3 h-3 text-gx-success stroke-[2.5]" />
            <span>step 6 &middot; Write emails</span>
          </button>
        </div>
      </div>

      {/* 3. Fixed Operations & Account Footer */}
      <div className="p-2 border-t border-gx-border bg-gx-surface flex-shrink-0 space-y-1">
        <Link
          href="/ops"
          className="flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover transition-colors group"
          title="Open engineering operations console"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-gx-ink-muted group-hover:text-gx-ink-secondary" />
            <span className="font-medium">Operations Console</span>
          </div>
          <span className="text-[10px] font-mono text-gx-ink-muted">/ops</span>
        </Link>
        <AccountPopover userEmail="growxlabstech@gmail.com" />
      </div>
    </aside>
  );
}
