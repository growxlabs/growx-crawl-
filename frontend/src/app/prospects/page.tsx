"use client";

import React from "react";
import { ProjectProspectsTable } from "@/features/projects/ProjectProspectsTable";

export default function ProspectsGlobalPage() {
  return (
    <div className="space-y-5">
      <div className="border-b border-neutral-200 pb-4">
        <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
          Prospects
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          Accounts prioritized for outreach based on fit, timing, and verified intelligence.
        </p>
      </div>
      <ProjectProspectsTable projectId="prj_growx_mfg_india" />
    </div>
  );
}
