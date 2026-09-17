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
    <div className="pl-8 pr-2 text-[11px] text-gx-ink-secondary truncate leading-snug pt-0.5">
      {summary}
    </div>
  );
}
