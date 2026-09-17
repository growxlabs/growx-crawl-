"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  Building2,
  FolderGit2,
  Users,
  Send,
  Mail,
  Calendar,
  DollarSign,
  CreditCard,
  Lock,
  ChevronRight,
  Database,
  BarChart3,
  GitCompare,
  History,
} from "lucide-react";

export function Navigation() {
  const pathname = usePathname();

  const isCompanyActive = pathname.startsWith("/company");
  const isProjectsActive = pathname.startsWith("/projects");
  const isProspectsActive = pathname.startsWith("/prospects");
  const isIntelligenceActive = pathname.startsWith("/intelligence");

  return (
    <aside className="w-64 border-r border-neutral-200 bg-white flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="h-14 px-4 border-b border-neutral-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-neutral-900 flex items-center justify-center text-white font-bold text-xs tracking-tighter">
            GX
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-xs text-neutral-900 tracking-tight leading-none">
              GrowX AutoGTM
            </span>
            <span className="text-[10px] text-neutral-400 font-mono">v1.14 Intelligence</span>
          </div>
        </div>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-neutral-100 text-neutral-600 border border-neutral-200">
          PROD
        </span>
      </div>

      {/* Main Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {/* Core Intelligence & Operations */}
        <div>
          <div className="px-2 mb-2 text-[10px] font-semibold text-neutral-400 uppercase tracking-wider font-mono">
            Intelligence Platform
          </div>
          <nav className="space-y-1">
            <Link
              href="/intelligence"
              className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                isIntelligenceActive
                  ? "bg-neutral-900 text-white"
                  : "text-neutral-700 hover:bg-neutral-100"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Compass className="w-3.5 h-3.5" />
                <span>Intelligence Explorer</span>
              </div>
            </Link>

            {/* My Company Group */}
            <div>
              <Link
                href="/company/overview"
                className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                  isCompanyActive
                    ? "bg-neutral-100 text-neutral-900 font-semibold"
                    : "text-neutral-700 hover:bg-neutral-100"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Building2 className="w-3.5 h-3.5 text-neutral-500" />
                  <span>My Company</span>
                </div>
                <ChevronRight className={`w-3 h-3 transition-transform ${isCompanyActive ? "rotate-90 text-neutral-900" : "text-neutral-400"}`} />
              </Link>

              {isCompanyActive && (
                <div className="ml-5 pl-2 mt-1 space-y-0.5 border-l border-neutral-200">
                  <Link
                    href="/company/overview"
                    className={`block px-2 py-1 rounded text-2xs transition-colors ${
                      pathname === "/company/overview"
                        ? "text-neutral-900 font-semibold bg-neutral-100"
                        : "text-neutral-500 hover:text-neutral-900"
                    }`}
                  >
                    Overview
                  </Link>
                  <Link
                    href="/company/analysis"
                    className={`block px-2 py-1 rounded text-2xs transition-colors ${
                      pathname === "/company/analysis"
                        ? "text-neutral-900 font-semibold bg-neutral-100"
                        : "text-neutral-500 hover:text-neutral-900"
                    }`}
                  >
                    Seller Analysis
                  </Link>
                  <Link
                    href="/company/competitors"
                    className={`block px-2 py-1 rounded text-2xs transition-colors ${
                      pathname === "/company/competitors"
                        ? "text-neutral-900 font-semibold bg-neutral-100"
                        : "text-neutral-500 hover:text-neutral-900"
                    }`}
                  >
                    Competitors Graph
                  </Link>
                  <Link
                    href="/company/history"
                    className={`block px-2 py-1 rounded text-2xs transition-colors ${
                      pathname === "/company/history"
                        ? "text-neutral-900 font-semibold bg-neutral-100"
                        : "text-neutral-500 hover:text-neutral-900"
                    }`}
                  >
                    Historical Timeline
                  </Link>
                </div>
              )}
            </div>

            {/* Projects */}
            <Link
              href="/projects"
              className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                isProjectsActive
                  ? "bg-neutral-900 text-white"
                  : "text-neutral-700 hover:bg-neutral-100"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <FolderGit2 className="w-3.5 h-3.5" />
                <span>Projects</span>
              </div>
            </Link>

            {/* Prospects */}
            <Link
              href="/prospects"
              className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                isProspectsActive
                  ? "bg-neutral-900 text-white"
                  : "text-neutral-700 hover:bg-neutral-100"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Users className="w-3.5 h-3.5" />
                <span>Ranked Prospects</span>
              </div>
            </Link>
          </nav>
        </div>

        {/* Future AutoGTM Execution Areas (Locked) */}
        <div>
          <div className="px-2 mb-2 text-[10px] font-semibold text-neutral-400 uppercase tracking-wider font-mono">
            Execution Modules
          </div>
          <div className="space-y-1">
            {[
              { name: "Campaigns", icon: Send, phase: "Phase 16" },
              { name: "Mail", icon: Mail, phase: "Phase 17" },
              { name: "Meetings", icon: Calendar, phase: "Phase 18" },
              { name: "Opportunities", icon: DollarSign, phase: "Phase 19" },
              { name: "Credits & Billing", icon: CreditCard, phase: "Phase 20" },
            ].map((item) => (
              <div
                key={item.name}
                className="flex items-center justify-between px-2.5 py-1.5 rounded text-xs text-neutral-400 cursor-not-allowed opacity-60"
                title={`${item.name} - Scheduled for ${item.phase}`}
              >
                <div className="flex items-center gap-2.5">
                  <item.icon className="w-3.5 h-3.5 text-neutral-400" />
                  <span>{item.name}</span>
                </div>
                <div className="flex items-center gap-1 text-[9px] font-mono text-neutral-400">
                  <Lock className="w-2.5 h-2.5" />
                  <span>{item.phase}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer / System Health */}
      <div className="p-3 border-t border-neutral-200 bg-neutral-50/50">
        <div className="flex items-center justify-between text-[11px] text-neutral-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
            FastAPI: 7411
          </span>
          <span className="font-mono text-[10px]">254 Tests Passing</span>
        </div>
      </div>
    </aside>
  );
}
