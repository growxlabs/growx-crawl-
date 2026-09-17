"use client";

import React from "react";

interface WorkflowStageSummaryProps {
  summary?: string;
  isExpanded?: boolean;
}

export function WorkflowStageSummary({
  summary,
  isExpanded,
}: WorkflowStageSummaryProps) {
  if (!summary || isExpanded) return null;

  return (
    <div className="pl-6 text-[11px] text-slate-400 truncate leading-snug mt-0.5">
      {summary}
    </div>
  );
}
