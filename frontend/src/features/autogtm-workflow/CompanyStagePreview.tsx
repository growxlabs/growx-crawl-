"use client";

import React from "react";
import { useCockpit } from "@/features/cockpit/CockpitContext";

export function CompanyStagePreview() {
  const { company } = useCockpit();

  return (
    <div className="mt-2.5 p-2.5 rounded-lg bg-[#141824] border border-[#212738] flex items-center gap-2.5">
      <div className="w-8 h-8 rounded bg-white flex items-center justify-center text-slate-900 font-bold text-xs flex-shrink-0 tracking-tighter shadow-sm">
        GX
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-white truncate">
          {company.name}
        </div>
        <div className="text-[11px] text-slate-400 font-mono truncate">
          {company.domain}
        </div>
      </div>
    </div>
  );
}
