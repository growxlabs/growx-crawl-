"use client";

import React, { useEffect, useState } from "react";
import { subscribeJobEvents, JobEvent } from "@/lib/api/jobs";
import { RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";

interface JobProgressBarProps {
  jobId: string;
  onComplete?: () => void;
  title?: string;
}

export function JobProgressBar({
  jobId,
  onComplete,
  title = "Processing...",
}: JobProgressBarProps) {
  const [percent, setPercent] = useState<number>(10);
  const [currentStep, setCurrentStep] = useState<string>("Initializing job...");
  const [status, setStatus] = useState<"running" | "completed" | "failed">("running");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    // Connect SSE stream
    const unsubscribe = subscribeJobEvents(
      jobId,
      (event: JobEvent) => {
        if (!active) return;
        if (event.step) setCurrentStep(event.step);
        if (typeof event.progress === "number") {
          setPercent(Math.min(100, Math.max(0, event.progress)));
        }

        if (event.status === "completed") {
          setStatus("completed");
          setPercent(100);
          if (onComplete) onComplete();
        } else if (event.status === "failed") {
          setStatus("failed");
          setErrorMsg(event.message || "Execution encountered an error.");
        }
      },
      (err) => {
        if (!active) return;
        console.warn("SSE connection error for job", jobId, err);
      }
    );

    // Simulated progress increment if backend sends discrete chunks
    const timer = setInterval(() => {
      setPercent((prev) => {
        if (prev < 90 && status === "running") {
          return prev + Math.floor(Math.random() * 8) + 2;
        }
        return prev;
      });
    }, 800);

    return () => {
      active = false;
      clearInterval(timer);
      unsubscribe();
    };
  }, [jobId, onComplete, status]);

  return (
    <div className="bg-white border border-neutral-200 rounded p-3 text-xs shadow-sm max-w-md w-full">
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-1.5 font-medium text-neutral-800">
          {status === "running" && (
            <RefreshCw className="w-3.5 h-3.5 text-indigo-600 animate-spin flex-shrink-0" />
          )}
          {status === "completed" && (
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
          )}
          {status === "failed" && (
            <AlertCircle className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />
          )}
          <span className="truncate">{title}</span>
        </div>
        <span className="font-mono text-[11px] text-neutral-500 tabular-nums">
          {percent}%
        </span>
      </div>

      {/* Progress Track */}
      <div className="w-full bg-neutral-100 rounded-full h-1.5 overflow-hidden border border-neutral-200">
        <div
          className={`h-full transition-all duration-300 ${
            status === "failed"
              ? "bg-rose-500"
              : status === "completed"
              ? "bg-emerald-500"
              : "bg-indigo-600"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>

      <div className="mt-1.5 flex items-center justify-between text-[10px] text-neutral-400">
        <span className="truncate max-w-[280px]">
          {errorMsg ? (
            <span className="text-rose-600">{errorMsg}</span>
          ) : (
            currentStep
          )}
        </span>
        <span className="font-mono">{jobId.slice(0, 10)}...</span>
      </div>
    </div>
  );
}
