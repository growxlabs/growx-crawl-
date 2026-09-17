"use client";

import React from "react";
import { ProjectProspectsTable } from "@/features/projects/ProjectProspectsTable";

export default function ProspectsGlobalPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-neutral-900 font-mono uppercase tracking-wide">
            Prioritized Prospects
          </h1>
          <p className="text-xs text-neutral-500 mt-0.5">
            Global view of candidate accounts across active AutoGTM campaigns.
          </p>
        </div>
      </div>
      <ProjectProspectsTable projectId="prj_us_saas_expansion" />
    </div>
  );
}
