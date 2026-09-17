"use client";

import React, { useState } from "react";
import { triggerProspectReverify } from "@/lib/api/prospects";
import { JobProgressBar } from "@/components/status/JobProgressBar";
import { RefreshCw, AlertTriangle } from "lucide-react";

interface ReverifyCalloutProps {
  prospectId: string;
  companyName: string;
  onCompleted?: () => void;
}

export function ReverifyCallout({
  prospectId,
  companyName,
  onCompleted,
}: ReverifyCalloutProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await triggerProspectReverify(prospectId);
      setJobId(res.job_id);
    } catch (err) {
      console.error("Reverify trigger failed", err);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="p-4 rounded border border-amber-200 bg-amber-50/50 space-y-3 text-xs">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-semibold text-amber-900">
              Re-verification Recommended
            </div>
            <p className="text-amber-800 text-[11px] mt-0.5 leading-relaxed">
              Critical buyer facts for {companyName} have aged or show conflicting source signals.
              Run a targeted crawl to refresh DOM citations and ensure zero-hallucination outbound qualification.
            </p>
          </div>
        </div>

        {!jobId && (
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-amber-600 hover:bg-amber-700 text-white font-medium text-xs shadow-2xs transition-colors flex-shrink-0 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${triggering ? "animate-spin" : ""}`} />
            <span>{triggering ? "Initiating..." : "Reverify Account"}</span>
          </button>
        )}
      </div>

      {jobId && (
        <div className="pt-2 border-t border-amber-200/60">
          <JobProgressBar
            jobId={jobId}
            title={`Re-verifying ${companyName}`}
            onComplete={() => {
              setJobId(null);
              if (onCompleted) onCompleted();
            }}
          />
        </div>
      )}
    </div>
  );
}
