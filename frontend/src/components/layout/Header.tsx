"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  Search,
  Activity,
  ChevronDown,
  CheckCircle2,
  Sparkles,
  Sliders,
  LogOut,
  User,
} from "lucide-react";
import { listProjects, Project } from "@/lib/api/projects";
import { listJobs, JobItem } from "@/lib/api/jobs";
import { formatActivityMessage } from "@/lib/product-language";

export function Header() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("prj_growx_mfg_india");
  const [jobs, setJobs] = useState<JobItem[]>([]);
  const [showActivityPopover, setShowActivityPopover] = useState<boolean>(false);
  const [showProfileMenu, setShowProfileMenu] = useState<boolean>(false);

  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listProjects()
      .then((projs) => {
        if (projs && projs.length > 0) {
          setProjects(projs);
          // Default to first project if available
          setSelectedProject(projs[0].id);
        }
      })
      .catch(() => {});

    listJobs()
      .then((j) => {
        setJobs(j);
      })
      .catch(() => {});
  }, []);

  // Close popovers on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowActivityPopover(false);
        setShowProfileMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const runningJobs = jobs.filter((j) => j.status === "running");
  const activeCount = runningJobs.length;

  return (
    <header className="h-14 border-b border-neutral-200 bg-white px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Active Project Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-medium text-neutral-500">
          <span className="hidden sm:inline">Active Project:</span>
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="text-neutral-900 font-semibold bg-neutral-100 hover:bg-neutral-200/80 border border-neutral-300 rounded px-2.5 py-1 text-xs outline-none cursor-pointer transition-colors"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
            {projects.length === 0 && (
              <option value="prj_growx_mfg_india">
                GrowxLabs — Manufacturing India
              </option>
            )}
          </select>
        </div>
      </div>

      {/* Center: Clean Search */}
      <div className="w-80 md:w-96 relative">
        <Search className="w-3.5 h-3.5 text-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          placeholder="Search accounts, people, or signals..."
          className="w-full bg-neutral-50 border border-neutral-200 rounded-md pl-8 pr-3 py-1.5 text-xs placeholder:text-neutral-400 text-neutral-800 outline-none focus:border-neutral-400 focus:bg-white transition-colors"
        />
      </div>

      {/* Right: Activity & Profile */}
      <div className="flex items-center gap-3" ref={popoverRef}>
        {/* Activity Indicator */}
        <div className="relative">
          <button
            onClick={() => {
              setShowActivityPopover(!showActivityPopover);
              setShowProfileMenu(false);
            }}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium border transition-colors ${
              activeCount > 0
                ? "bg-neutral-900 text-white border-neutral-900 hover:bg-neutral-800"
                : "bg-neutral-50 text-neutral-700 border-neutral-200 hover:bg-neutral-100"
            }`}
          >
            <Activity
              className={`w-3.5 h-3.5 ${
                activeCount > 0 ? "animate-spin text-white" : "text-neutral-500"
              }`}
            />
            <span>{activeCount > 0 ? `Activity · ${activeCount}` : "Activity"}</span>
            <ChevronDown className="w-3 h-3 opacity-60" />
          </button>

          {showActivityPopover && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-neutral-200 rounded-lg shadow-xl p-3 z-30 animate-in fade-in-50 duration-150">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-neutral-100 text-xs font-semibold text-neutral-900">
                <span>Current Activity</span>
                <span className="text-[11px] font-normal text-neutral-400">
                  {activeCount > 0 ? "In progress" : "All systems ready"}
                </span>
              </div>

              {activeCount > 0 ? (
                <div className="space-y-2">
                  {runningJobs.map((job) => (
                    <div
                      key={job.job_id}
                      className="p-2.5 rounded bg-neutral-50 border border-neutral-200/80 flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5">
                        <div className="font-medium text-neutral-900">
                          {formatActivityMessage(job.job_type, job.prospects_updated)}
                        </div>
                        <div className="text-[10px] text-neutral-400">
                          Started {new Date(job.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] bg-neutral-200 text-neutral-800 font-medium">
                        Running
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-4 text-center space-y-1.5">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 mx-auto" />
                  <div className="text-xs font-medium text-neutral-800">
                    All intelligence up to date
                  </div>
                  <div className="text-[11px] text-neutral-500 max-w-[220px] mx-auto leading-normal">
                    Target accounts, verified personas, and market signals are fresh.
                  </div>
                </div>
              )}

              <div className="mt-3 pt-2 border-t border-neutral-100 text-right">
                <Link
                  href="/ops"
                  onClick={() => setShowActivityPopover(false)}
                  className="text-[11px] text-neutral-500 hover:text-neutral-900 underline"
                >
                  View operations console &rarr;
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Operator Profile Menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowProfileMenu(!showProfileMenu);
              setShowActivityPopover(false);
            }}
            className="w-8 h-8 rounded-full bg-neutral-100 hover:bg-neutral-200 border border-neutral-300 flex items-center justify-center text-xs font-semibold text-neutral-800 transition-colors"
            title="GrowxLabs Operator"
          >
            GL
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-neutral-200 rounded-lg shadow-xl p-2 z-30 animate-in fade-in-50 duration-150 text-xs">
              <div className="px-2.5 py-2 border-b border-neutral-100">
                <div className="font-semibold text-neutral-900">GrowxLabs Operator</div>
                <div className="text-[11px] text-neutral-400">operator@growxlabs.tech</div>
              </div>

              <div className="py-1 space-y-0.5">
                <Link
                  href="/company/overview"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded hover:bg-neutral-100 text-neutral-700"
                >
                  <User className="w-3.5 h-3.5 text-neutral-400" />
                  <span>My Company</span>
                </Link>
                <Link
                  href="/ops"
                  onClick={() => setShowProfileMenu(false)}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded hover:bg-neutral-100 text-neutral-700"
                >
                  <Sliders className="w-3.5 h-3.5 text-neutral-400" />
                  <span>Operations Console</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
