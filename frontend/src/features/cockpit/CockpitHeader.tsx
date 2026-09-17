"use client";

import React from "react";
import { useCockpit } from "./CockpitContext";
import { Send } from "lucide-react";

export function CockpitHeader() {
  const { setIsOutreachModalOpen } = useCockpit();

  return (
    <header className="h-14 border-b border-gx-border bg-gx-surface px-6 flex items-center justify-between sticky top-0 z-10 select-none text-gx-ink flex-shrink-0">
      {/* Left Stepper Progression */}
      <div className="flex items-center gap-6 overflow-x-auto py-1">
        {/* Stages 1 to 5 */}
        <div className="flex items-center gap-2">
          {[1, 2, 3, 4, 5].map((num) => (
            <React.Fragment key={num}>
              <div className="w-5 h-5 rounded-full bg-gx-surface-soft border border-gx-border flex items-center justify-center text-[10px] font-semibold text-gx-ink-secondary">
                {num}
              </div>
              <div className="w-4 h-[1px] bg-gx-border" />
            </React.Fragment>
          ))}

          {/* Active Step 6 Pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 bg-gx-primary-soft border border-gx-primary-border rounded-full text-xs font-semibold text-gx-primary shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-gx-primary animate-pulse"></span>
            <span>6 Outreach ready</span>
          </div>
        </div>

        {/* Future Steps (What happens next - stacked above steps 7, 8, 9 matching Explee) */}
        <div className="hidden xl:flex flex-col items-center justify-center pl-4 border-l border-gx-border/60">
          <span className="text-[9px] uppercase font-bold text-gx-ink-muted tracking-widest leading-none mb-1 select-none">
            What happens next
          </span>
          <div className="flex items-center gap-4 text-xs text-gx-ink-secondary">
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full border border-gx-border bg-gx-surface-soft flex items-center justify-center text-[9px] font-semibold text-gx-ink-muted">
                7
              </span>
              <span>Send emails</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full border border-gx-border bg-gx-surface-soft flex items-center justify-center text-[9px] font-semibold text-gx-ink-muted">
                8
              </span>
              <span>Book meetings</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full border border-gx-border bg-gx-surface-soft flex items-center justify-center text-[9px] font-semibold text-gx-ink-muted">
                9
              </span>
              <span>Learn &amp; double down</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right: Credits and CTA */}
      <div className="flex items-center gap-4 flex-shrink-0">
        <div className="text-right hidden sm:block">
          <div className="text-xs font-semibold text-gx-ink">$30 free credits</div>
          <div className="text-[10px] text-gx-ink-muted">No upfront charge</div>
        </div>

        <button
          type="button"
          onClick={() => setIsOutreachModalOpen(true)}
          className="bg-gx-primary hover:bg-gx-primary-hover text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99]"
        >
          <Send className="w-3.5 h-3.5" />
          <span>Start outreach</span>
        </button>
      </div>
    </header>
  );
}
