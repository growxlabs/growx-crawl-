"use client";

import React from "react";
import { ProjectOverview } from "@/features/projects/ProjectOverview";

export default function ProjectOverviewPage({
  params,
}: {
  params: { projectId: string };
}) {
  return <ProjectOverview projectId={params.projectId} />;
}
