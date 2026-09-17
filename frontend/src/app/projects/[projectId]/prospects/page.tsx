"use client";

import React from "react";
import { ProjectProspectsTable } from "@/features/projects/ProjectProspectsTable";

export default function ProjectProspectsPage({
  params,
}: {
  params: { projectId: string };
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-neutral-900 font-mono uppercase tracking-wide">
            Ranked Prospect Accounts
          </h1>
          <p className="text-xs text-neutral-500 mt-0.5">
            Accounts ordered by final composite score combining ICP fit, verified evidence, and temporal buying signals.
          </p>
        </div>
      </div>
      <ProjectProspectsTable projectId={params.projectId} />
    </div>
  );
}
