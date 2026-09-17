"use client";

import React, { useState } from "react";
import { Search, Sparkles, CheckCircle2, Clock } from "lucide-react";
import { JobProgressBar } from "@/components/status/JobProgressBar";
import { triggerBulkAction } from "@/lib/api/prospects";

export default function ProjectResearchPage({
  params,
}: {
  params: { projectId: string };
}) {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const handleLaunchDeepCrawl = async () => {
    try {
      const res = await triggerBulkAction({
        action: "research",
        prospect_ids: ["psp_linear", "psp_retool", "psp_datadog"],
      });
      setActiveJobId(res.job_id);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-neutral-800" />
              <h1 className="text-base font-bold text-neutral-900">
                Autonomous Deep Research
              </h1>
            </div>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl leading-relaxed">
              Launch targeted background crawls across company investor relations, engineering blogs,
              and executive profiles to discover unindexed buying triggers.
            </p>
          </div>

          <button
            onClick={handleLaunchDeepCrawl}
            disabled={!!activeJobId}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 shadow-2xs transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{activeJobId ? "Crawl Active..." : "Run Autonomous Crawl on Incomplete Accounts"}</span>
          </button>
        </div>

        {activeJobId && (
          <div className="mt-4 pt-4 border-t border-neutral-100">
            <JobProgressBar
              jobId={activeJobId}
              title="Autonomous Multipage Deep Crawl"
              onComplete={() => setActiveJobId(null)}
            />
          </div>
        )}
      </div>

      <div className="bg-white border border-neutral-200 rounded p-6 space-y-4">
        <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
          Recommended Research Targets
        </h2>
        <div className="space-y-3 text-xs">
          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between">
            <div>
              <div className="font-semibold text-neutral-900">Retool Inc.</div>
              <div className="text-[11px] text-neutral-500">
                Recommended: Crawl changelog & enterprise security whitepapers.
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-medium">
              Research More
            </span>
          </div>

          <div className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between">
            <div>
              <div className="font-semibold text-neutral-900">Supabase</div>
              <div className="text-[11px] text-neutral-500">
                Recommended: Verify SOC2 compliance and enterprise pricing model.
              </div>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-medium">
              Reverify
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
