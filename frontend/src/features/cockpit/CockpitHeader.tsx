"use client";

import React from "react";
import { useCockpit } from "./CockpitContext";
import { Sparkles, Send } from "lucide-react";

export function CockpitHeader() {
  const { setIsOutreachModalOpen } = useCockpit();

  return (
    <header className="h-16 border-b border-[#1e2330] bg-[#0d0f15] px-6 flex items-center justify-between sticky top-0 z-10 select-none text-slate-300">
      {/* Left Stepper Progression */}
      <div className="flex items-center gap-6 overflow-x-auto py-1">
        {/* Stages 1 to 6 */}
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((num) => (
            <React.Fragment key={num}>
              <div className="w-5 h-5 rounded-full bg-[#181d29] border border-[#262e40] flex items-center justify-center text-[10px] font-semibold text-slate-400">
                {num}
              </div>
              <div className="w-4 h-[1px] bg-[#232938]" />
            </React.Fragment>
          ))}

          {/* Active Step 6 Pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#141923] border border-[#252c3d] rounded-full text-xs font-semibold text-white shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>6 Outreach ready</span>
          </div>
        </div>

        {/* Vertical Divider */}
        <div className="h-5 w-[1px] bg-[#232938] hidden lg:block" />

        {/* Future Steps (What happens next) */}
        <div className="hidden lg:flex items-center gap-4 text-xs text-slate-400">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            What happens next
          </span>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-slate-400">
              <span className="w-4 h-4 rounded-full border border-[#2b3346] flex items-center justify-center text-[9px]">
                7
              </span>
              <span>Send emails</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-400">
              <span className="w-4 h-4 rounded-full border border-[#2b3346] flex items-center justify-center text-[9px]">
                8
              </span>
              <span>Book meetings</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-400">
              <span className="w-4 h-4 rounded-full border border-[#2b3346] flex items-center justify-center text-[9px]">
                9
              </span>
              <span>Learn & double down</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Credits and CTA */}
      <div className="flex items-center gap-4 flex-shrink-0">
        <div className="text-right hidden sm:block">
          <div className="text-xs font-medium text-slate-200">$30 free credits</div>
          <div className="text-[10px] text-slate-400">No upfront charge</div>
        </div>

        <button
          onClick={() => setIsOutreachModalOpen(true)}
          className="bg-[#00c288] hover:bg-[#00d696] text-slate-950 font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-lg shadow-emerald-950/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Start outreach</span>
        </button>
      </div>
    </header>
  );
}
