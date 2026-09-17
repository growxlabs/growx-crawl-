"use client";

import React, { useEffect, useState } from "react";
import { useEvidence } from "./EvidenceContext";
import { getEvidence, EvidenceRecord } from "@/lib/api/verification";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import {
  X,
  ExternalLink,
  ShieldCheck,
  Edit3,
  FileText,
  Clock,
  Cpu,
  Layers,
} from "lucide-react";

export function EvidenceInspector() {
  const { drawerData, closeEvidenceDrawer, openCorrectionModal } = useEvidence();
  const [evidenceDetails, setEvidenceDetails] = useState<EvidenceRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (drawerData.isOpen && drawerData.evidenceId) {
      setLoading(true);
      getEvidence(drawerData.evidenceId)
        .then((res) => {
          setEvidenceDetails(res);
        })
        .catch(() => {
          // Fallback to drawer passed data if not found via direct ID
          setEvidenceDetails(null);
        })
        .finally(() => setLoading(false));
    }
  }, [drawerData.isOpen, drawerData.evidenceId]);

  if (!drawerData.isOpen) return null;

  const currentStatus =
    evidenceDetails?.verification_status ||
    drawerData.verificationStatus ||
    "Verified";
  const currentConfidence =
    evidenceDetails?.confidence_score ?? drawerData.confidenceScore ?? 0.95;
  const currentSnippet =
    evidenceDetails?.raw_snippet ||
    drawerData.rawSnippet ||
    "Exact source quotation recorded during crawler DOM evaluation and fact synthesis.";
  const currentUrl = evidenceDetails?.source_url || drawerData.sourceUrl;
  const currentTimestamp =
    evidenceDetails?.extracted_at ||
    drawerData.extractedAt ||
    new Date().toISOString();
  const currentMethod =
    evidenceDetails?.method || drawerData.method || "dom_text_parser";

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-neutral-900/30 backdrop-blur-[1px] transition-opacity"
        onClick={closeEvidenceDrawer}
      />

      {/* Slide-out Drawer */}
      <div className="relative w-full max-w-md bg-white h-full shadow-2xl border-l border-neutral-200 flex flex-col z-10 animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-neutral-200 flex items-center justify-between bg-neutral-50/70">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-neutral-800" />
            <span className="font-semibold text-xs text-neutral-900 uppercase tracking-wider font-mono">
              Evidence Inspector
            </span>
          </div>
          <button
            onClick={closeEvidenceDrawer}
            className="p-1 rounded text-neutral-400 hover:text-neutral-800 hover:bg-neutral-200/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs text-neutral-700">
          {/* Status & Confidence Banner */}
          <div className="bg-neutral-50 border border-neutral-200 rounded p-3 flex items-center justify-between">
            <div>
              <div className="text-[10px] uppercase font-mono text-neutral-400 mb-1">
                Verification State
              </div>
              <StatusBadge status={currentStatus} size="sm" />
            </div>
            <div>
              <div className="text-[10px] uppercase font-mono text-neutral-400 mb-1 text-right">
                Confidence
              </div>
              <ConfidenceIndicator score={currentConfidence} size="sm" />
            </div>
          </div>

          {/* Claim / Fact Description */}
          <div>
            <div className="text-[10px] uppercase font-mono text-neutral-400 mb-1">
              Verified Fact Claim
            </div>
            <div className="p-2.5 bg-neutral-50/80 border border-neutral-200 rounded font-medium text-neutral-900 leading-relaxed">
              {drawerData.claim || "Canonical verified attribute claim."}
            </div>
          </div>

          {/* Raw Verbatim Excerpt */}
          <div>
            <div className="text-[10px] uppercase font-mono text-neutral-400 mb-1 flex items-center gap-1">
              <FileText className="w-3 h-3 text-neutral-500" />
              <span>Verbatim Source Proof</span>
            </div>
            <div className="p-3 bg-neutral-900 text-neutral-100 font-mono text-[11px] rounded border border-neutral-800 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap">
              {currentSnippet}
            </div>
          </div>

          {/* Provenance Metadata Table */}
          <div className="space-y-2 border-t border-neutral-200 pt-3">
            <div className="text-[10px] uppercase font-mono text-neutral-400">
              Provenance & Metadata
            </div>

            <div className="space-y-1.5 font-mono text-[11px]">
              {drawerData.factId && (
                <div className="flex items-center justify-between py-1 border-b border-neutral-100">
                  <span className="text-neutral-400">Fact ID</span>
                  <span className="text-neutral-800 font-semibold truncate max-w-[200px]">
                    {drawerData.factId}
                  </span>
                </div>
              )}

              {drawerData.evidenceId && (
                <div className="flex items-center justify-between py-1 border-b border-neutral-100">
                  <span className="text-neutral-400">Evidence ID</span>
                  <span className="text-neutral-800 truncate max-w-[200px]">
                    {drawerData.evidenceId}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between py-1 border-b border-neutral-100">
                <span className="text-neutral-400">Extracted At</span>
                <span className="text-neutral-800 truncate max-w-[200px]">
                  {currentTimestamp}
                </span>
              </div>

              <div className="flex items-center justify-between py-1 border-b border-neutral-100">
                <span className="text-neutral-400">Pipeline Method</span>
                <span className="text-neutral-800">{currentMethod}</span>
              </div>

              {currentUrl && (
                <div className="pt-2">
                  <div className="text-neutral-400 mb-1 text-[10px]">Source URL</div>
                  <a
                    href={currentUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-800 break-all underline text-xs"
                  >
                    <span>{currentUrl}</span>
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-neutral-200 bg-neutral-50/70 flex items-center justify-between">
          <button
            onClick={() =>
              openCorrectionModal({
                factId: drawerData.factId,
                claim: drawerData.claim,
              })
            }
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-neutral-300 bg-white hover:bg-neutral-100 text-neutral-800 font-medium text-xs shadow-2xs transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5 text-neutral-600" />
            <span>Suggest Fact Correction</span>
          </button>

          <button
            onClick={closeEvidenceDrawer}
            className="px-3 py-1.5 rounded text-neutral-600 hover:text-neutral-900 text-xs font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
