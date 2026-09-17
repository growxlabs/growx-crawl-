"use client";

import React, { useEffect, useState } from "react";
import { Search, Activity, ChevronDown, CheckCircle2, RefreshCw } from "lucide-react";
import { listProjects, Project } from "@/lib/api/projects";
import { listJobs, JobItem } from "@/lib/api/jobs";

export function Header() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("prj_us_saas_expansion");
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [showJobsDropdown, setShowJobsDropdown] = useState<boolean>(false);

  useEffect(() => {
    listProjects().then((projs) => {
      if (projs && projs.length > 0) {
        setProjects(projs);
        setSelectedProject(projs[0].id);
      }
    }).catch(() => {});

    listJobs().then((j) => {
      setJobs(j);
    }).catch(() => {});
  }, []);

  const runningJobsCount = jobs.filter((j) => j.status === "running").length;

  return (
    <header className="h-14 border-b border-neutral-200 bg-white px-6 flex items-center justify-between sticky top-0 z-10">
      {/* Left: Project Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-neutral-500 font-medium">
          <span>Active Project:</span>
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="text-neutral-900 font-semibold bg-neutral-100 hover:bg-neutral-200/70 border border-neutral-300/80 rounded px-2.5 py-1 text-xs outline-none cursor-pointer"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
            {projects.length === 0 && (
              <option value="prj_us_saas_expansion">US Mid-Market SaaS Expansion</option>
            )}
          </select>
        </div>
      </div>

      {/* Center: Global Search */}
      <div className="w-96 relative">
        <Search className="w-3.5 h-3.5 text-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search accounts, domains, people, or signals..."
          className="w-full bg-neutral-50 border border-neutral-200 rounded pl-8 pr-3 py-1.5 text-xs placeholder:text-neutral-400 text-neutral-800 outline-none focus:border-neutral-400 focus:bg-white transition-colors"
        />
      </div>

      {/* Right: Activity & Status */}
      <div className="flex items-center gap-3">
        {/* Active Jobs Badge */}
        <div className="relative">
          <button
            onClick={() => setShowJobsDropdown(!showJobsDropdown)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-2xs font-mono border transition-colors ${
              runningJobsCount > 0
                ? "bg-amber-50 text-amber-800 border-amber-300 hover:bg-amber-100"
                : "bg-neutral-50 text-neutral-600 border-neutral-200 hover:bg-neutral-100"
            }`}
          >
            <Activity className={`w-3 h-3 ${runningJobsCount > 0 ? "animate-spin text-amber-600" : "text-neutral-400"}`} />
            <span>{runningJobsCount > 0 ? `${runningJobsCount} Jobs Running` : "Jobs Idle"}</span>
            <ChevronDown className="w-2.5 h-2.5 text-neutral-400" />
          </button>

          {showJobsDropdown && (
            <div className="absolute right-0 mt-1.5 w-72 bg-white border border-neutral-200 rounded-lg shadow-lg p-2.5 z-20 text-xs">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100 font-semibold text-neutral-700">
                <span>Recent Jobs</span>
                <span className="text-[10px] text-neutral-400 font-mono">FastAPI Worker</span>
              </div>
              <div className="space-y-1.5">
                {jobs.map((job) => (
                  <div key={job.job_id} className="p-1.5 rounded bg-neutral-50 border border-neutral-100 flex items-center justify-between text-2xs">
                    <div>
                      <div className="font-mono font-medium text-neutral-800">{job.job_type}</div>
                      <div className="text-neutral-400 text-[10px]">{job.job_id}</div>
                    </div>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-emerald-100 text-emerald-800">
                      {job.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Verification Status Indicator */}
        <div className="flex items-center gap-1 text-2xs font-medium text-neutral-600">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          <span>Verification Online</span>
        </div>
      </div>
    </header>
  );
}
