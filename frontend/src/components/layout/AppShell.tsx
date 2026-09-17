"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { ThemeProvider } from "@/context/ThemeContext";
import { CockpitProvider } from "@/features/cockpit/CockpitContext";
import { AutoGTMWorkflowSidebar } from "@/features/autogtm-workflow/AutoGTMWorkflowSidebar";
import { CockpitHeader } from "@/features/cockpit/CockpitHeader";
import { EvidenceProvider } from "../inspector/EvidenceContext";
import { EvidenceInspector } from "../inspector/EvidenceInspector";
import { FactCorrectionModal } from "../inspector/FactCorrectionModal";
import { CompetitorModal } from "@/features/cockpit/CompetitorModal";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const isOps = pathname.startsWith("/ops");

  if (isOps) {
    return (
      <ThemeProvider>
        <EvidenceProvider>
          <div className="flex h-screen w-screen overflow-hidden bg-[#0a0c10] text-slate-100 font-sans">
            <main className="flex-1 overflow-y-auto bg-[#0a0c10]">
              {children}
            </main>
          </div>
        </EvidenceProvider>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <EvidenceProvider>
        <CockpitProvider>
          <div className="flex h-screen w-screen overflow-hidden bg-gx-canvas text-gx-ink font-sans">
            {/* Workflow Stages Sidebar */}
            <AutoGTMWorkflowSidebar />

            {/* Right Main Column (Top Stepper + Unified Cockpit Area) */}
            <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-gx-canvas">
              <CockpitHeader />
              <main className="flex-1 min-h-0 overflow-hidden flex flex-col bg-gx-canvas">
                {children}
              </main>
            </div>

            {/* Global Slide-out Drawer and Modals */}
            <EvidenceInspector />
            <FactCorrectionModal />
            <CompetitorModal />
          </div>
        </CockpitProvider>
      </EvidenceProvider>
    </ThemeProvider>
  );
}
