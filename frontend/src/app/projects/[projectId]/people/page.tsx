"use client";

import React from "react";
import { ProjectPeopleList } from "@/features/projects/ProjectPeopleList";

export default function ProjectPeoplePage({
  params,
}: {
  params: { projectId: string };
}) {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-sm font-bold text-neutral-900 font-mono uppercase tracking-wide">
          Target Buyer Personas & Contacts
        </h1>
        <p className="text-xs text-neutral-500 mt-0.5">
          Verified decision makers and champions matched to the active project ICP profile.
        </p>
      </div>
      <ProjectPeopleList projectId={params.projectId} />
    </div>
  );
}
