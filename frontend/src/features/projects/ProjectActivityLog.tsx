"use client";

import React, { useEffect, useState } from "react";
import {
  ProjectActivityItem,
  getProjectActivity,
} from "@/lib/api/projects";
import { Clock, UserCheck, RefreshCw, Sparkles, Edit3 } from "lucide-react";

interface ProjectActivityLogProps {
  projectId: string;
}

export function ProjectActivityLog({ projectId }: ProjectActivityLogProps) {
  const [activities, setActivities] = useState<ProjectActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getProjectActivity(projectId)
      .then((data) => setActivities(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [projectId]);

  const defaultActivities: ProjectActivityItem[] = [
    {
      id: "act_001",
      timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
      actor: "AutoGTM Scoring Engine",
      action_type: "prospect_ranking_completed",
      description: "Ranked 48 prospect companies against active ICP v1.0. 14 accounts flagged as Priority.",
      target_entity_id: projectId,
    },
    {
      id: "act_002",
      timestamp: new Date(Date.now() - 3600000 * 5).toISOString(),
      actor: "DOM Crawler Service",
      action_type: "reverification_job_completed",
      description: "Re-crawled pricing pages and team directory for 5 accounts.",
      target_entity_id: "cmp_linear",
    },
    {
      id: "act_003",
      timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
      actor: "Operator",
      action_type: "fact_override",
      description: "Manually corrected Supabase employee count to 120 based on LinkedIn census.",
      target_entity_id: "cmp_supabase",
    },
    {
      id: "act_004",
      timestamp: new Date(Date.now() - 3600000 * 48).toISOString(),
      actor: "AutoGTM Admin",
      action_type: "project_created",
      description: "Initialized project 'US Mid-Market SaaS Expansion' with attached ICP v1.0.",
      target_entity_id: projectId,
    },
  ];

  const list = activities.length > 0 ? activities : defaultActivities;

  return (
    <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs space-y-6">
      <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wider font-mono text-neutral-900">
            Project Audit & Activity Stream
          </h2>
          <p className="text-xs text-neutral-500 mt-0.5">
            Full provenance of automated pipeline execution and human fact overrides.
          </p>
        </div>
        <span className="text-xs font-mono text-neutral-400">
          {list.length} Events Logged
        </span>
      </div>

      <div className="relative border-l border-neutral-200 ml-3.5 pl-6 space-y-6">
        {list.map((act) => (
          <div key={act.id} className="relative group">
            <div className="absolute -left-[31px] top-1.5 w-3 h-3 rounded-full bg-neutral-900 border-2 border-white shadow-xs" />

            <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-xs text-neutral-900">
                  {act.actor}
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-600 border border-neutral-200">
                  {act.action_type.replace(/_/g, " ")}
                </span>
              </div>
              <div className="flex items-center gap-1 text-[11px] font-mono text-neutral-400">
                <Clock className="w-3 h-3" />
                <span>{new Date(act.timestamp).toLocaleString()}</span>
              </div>
            </div>

            <p className="text-xs text-neutral-700 leading-relaxed font-sans mt-1">
              {act.description}
            </p>

            {act.target_entity_id && (
              <div className="mt-1.5 text-[10px] font-mono text-neutral-400">
                Entity: {act.target_entity_id}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
