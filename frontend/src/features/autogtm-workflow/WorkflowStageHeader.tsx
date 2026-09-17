"use client";

import React from "react";
import { Check, Loader2, AlertCircle, CircleAlert, ChevronRight } from "lucide-react";
import { WorkflowStageState } from "./workflow-presenter";

interface WorkflowStageHeaderProps {
  order: number;
  title: string;
  state: WorkflowStageState;
  isExpanded: boolean;
  onToggle: () => void;
  canExpand?: boolean;
}

export function WorkflowStageHeader({
  order,
  title,
  state,
  isExpanded,
  onToggle,
  canExpand = true,
}: WorkflowStageHeaderProps) {
  // Render accessible, restrained state glyph
  const renderStateIndicator = () => {
    switch (state) {
      case "completed":
        return (
          <span
            className="w-4 h-4 rounded-full bg-gx-success-soft border border-gx-success/30 text-gx-success flex items-center justify-center text-[10px] flex-shrink-0"
            title="Stage completed"
            aria-label="Completed"
          >
            <Check className="w-2.5 h-2.5 stroke-[2.5]" />
          </span>
        );
      case "running":
        return (
          <span
            className="w-4 h-4 rounded-full bg-gx-primary-soft border border-gx-primary-border text-gx-primary flex items-center justify-center flex-shrink-0"
            title="Stage in progress"
            aria-label="In progress"
          >
            <Loader2 className="w-2.5 h-2.5 animate-spin" />
          </span>
        );
      case "attention":
        return (
          <span
            className="w-4 h-4 rounded-full bg-gx-warning-soft border border-gx-warning/30 text-gx-warning flex items-center justify-center flex-shrink-0"
            title="Action required"
            aria-label="Attention needed"
          >
            <AlertCircle className="w-2.5 h-2.5" />
          </span>
        );
      case "failed":
        return (
          <span
            className="w-4 h-4 rounded-full bg-gx-danger-soft border border-gx-danger/30 text-gx-danger flex items-center justify-center flex-shrink-0"
            title="Stage failed"
            aria-label="Failed"
          >
            <CircleAlert className="w-2.5 h-2.5" />
          </span>
        );
      case "pending":
      default:
        return (
          <span
            className="w-4 h-4 rounded-full border border-gx-border bg-gx-surface-soft text-gx-ink-muted flex items-center justify-center text-[9px] font-mono flex-shrink-0"
            title="Pending"
            aria-label="Pending"
          >
            {order}
          </span>
        );
    }
  };

  const isPending = state === "pending";

  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={!canExpand}
      aria-expanded={isExpanded}
      className={`w-full flex items-center justify-between text-left transition-colors select-none text-xs ${
        isExpanded
          ? "bg-gx-primary-soft text-gx-ink border-l-2 border-gx-primary pl-2 pr-2 py-1.5 rounded-r-md font-semibold"
          : isPending
          ? "cursor-default text-gx-ink-muted border-l-2 border-transparent pl-2 pr-2 py-1.5"
          : "cursor-pointer text-gx-ink hover:bg-gx-surface-soft border-l-2 border-transparent pl-2 pr-2 py-1.5 rounded-r-md group"
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        {renderStateIndicator()}
        <div className="truncate flex items-center gap-1.5">
          <span className="text-gx-ink-muted text-[11px] font-mono">{order}.</span>
          <span
            className={
              isExpanded
                ? "text-gx-ink font-semibold"
                : isPending
                ? "text-gx-ink-muted"
                : "text-gx-ink group-hover:text-gx-primary"
            }
          >
            {title}
          </span>
        </div>
      </div>

      {canExpand && !isPending && (
        <ChevronRight
          className={`w-3.5 h-3.5 text-gx-ink-muted transition-transform flex-shrink-0 ml-1 ${
            isExpanded ? "rotate-90 text-gx-primary" : "group-hover:text-gx-ink-secondary"
          }`}
        />
      )}
    </button>
  );
}
