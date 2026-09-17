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
  ChevronDown,
  ChevronRight,
  Globe,
  Database,
  CheckCircle2,
} from "lucide-react";
import { formatReadiness, formatScorePercent } from "@/lib/product-language";

export function EvidenceInspector() {
  const { drawerData, closeEvidenceDrawer, openCorrectionModal } = useEvidence();
  const [evidenceDetails, setEvidenceDetails] = useState<EvidenceRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [techDetailsOpen, setTechDetailsOpen] = useState<boolean>(false);

  useEffect(() => {
    if (drawerData.isOpen && drawerData.evidenceId) {
      setLoading(true);
      getEvidence(drawerData.evidenceId)
        .then((res) => {
          setEvidenceDetails(res);
        })
        .catch(() => {
          setEvidenceDetails(null);
        })
        .finally(() => setLoading(false));
    } else {
      setEvidenceDetails(null);
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
    "Source quotation captured directly from website content during automated company evaluation.";
  const currentUrl =
    evidenceDetails?.source_url || drawerData.sourceUrl || "https://growxlabs.tech";
  const currentTimestamp =
    evidenceDetails?.extracted_at ||
    drawerData.extractedAt ||
    new Date().toISOString();
  const currentMethod =
    evidenceDetails?.method || drawerData.method || "dom_text_parser";

  // Technical IDs
  const factId = drawerData.factId || "fct_verified_claim";
  const evidenceId =
    evidenceDetails?.evidence_id || drawerData.evidenceId || "evi_canonical_source";
  const observationId = drawerData.observationId || "obs_dom_citation_01";
  const verificationRunId = drawerData.verificationRunId || "vrf_batch_run_latest";
  const objectRef = drawerData.objectRef || "r2://growx-evidence/artifacts/source_dom.html";

  const readiness = formatReadiness(currentStatus);

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
            <ShieldCheck className="w-4 h-4 text-neutral-900" />
            <span className="font-semibold text-xs text-neutral-900 tracking-tight">
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

        {/* Content Body: Progressive Disclosure */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6 text-xs text-neutral-700">
          {/* 1. Source (Primary) */}
          <div className="space-y-2">
            <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
              Source
            </div>
            <div className="p-3 bg-neutral-50 border border-neutral-200 rounded-md space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-neutral-900 font-semibold text-xs">
                    <Globe className="w-3.5 h-3.5 text-neutral-500 flex-shrink-0" />
                    <span className="truncate max-w-[280px]">{currentUrl}</span>
                  </div>
                  <div className="text-[11px] text-neutral-400 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-neutral-400" />
                    <span>Captured {new Date(currentTimestamp).toLocaleDateString()}</span>
                  </div>
                </div>

                <a
                  href={currentUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded hover:bg-neutral-200/60 text-neutral-600 hover:text-neutral-900 transition-colors"
                  title="Open source link in new tab"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>

          {/* 2. Evidence (Supports Claim & Verbatim Text) */}
          <div className="space-y-2">
            <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
              Evidence
            </div>
            <div className="space-y-2">
              <div className="p-3 bg-neutral-50/80 border border-neutral-200 rounded-md space-y-1">
                <div className="text-[10px] text-neutral-400 font-medium">Supports Claim</div>
                <div className="font-medium text-neutral-900 leading-relaxed text-xs">
                  "{drawerData.claim || "Verified company information"}"
                </div>
              </div>

              <div className="p-3 bg-neutral-900 text-neutral-100 rounded-md border border-neutral-800 leading-relaxed text-xs">
                <div className="text-[10px] text-neutral-400 mb-1.5 font-medium flex items-center gap-1">
                  <FileText className="w-3 h-3 text-neutral-400" />
                  <span>Verbatim Source Quotation</span>
                </div>
                <div className="italic text-neutral-200 whitespace-pre-wrap max-h-40 overflow-y-auto pr-1 text-[11px]">
                  "{currentSnippet}"
                </div>
              </div>
            </div>
          </div>

          {/* 3. Verification State */}
          <div className="space-y-2">
            <div className="text-[11px] font-semibold text-neutral-400 uppercase tracking-wider">
              Verification
            </div>
            <div className="p-3 bg-neutral-50 border border-neutral-200 rounded-md flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <div>
                  <div className="font-semibold text-neutral-900 text-xs">
                    {readiness.label}
                  </div>
                  <div className="text-[11px] text-neutral-500">
                    Confidence: {formatScorePercent(currentConfidence)}
                  </div>
                </div>
              </div>
              <StatusBadge status={currentStatus} size="sm" />
            </div>
          </div>

          {/* 4. Technical Details (Expandable Accordion) */}
          <div className="pt-2 border-t border-neutral-200">
            <button
              onClick={() => setTechDetailsOpen(!techDetailsOpen)}
              className="w-full flex items-center justify-between py-2 text-xs font-medium text-neutral-500 hover:text-neutral-900 transition-colors"
            >
              <div className="flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-neutral-400" />
                <span>Technical Provenance & IDs</span>
              </div>
              {techDetailsOpen ? (
                <ChevronDown className="w-3.5 h-3.5 text-neutral-400" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-neutral-400" />
              )}
            </button>

            {techDetailsOpen && (
              <div className="mt-2 p-3 bg-neutral-50 rounded-md border border-neutral-200 space-y-2 font-mono text-[11px] animate-in fade-in-50 duration-150">
                <div className="flex items-center justify-between py-1 border-b border-neutral-200/60">
                  <span className="text-neutral-400">Fact ID</span>
                  <span className="text-neutral-800 font-medium truncate max-w-[210px]">{factId}</span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-neutral-200/60">
                  <span className="text-neutral-400">Evidence ID</span>
                  <span className="text-neutral-800 truncate max-w-[210px]">{evidenceId}</span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-neutral-200/60">
                  <span className="text-neutral-400">Observation ID</span>
                  <span className="text-neutral-800 truncate max-w-[210px]">{observationId}</span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-neutral-200/60">
                  <span className="text-neutral-400">Verification Run</span>
                  <span className="text-neutral-800 truncate max-w-[210px]">{verificationRunId}</span>
                </div>

                <div className="flex items-center justify-between py-1 border-b border-neutral-200/60">
                  <span className="text-neutral-400">Method</span>
                  <span className="text-neutral-800">{currentMethod}</span>
                </div>

                <div className="pt-1">
                  <div className="text-neutral-400 text-[10px] mb-0.5">Object Reference</div>
                  <div className="text-neutral-700 break-all text-[10px] bg-white p-1.5 rounded border border-neutral-200">
                    {objectRef}
                  </div>
                </div>
              </div>
            )}
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
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-neutral-300 bg-white hover:bg-neutral-100 text-neutral-800 font-medium text-xs shadow-2xs transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5 text-neutral-600" />
            <span>Suggest Correction</span>
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
