"use client";

import React from "react";
import { useCockpit } from "./CockpitContext";
import { Send } from "lucide-react";

export function CockpitHeader() {
  const { setIsOutreachModalOpen } = useCockpit();

  return (
    <header className="h-14 border-b border-[#DDE2E8] bg-[#FFFFFF] px-6 flex items-center justify-between sticky top-0 z-10 select-none text-[#111318] flex-shrink-0">
      {/* Left Stepper Progression */}
      <div className="flex items-center gap-6 overflow-x-auto py-1">
        {/* Stages 1 to 6 */}
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((num) => (
            <React.Fragment key={num}>
              <div className="w-5 h-5 rounded-full bg-[#F1F3F6] border border-[#DDE2E8] flex items-center justify-center text-[10px] font-semibold text-[#4D5663]">
                {num}
              </div>
              <div className="w-4 h-[1px] bg-[#DDE2E8]" />
            </React.Fragment>
          ))}

          {/* Active Step 6 Pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 bg-[#EDF2FF] border border-[#C9D5FF] rounded-full text-xs font-semibold text-[#315EF5] shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-[#315EF5] animate-pulse"></span>
            <span>6 Outreach ready</span>
          </div>
        </div>

        {/* Vertical Divider */}
        <div className="h-5 w-[1px] bg-[#DDE2E8] hidden lg:block" />

        {/* Future Steps (What happens next) */}
        <div className="hidden lg:flex items-center gap-4 text-xs text-[#4D5663]">
          <span className="text-[10px] uppercase font-semibold text-[#818A97] tracking-wider">
            What happens next
          </span>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-[#4D5663]">
              <span className="w-4 h-4 rounded-full border border-[#DDE2E8] bg-[#F1F3F6] flex items-center justify-center text-[9px] font-semibold text-[#818A97]">
                7
              </span>
              <span>Send emails</span>
            </div>
            <div className="flex items-center gap-1.5 text-[#4D5663]">
              <span className="w-4 h-4 rounded-full border border-[#DDE2E8] bg-[#F1F3F6] flex items-center justify-center text-[9px] font-semibold text-[#818A97]">
                8
              </span>
              <span>Book meetings</span>
            </div>
            <div className="flex items-center gap-1.5 text-[#4D5663]">
              <span className="w-4 h-4 rounded-full border border-[#DDE2E8] bg-[#F1F3F6] flex items-center justify-center text-[9px] font-semibold text-[#818A97]">
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
          <div className="text-xs font-semibold text-[#111318]">$30 free credits</div>
          <div className="text-[10px] text-[#818A97]">No upfront charge</div>
        </div>

        <button
          type="button"
          onClick={() => setIsOutreachModalOpen(true)}
          className="bg-[#315EF5] hover:bg-[#244BD6] text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99]"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Start outreach</span>
        </button>
      </div>
    </header>
  );
}
