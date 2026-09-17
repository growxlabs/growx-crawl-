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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in-50 duration-150">
      <div className="bg-[#121622] border border-[#232a3c] rounded-2xl max-w-md w-full p-6 text-slate-200 shadow-2xl space-y-6">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#1e2434]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-950/80 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Send className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">Launch Outbound Campaign</div>
              <div className="text-[11px] text-slate-400">{currentCampaign.name}</div>
            </div>
          </div>
          <button
            onClick={resetCampaignLaunchState}
            className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-[#1a2030]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {campaignLaunchSuccess ? (
          /* Success Screen */
          <div className="py-6 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-emerald-950/90 border border-emerald-400/50 flex items-center justify-center mx-auto text-emerald-400 shadow-lg shadow-emerald-950/50 animate-bounce">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <div className="text-base font-bold text-white">Campaign Dispatched!</div>
              <p className="text-xs text-slate-300 max-w-xs mx-auto leading-relaxed">
                Outreach emails have been queued and sent to {verifiedCount} verified decision makers across target accounts.
              </p>
            </div>
            <div className="pt-2">
              <button
                onClick={resetCampaignLaunchState}
                className="w-full bg-[#00c288] hover:bg-[#00d696] text-slate-950 font-bold text-xs py-2.5 rounded-lg transition-colors"
              >
                Back to Cockpit
              </button>
            </div>
          </div>
        ) : (
          /* Review & Confirmation Screen */
          <div className="space-y-5">
            <div className="bg-[#161c29] border border-[#232d42] rounded-xl p-4 space-y-3">
              <div className="text-xs font-semibold text-white flex items-center justify-between">
                <span>Campaign Summary</span>
                <span className="text-emerald-400 font-mono text-[11px]">Ready to send</span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-[#111520] border border-[#1e2536]">
                  <div className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
                    <Users className="w-3 h-3 text-slate-400" />
                    <span>Verified Contacts</span>
                  </div>
                  <div className="text-sm font-bold text-white">{verifiedCount} personas</div>
                </div>

                <div className="p-2.5 rounded-lg bg-[#111520] border border-[#1e2536]">
                  <div className="text-[10px] text-slate-400 flex items-center gap-1 mb-1">
                    <Mail className="w-3 h-3 text-slate-400" />
                    <span>Emails Ready</span>
                  </div>
                  <div className="text-sm font-bold text-emerald-400">{verifiedCount} drafts</div>
                </div>
              </div>

              <div className="space-y-1.5 pt-1 text-[11px] text-slate-300">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span>Verified via Hunter, Findymail & Exreacher</span>
                </div>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  <span>Hyper-personalized hooks citing live company milestones</span>
                </div>
              </div>
            </div>

            {/* Strategy / Warmup note */}
            <div className="text-[11px] text-slate-400 bg-[#12151e] p-3 rounded-lg border border-[#1c2230] leading-relaxed">
              Emails will be sent smoothly with mailbox warm-up safety limits (max 30 emails/day per domain) to preserve pristine inbox deliverability.
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 pt-1">
              <button
                type="button"
                onClick={resetCampaignLaunchState}
                className="flex-1 py-2.5 bg-[#171c28] hover:bg-[#202738] text-slate-300 rounded-lg text-xs font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isLaunching || verifiedCount === 0}
                onClick={handleLaunch}
                className="flex-1 py-2.5 bg-[#00c288] hover:bg-[#00d696] disabled:opacity-50 text-slate-950 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-950/40"
              >
                {isLaunching ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                    <span>Launching...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Confirm & Launch</span>
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
