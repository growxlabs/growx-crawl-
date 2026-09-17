"use client";

import React from "react";
import { ProjectActivityLog } from "@/features/projects/ProjectActivityLog";

export default function ProjectActivityPage({
  params,
}: {
  params: { projectId: string };
}) {
  return <ProjectActivityLog projectId={params.projectId} />;
}
