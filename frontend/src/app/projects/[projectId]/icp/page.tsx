"use client";

import React from "react";
import { ICPView } from "@/features/icp/ICPView";

export default function ProjectICPPage({
  params,
}: {
  params: { projectId: string };
}) {
  return <ICPView icpId="icp_us_midmarket_saas" />;
}
