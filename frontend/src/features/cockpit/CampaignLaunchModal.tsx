"use client";

import React, { useState } from "react";
import { useCockpit } from "./CockpitContext";
import { X, Send, CheckCircle2, ShieldCheck, Mail, Users, Sparkles, Loader2 } from "lucide-react";

export function CampaignLaunchModal() {
  const {
    isOutreachModalOpen,
    setIsOutreachModalOpen,
    campaigns,
    activeCampaignId,
    filteredContacts,
    launchCampaignOutreach,
    campaignLaunchSuccess,
    resetCampaignLaunchState,
  } = useCockpit();

  const [isLaunching, setIsLaunching] = useState(false);

  if (!isOutreachModalOpen) return null;

  const currentCampaign = campaigns.find((c) => c.id === activeCampaignId) || campaigns[0];
  const verifiedCount = filteredContacts.filter((c) => c.emailStatus !== "missing").length;

  const handleLaunch = async () => {
    setIsLaunching(true);
    await launchCampaignOutreach();
    setIsLaunching(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in-50 duration-150">
      <div className="bg-gx-surface border border-gx-border rounded-2xl max-w-md w-full p-6 text-gx-ink shadow-xl space-y-6">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-gx-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gx-primary-soft border border-gx-primary-border flex items-center justify-center text-gx-primary">
              <Send className="w-4 h-4" />
            </div>
            <div>
              <div className="font-semibold text-gx-ink text-sm">Launch Outbound Campaign</div>
              <div className="text-[11px] text-gx-ink-secondary">{currentCampaign.name}</div>
            </div>
          </div>
          <button
            type="button"
            onClick={resetCampaignLaunchState}
            className="text-gx-ink-muted hover:text-gx-ink p-1 rounded-md hover:bg-gx-surface-soft transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {campaignLaunchSuccess ? (
          /* Success Screen */
          <div className="py-6 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-gx-success-soft border border-gx-success/30 flex items-center justify-center mx-auto text-gx-success shadow-sm animate-bounce">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="text-base font-semibold text-gx-ink">Campaign Dispatched!</div>
              <p className="text-xs text-gx-ink-secondary max-w-xs mx-auto leading-relaxed">
                Outreach emails have been queued and sent to {verifiedCount} verified decision makers across target accounts.
              </p>
            </div>
            <div className="pt-2">
              <button
                type="button"
                onClick={resetCampaignLaunchState}
                className="w-full bg-gx-primary hover:bg-gx-primary-hover text-white font-semibold text-xs py-2.5 rounded-lg transition-colors"
              >
                Back to Cockpit
              </button>
            </div>
          </div>
        ) : (
          /* Review & Confirmation Screen */
          <div className="space-y-5">
            <div className="bg-gx-surface-soft border border-gx-border rounded-xl p-4 space-y-3">
              <div className="text-xs font-semibold text-gx-ink flex items-center justify-between">
                <span>Campaign Summary</span>
                <span className="text-gx-success font-mono text-[11px] font-semibold">Ready to send</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-gx-surface border border-gx-border">
                  <div className="text-[10px] text-gx-ink-muted flex items-center gap-1 mb-1">
                    <Users className="w-3 h-3 text-gx-ink-muted" />
                    <span>Verified Contacts</span>
                  </div>
                  <div className="text-sm font-semibold text-gx-ink">{verifiedCount} personas</div>
                </div>

                <div className="p-2.5 rounded-lg bg-gx-surface border border-gx-border">
                  <div className="text-[10px] text-gx-ink-muted flex items-center gap-1 mb-1">
                    <Mail className="w-3 h-3 text-gx-ink-muted" />
                    <span>Emails Ready</span>
                  </div>
                  <div className="text-sm font-semibold text-gx-primary">{verifiedCount} drafts</div>
                </div>
              </div>

              <div className="space-y-1.5 pt-1 text-[11px] text-gx-ink-secondary">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-gx-success flex-shrink-0" />
                  <span>Verified via Hunter, Findymail &amp; Exreacher</span>
                </div>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-gx-primary flex-shrink-0" />
                  <span>Hyper-personalized hooks citing live company milestones</span>
                </div>
              </div>
            </div>

            {/* Strategy / Warmup note */}
            <div className="text-[11px] text-gx-ink-secondary bg-gx-surface-soft p-3 rounded-lg border border-gx-border leading-relaxed">
              Emails will be sent smoothly with mailbox warm-up safety limits (max 30 emails/day per domain) to preserve pristine inbox deliverability.
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 pt-1">
              <button
                type="button"
                onClick={resetCampaignLaunchState}
                className="flex-1 py-2.5 bg-gx-surface-soft hover:bg-gx-surface-hover border border-gx-border text-gx-ink rounded-lg text-xs font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isLaunching || verifiedCount === 0}
                onClick={handleLaunch}
                className="flex-1 py-2.5 bg-gx-primary hover:bg-gx-primary-hover disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all shadow-sm"
              >
                {isLaunching ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                    <span>Launching...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Confirm &amp; Launch</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
