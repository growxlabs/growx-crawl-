"use client";

import React from "react";
import { AutoGTMWorkflowStageView } from "./workflow-presenter";
import { WorkflowStageHeader } from "./WorkflowStageHeader";
import { WorkflowStageSummary } from "./WorkflowStageSummary";
import { WorkflowStageBody } from "./WorkflowStageBody";

interface WorkflowStageProps {
  stage: AutoGTMWorkflowStageView;
  isExpanded: boolean;
  onToggle: () => void;
  isLast?: boolean;
}

export function WorkflowStage({
  stage,
  isExpanded,
  onToggle,
  isLast = false,
}: WorkflowStageProps) {
  return (
    <div className="relative group">
      {/* Subtle vertical connector between stages */}
      {!isLast && (
        <div
          className={`absolute left-[15px] top-7 bottom-0 w-[1.5px] ${
            stage.state === "completed"
              ? "bg-gx-success/30"
              : "bg-gx-border-soft"
          }`}
          aria-hidden="true"
        />
      )}

      {/* Stage Container */}
      <div className="relative z-1 space-y-0.5 pb-3">
        <WorkflowStageHeader
          order={stage.order}
          title={stage.title}
          state={stage.state}
          isExpanded={isExpanded}
          onToggle={onToggle}
          canExpand={stage.state !== "pending"}
        />

        <WorkflowStageSummary
          summary={stage.summary}
          isExpanded={isExpanded}
        />

        <WorkflowStageBody
          stageKey={stage.key}
          isExpanded={isExpanded}
        />
      </div>
    </div>
  );
}
