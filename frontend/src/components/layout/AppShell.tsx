"use client";

import React from "react";
import { Navigation } from "./Navigation";
import { Header } from "./Header";
import { Breadcrumbs } from "./Breadcrumbs";
import { EvidenceProvider } from "../inspector/EvidenceContext";
import { EvidenceInspector } from "../inspector/EvidenceInspector";
import { FactCorrectionModal } from "../inspector/FactCorrectionModal";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <EvidenceProvider>
      <div className="flex h-screen w-screen overflow-hidden bg-neutral-50/50 text-neutral-900 font-sans">
        {/* Left Navigation Sidebar */}
        <Navigation />

        {/* Main Content Pane */}
        <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
          {/* Top Header */}
          <Header />

          {/* Subheader / Breadcrumbs bar */}
          <div className="h-10 border-b border-neutral-200/80 bg-white px-6 flex items-center justify-between flex-shrink-0">
            <Breadcrumbs />
          </div>

          {/* Scrollable Page Body */}
          <main className="flex-1 overflow-y-auto p-6 bg-neutral-50/60">
            <div className="max-w-7xl mx-auto w-full pb-12">
              {children}
            </div>
          </main>
        </div>

        {/* Global Slide-out Drawer and Modal */}
        <EvidenceInspector />
        <FactCorrectionModal />
      </div>
    </EvidenceProvider>
  );
}
