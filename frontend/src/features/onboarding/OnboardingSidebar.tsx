"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Folder, ChevronsUpDown, Plus, Check } from "lucide-react";
import { useCockpit } from "@/features/cockpit/CockpitContext";
import { AccountPopover } from "@/features/account/AccountPopover";

export function OnboardingSidebar() {
  const { projects, activeProjectId, selectProject } = useCockpit();
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);

  return (
    <aside
      className="w-64 bg-gx-surface border-r border-gx-border flex flex-col h-screen select-none text-gx-ink font-sans z-20 flex-shrink-0"
      aria-label="GrowX Navigation"
    >
      {/* 1. Brand Header */}
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

      {/* 2. Top Project Selector Region */}
      <div className="p-3 border-b border-gx-border-soft relative">
        <button
          type="button"
          onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-gx-surface-soft hover:bg-gx-surface-hover border border-gx-border text-xs font-medium text-gx-ink transition-colors shadow-2xs"
        >
          <div className="flex items-center gap-2 truncate">
            <Folder className="w-4 h-4 text-gx-ink-muted flex-shrink-0" />
            <span className="truncate">
              {activeProjectId
                ? projects.find((p) => p.id === activeProjectId)?.name || "Select project"
                : "Select project"}
            </span>
          </div>
          <ChevronsUpDown className="w-3.5 h-3.5 text-gx-ink-muted flex-shrink-0 ml-1" />
        </button>

        {/* Project Selector Dropdown Menu matching Explee media_1789643494455.png */}
        {isProjectDropdownOpen && (
          <>
            <div
              className="fixed inset-0 z-30"
              onClick={() => setIsProjectDropdownOpen(false)}
            />
            <div className="absolute top-full left-3 right-3 mt-1 bg-gx-surface border border-gx-border rounded-xl p-1.5 shadow-xl z-40 text-xs text-gx-ink space-y-1 animate-in fade-in-50 duration-150">
              <div className="px-2.5 py-1 text-[10px] font-semibold text-gx-ink-muted uppercase tracking-wider">
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
                      setIsProjectDropdownOpen(false);
                    }}
                    className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-left transition-colors ${
                      isSelected
                        ? "bg-gx-primary-soft text-gx-primary font-semibold"
                        : "text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover"
                    }`}
                  >
                    <div className="truncate pr-2">
                      <div className="text-xs font-medium truncate">{proj.name}</div>
                      <div className="text-[10px] text-gx-ink-muted font-mono truncate">
                        {proj.domain}
                      </div>
                    </div>
                    {isSelected && <Check className="w-3.5 h-3.5 flex-shrink-0 text-gx-primary" />}
                  </button>
                );
              })}

              <div className="pt-1 border-t border-gx-border-soft">
                <button
                  type="button"
                  onClick={() => {
                    selectProject(null);
                    setIsProjectDropdownOpen(false);
                  }}
                  className={`w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors ${
                    !activeProjectId
                      ? "bg-gx-surface-soft text-gx-ink font-semibold"
                      : "text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover"
                  }`}
                >
                  <Plus className="w-4 h-4 text-gx-ink-muted" />
                  <span>New project</span>
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* 3. Empty Center Canvas in Sidebar */}
      <div className="flex-1" />

      {/* 4. Bottom User Profile Footer matching Explee */}
      <div className="p-2.5 border-t border-gx-border bg-gx-surface flex-shrink-0">
        <AccountPopover userEmail="growxlabstech@gmail.com" />
      </div>
    </aside>
  );
}
