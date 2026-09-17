"use client";

import React from "react";
import { ProspectDetailView } from "@/features/prospects/ProspectDetailView";

export default function ProspectDetailPage({
  params,
}: {
  params: { prospectId: string };
}) {
  return <ProspectDetailView prospectId={params.prospectId} />;
}
