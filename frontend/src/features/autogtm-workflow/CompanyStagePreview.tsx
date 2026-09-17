"use client";

import React from "react";
import { useCockpit } from "@/features/cockpit/CockpitContext";

export function CompanyStagePreview() {
  const { company } = useCockpit();

  return (
    <div className="mt-2 p-2.5 rounded-lg bg-[#F6F7F9] border border-[#DDE2E8] flex items-center gap-2.5">
      <div className="w-7 h-7 rounded bg-[#315EF5] flex items-center justify-center text-white font-bold text-xs flex-shrink-0 tracking-tighter shadow-xs">
        GX
      </div>
      <div className="min-w-0">
        <div className="text-xs font-semibold text-[#111318] truncate">
          {company.name}
        </div>
        <div className="text-[11px] text-[#4D5663] font-mono truncate">
          {company.domain}
        </div>
      </div>
    </div>
  );
}
