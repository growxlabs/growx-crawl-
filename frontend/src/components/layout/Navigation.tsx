"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Building2,
  FolderGit2,
  Users,
  Send,
  Mail,
  Calendar,
  DollarSign,
  Lock,
  ChevronRight,
  Terminal,
} from "lucide-react";

export function Navigation() {
  const pathname = usePathname();

  const isCompanyActive =
    pathname.startsWith("/company") ||
    pathname.startsWith("/app/company");
  const isProjectsActive =
    pathname.startsWith("/projects") ||
    pathname.startsWith("/app/projects");
  const isProspectsActive =
    pathname.startsWith("/prospects") ||
    pathname.startsWith("/app/prospects");
  const isOpsActive = pathname.startsWith("/ops");

  // Keep My Company expanded if currently visiting any company page
  const [companyExpanded, setCompanyExpanded] = useState<boolean>(true);

  return (
    <aside className="w-64 border-r border-neutral-200 bg-white flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="h-14 px-4 border-b border-neutral-200 flex items-center justify-between">
        <Link href="/projects" className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-neutral-900 flex items-center justify-center text-white font-bold text-xs tracking-tighter">
            GX
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm text-neutral-900 tracking-tight leading-tight">
              GrowX
            </span>
            <span className="text-[10px] text-neutral-400">AutoGTM Operating System</span>
          </div>
        </Link>
      </div>

      {/* Main Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
        <nav className="space-y-1">
          {/* My Company Group */}
          <div>
            <button
              onClick={() => setCompanyExpanded(!companyExpanded)}
              className={`w-full flex items-center justify-between px-2.5 py-2 rounded text-xs font-medium transition-colors ${
                isCompanyActive
                  ? "bg-neutral-100 text-neutral-900 font-semibold"
                  : "text-neutral-700 hover:bg-neutral-50"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Building2 className="w-4 h-4 text-neutral-500" />
                <span>My Company</span>
              </div>
              <ChevronRight
                className={`w-3.5 h-3.5 text-neutral-400 transition-transform ${
                  companyExpanded ? "rotate-90 text-neutral-800" : ""
                }`}
              />
            </button>

            {companyExpanded && (
              <div className="ml-5 pl-2 mt-1 space-y-0.5 border-l border-neutral-200">
                <Link
                  href="/company/overview"
                  className={`block px-2.5 py-1.5 rounded text-xs transition-colors ${
                    pathname === "/company/overview"
                      ? "text-neutral-900 font-semibold bg-neutral-100"
                      : "text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50"
                  }`}
                >
                  Overview
                </Link>
                <Link
                  href="/company/positioning"
                  className={`block px-2.5 py-1.5 rounded text-xs transition-colors ${
                    pathname === "/company/positioning" || pathname === "/company/analysis"
                      ? "text-neutral-900 font-semibold bg-neutral-100"
                      : "text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50"
                  }`}
                >
                  Positioning
                </Link>
                <Link
                  href="/company/competitors"
                  className={`block px-2.5 py-1.5 rounded text-xs transition-colors ${
                    pathname === "/company/competitors"
                      ? "text-neutral-900 font-semibold bg-neutral-100"
                      : "text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50"
                  }`}
                >
                  Competitors
                </Link>
                <Link
                  href="/company/changes"
                  className={`block px-2.5 py-1.5 rounded text-xs transition-colors ${
                    pathname === "/company/changes" || pathname === "/company/history"
                      ? "text-neutral-900 font-semibold bg-neutral-100"
                      : "text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50"
                  }`}
                >
                  Changes
                </Link>
              </div>
            )}
          </div>

          {/* Projects */}
          <Link
            href="/projects"
            className={`flex items-center justify-between px-2.5 py-2 rounded text-xs font-medium transition-colors ${
              isProjectsActive
                ? "bg-neutral-900 text-white font-semibold"
                : "text-neutral-700 hover:bg-neutral-100"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <FolderGit2 className="w-4 h-4" />
              <span>Projects</span>
            </div>
          </Link>

          {/* Prospects */}
          <Link
            href="/prospects"
            className={`flex items-center justify-between px-2.5 py-2 rounded text-xs font-medium transition-colors ${
              isProspectsActive
                ? "bg-neutral-900 text-white font-semibold"
                : "text-neutral-700 hover:bg-neutral-100"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Users className="w-4 h-4" />
              <span>Prospects</span>
            </div>
          </Link>
        </nav>

        {/* GTM Progression Modules (Calm, Upcoming - No Phase Numbers) */}
        <div className="pt-2 border-t border-neutral-100 space-y-1">
          {[
            { name: "Campaigns", icon: Send },
            { name: "Mail", icon: Mail },
            { name: "Meetings", icon: Calendar },
            { name: "Opportunities", icon: DollarSign },
          ].map((item) => (
            <div
              key={item.name}
              className="flex items-center justify-between px-2.5 py-2 rounded text-xs text-neutral-400 cursor-not-allowed select-none opacity-70"
              title={`${item.name} · Available in upcoming workflow`}
            >
              <div className="flex items-center gap-2.5">
                <item.icon className="w-4 h-4 text-neutral-400" />
                <span>{item.name}</span>
              </div>
              <div className="flex items-center gap-1 text-[10px] text-neutral-400">
                <Lock className="w-3 h-3" />
                <span>Upcoming</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer / Ops Console Entry */}
      <div className="p-3 border-t border-neutral-200 bg-neutral-50/50">
        <Link
          href="/ops"
          className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
            isOpsActive
              ? "bg-neutral-900 text-white font-semibold"
              : "text-neutral-600 hover:bg-neutral-200/70 hover:text-neutral-900"
          }`}
          title="Open Engineering & Operations Console"
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-neutral-500" />
            <span>Operations Console</span>
          </div>
          <span className="text-[10px] font-mono text-neutral-400">/ops</span>
        </Link>
      </div>
    </aside>
  );
}
