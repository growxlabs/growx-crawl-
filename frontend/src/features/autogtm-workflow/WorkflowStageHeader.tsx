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
  // Render accessible state glyph
  const renderStateIndicator = () => {
    switch (state) {
      case "completed":
        return (
          <span
            className="w-4 h-4 rounded-full bg-emerald-950/80 border border-emerald-500/50 text-emerald-400 flex items-center justify-center text-[10px] flex-shrink-0"
            title="Stage completed"
            aria-label="Completed"
          >
            <Check className="w-2.5 h-2.5 stroke-[2.5]" />
          </span>
        );
      case "running":
        return (
          <span
            className="w-4 h-4 rounded-full bg-blue-950/80 border border-blue-500/50 text-blue-400 flex items-center justify-center flex-shrink-0"
            title="Stage in progress"
            aria-label="In progress"
          >
            <Loader2 className="w-2.5 h-2.5 animate-spin" />
          </span>
        );
      case "attention":
        return (
          <span
            className="w-4 h-4 rounded-full bg-amber-950/80 border border-amber-500/50 text-amber-400 flex items-center justify-center flex-shrink-0"
            title="Action required"
            aria-label="Attention needed"
          >
            <AlertCircle className="w-2.5 h-2.5" />
          </span>
        );
      case "failed":
        return (
          <span
            className="w-4 h-4 rounded-full bg-rose-950/80 border border-rose-500/50 text-rose-400 flex items-center justify-center flex-shrink-0"
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
            className="w-4 h-4 rounded-full border border-slate-700 bg-[#121622] text-slate-500 flex items-center justify-center text-[9px] font-mono flex-shrink-0"
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
      className={`w-full flex items-center justify-between text-left py-1 text-xs group transition-colors select-none ${
        isPending
          ? "cursor-default text-slate-500"
          : "cursor-pointer text-slate-200 hover:text-white"
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        {renderStateIndicator()}
        <div className="truncate font-medium flex items-center gap-1.5">
          <span className="text-slate-400 text-[11px] font-mono">{order}.</span>
          <span
            className={
              isExpanded
                ? "text-white font-semibold"
                : isPending
                ? "text-slate-500"
                : "text-slate-300 group-hover:text-white"
            }
          >
            {title}
          </span>
        </div>
      </div>

      {canExpand && !isPending && (
        <ChevronRight
          className={`w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 transition-transform flex-shrink-0 ml-1 ${
            isExpanded ? "rotate-90 text-slate-300" : ""
          }`}
        />
      )}
    </button>
  );
}
