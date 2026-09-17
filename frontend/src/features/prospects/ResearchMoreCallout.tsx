"use client";

import React, { useState } from "react";
import { triggerProspectResearch } from "@/lib/api/prospects";
import { JobProgressBar } from "@/components/status/JobProgressBar";
import { Search, Sparkles } from "lucide-react";

interface ResearchMoreCalloutProps {
  prospectId: string;
  companyName: string;
  onCompleted?: () => void;
}

export function ResearchMoreCallout({
  prospectId,
  companyName,
  onCompleted,
}: ResearchMoreCalloutProps) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      const res = await triggerProspectResearch(prospectId);
      setJobId(res.job_id);
    } catch (err) {
      console.error("Deep research trigger failed", err);
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="p-4 rounded border border-blue-200 bg-blue-50/40 space-y-3 text-xs">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <Search className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <div className="font-semibold text-blue-900">
              Deep Technical Research Recommended
            </div>
            <p className="text-blue-800 text-[11px] mt-0.5 leading-relaxed">
              {companyName} shows strong potential ICP fit, but technographic stack details
              and key executive contacts remain incomplete. Launch an autonomous deep crawl
              across engineering docs, careers pages, and press releases.
            </p>
          </div>
        </div>

        {!jobId && (
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs shadow-2xs transition-colors flex-shrink-0 disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{triggering ? "Launching..." : "Deep Research Account"}</span>
          </button>
        )}
      </div>

      {jobId && (
        <div className="pt-2 border-t border-blue-200/60">
          <JobProgressBar
            jobId={jobId}
            title={`Deep Researching ${companyName}`}
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
