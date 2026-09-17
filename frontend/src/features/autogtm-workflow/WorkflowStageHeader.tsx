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
            className="w-4 h-4 rounded-full bg-[#EAF7F1] border border-[#BDEBD7] text-[#16825D] flex items-center justify-center text-[10px] flex-shrink-0"
            title="Stage completed"
            aria-label="Completed"
          >
            <Check className="w-2.5 h-2.5 stroke-[2.5]" />
          </span>
        );
      case "running":
        return (
          <span
            className="w-4 h-4 rounded-full bg-[#EDF2FF] border border-[#C9D5FF] text-[#315EF5] flex items-center justify-center flex-shrink-0"
            title="Stage in progress"
            aria-label="In progress"
          >
            <Loader2 className="w-2.5 h-2.5 animate-spin" />
          </span>
        );
      case "attention":
        return (
          <span
            className="w-4 h-4 rounded-full bg-[#FFF5E5] border border-[#FEE1BA] text-[#A86514] flex items-center justify-center flex-shrink-0"
            title="Action required"
            aria-label="Attention needed"
          >
            <AlertCircle className="w-2.5 h-2.5" />
          </span>
        );
      case "failed":
        return (
          <span
            className="w-4 h-4 rounded-full bg-[#FDECEC] border border-[#F8C8C8] text-[#C64141] flex items-center justify-center flex-shrink-0"
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
            className="w-4 h-4 rounded-full border border-[#DDE2E8] bg-[#F1F3F6] text-[#818A97] flex items-center justify-center text-[9px] font-mono flex-shrink-0"
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
          ? "bg-[#EDF2FF] text-[#111318] border-l-2 border-[#315EF5] pl-2 pr-2 py-1.5 rounded-r-md font-semibold"
          : isPending
          ? "cursor-default text-[#818A97] border-l-2 border-transparent pl-2 pr-2 py-1.5"
          : "cursor-pointer text-[#111318] hover:bg-[#F1F3F6] border-l-2 border-transparent pl-2 pr-2 py-1.5 rounded-r-md group"
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        {renderStateIndicator()}
        <div className="truncate flex items-center gap-1.5">
          <span className="text-[#818A97] text-[11px] font-mono">{order}.</span>
          <span
            className={
              isExpanded
                ? "text-[#111318] font-semibold"
                : isPending
                ? "text-[#818A97]"
                : "text-[#111318] group-hover:text-[#315EF5]"
            }
          >
            {title}
          </span>
        </div>
      </div>

      {canExpand && !isPending && (
        <ChevronRight
          className={`w-3.5 h-3.5 text-[#818A97] transition-transform flex-shrink-0 ml-1 ${
            isExpanded ? "rotate-90 text-[#315EF5]" : "group-hover:text-[#4D5663]"
          }`}
        />
      )}
    </button>
  );
}
