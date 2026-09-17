"use client";

import React, { useState } from "react";
import { Search, Target, Send, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { useCockpit } from "@/features/cockpit/CockpitContext";

export function ProjectLauncher() {
  const { createProject, isCreatingProject } = useCockpit();
  const [domainInput, setDomainInput] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [stepIndex, setStepIndex] = useState(0);

  const STEPS = [
    "Analyzing company domain & website...",
    "Extracting core positioning & value propositions...",
    "Mapping competitor landscape...",
    "Assembling target accounts and campaign drafts...",
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = domainInput.trim();
    if (!trimmed) {
      setErrorMsg("Please enter a company website domain (e.g. acme.com)");
      return;
    }

    setErrorMsg("");

    // Step cycle animation while creating
    const timer = setInterval(() => {
      setStepIndex((prev) => (prev < STEPS.length - 1 ? prev + 1 : prev));
    }, 400);

    try {
      await createProject(trimmed);
    } finally {
      clearInterval(timer);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 md:p-12 overflow-y-auto bg-gx-canvas select-none">
      <div className="max-w-2xl w-full space-y-8 animate-in fade-in-50 duration-200">
        {/* Header Hero Section */}
        <div className="space-y-3 text-left">
          <div className="text-[11px] font-semibold text-gx-ink-muted uppercase tracking-widest">
            AutoGTM
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-gx-ink">
            Let&apos;s find your first customers
          </h1>
          <p className="text-sm md:text-base text-gx-ink-secondary leading-relaxed max-w-xl">
            Your AI go-to-market agent. Enter your company website and we&apos;ll
            spin up your project &mdash; research, campaigns and outreach, all
            set up for you.
          </p>
        </div>

        {/* Website Form */}
        <form onSubmit={handleSubmit} className="space-y-2">
          <label
            htmlFor="company-domain"
            className="block text-xs font-medium text-gx-ink-secondary"
          >
            Your company website
          </label>

          <div className="flex flex-col sm:flex-row items-stretch gap-2.5">
            <div className="flex-1 relative">
              <input
                id="company-domain"
                type="text"
                value={domainInput}
                onChange={(e) => {
                  setDomainInput(e.target.value);
                  if (errorMsg) setErrorMsg("");
                }}
                disabled={isCreatingProject}
                placeholder="yourcompany.com"
                className="w-full h-11 px-4 rounded-xl bg-gx-surface border border-gx-border text-sm text-gx-ink placeholder:text-gx-ink-muted outline-none focus:border-gx-primary focus:ring-2 focus:ring-gx-primary/20 transition-all"
                autoFocus
              />
            </div>

            <button
              type="submit"
              disabled={isCreatingProject}
              className="h-11 px-6 rounded-xl bg-gx-primary hover:bg-gx-primary-hover disabled:opacity-60 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-sm transition-all hover:scale-[1.01] active:scale-[0.99] flex-shrink-0"
            >
              {isCreatingProject ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Spinning up project...</span>
                </>
              ) : (
                <>
                  <span>Create my project</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {errorMsg && (
            <div className="text-xs text-gx-danger pt-1">{errorMsg}</div>
          )}

          {isCreatingProject && (
            <div className="p-3 bg-gx-surface border border-gx-border rounded-xl text-xs text-gx-ink-secondary flex items-center gap-2.5 animate-in fade-in duration-150">
              <Sparkles className="w-4 h-4 text-gx-primary animate-pulse flex-shrink-0" />
              <span>{STEPS[stepIndex]}</span>
            </div>
          )}
        </form>

        {/* 3 Value Proposition Cards matching Explee */}
        <div className="space-y-3 pt-2">
          {/* Card 1: Company Research */}
          <div className="p-4 rounded-xl bg-gx-surface border border-gx-border hover:border-gx-border-strong transition-colors flex items-start gap-4 shadow-2xs">
            <div className="w-9 h-9 rounded-lg bg-gx-surface-soft border border-gx-border flex items-center justify-center text-gx-ink-secondary flex-shrink-0">
              <Search className="w-4 h-4 text-gx-ink-secondary" />
            </div>
            <div className="space-y-0.5 min-w-0">
              <div className="text-sm font-semibold text-gx-ink">
                We research your company
              </div>
              <p className="text-xs text-gx-ink-secondary leading-relaxed">
                Pull your positioning and map the market in seconds.
              </p>
            </div>
          </div>

          {/* Card 2: Targeted Campaigns */}
          <div className="p-4 rounded-xl bg-gx-surface border border-gx-border hover:border-gx-border-strong transition-colors flex items-start gap-4 shadow-2xs">
            <div className="w-9 h-9 rounded-lg bg-gx-surface-soft border border-gx-border flex items-center justify-center text-gx-ink-secondary flex-shrink-0">
              <Target className="w-4 h-4 text-gx-ink-secondary" />
            </div>
            <div className="space-y-0.5 min-w-0">
              <div className="text-sm font-semibold text-gx-ink">
                We build targeted campaigns
              </div>
              <p className="text-xs text-gx-ink-secondary leading-relaxed">
                Ready-made segments of the customers worth reaching.
              </p>
            </div>
          </div>

          {/* Card 3: Outbound Outreach */}
          <div className="p-4 rounded-xl bg-gx-surface border border-gx-border hover:border-gx-border-strong transition-colors flex items-start gap-4 shadow-2xs">
            <div className="w-9 h-9 rounded-lg bg-gx-surface-soft border border-gx-border flex items-center justify-center text-gx-ink-secondary flex-shrink-0">
              <Send className="w-4 h-4 text-gx-ink-secondary" />
            </div>
            <div className="space-y-0.5 min-w-0">
              <div className="text-sm font-semibold text-gx-ink">
                We reach out for you
              </div>
              <p className="text-xs text-gx-ink-secondary leading-relaxed">
                Personalized emails to the right people, on autopilot.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
