"use client";

import React, { useState } from "react";
import { useEvidence } from "./EvidenceContext";
import { submitFactCorrection } from "@/lib/api/verification";
import { X, CheckCircle2, AlertCircle, Edit3 } from "lucide-react";

export function FactCorrectionModal() {
  const { correctionModalOpen, correctionTarget, closeCorrectionModal } = useEvidence();

  const [correctedValue, setCorrectedValue] = useState("");
  const [reason, setReason] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!correctionModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!correctedValue.trim() || !reason.trim()) {
      setError("Please provide both the corrected value and reason.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await submitFactCorrection({
        fact_id: correctionTarget?.factId,
        company_id: correctionTarget?.companyId,
        corrected_value: correctedValue.trim(),
        reason: reason.trim(),
        source_url: sourceUrl.trim() || undefined,
      });

      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setCorrectedValue("");
        setReason("");
        setSourceUrl("");
        closeCorrectionModal();
      }, 1200);
    } catch (err: any) {
      setError(err?.message || "Failed to submit fact correction.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-neutral-900/40 backdrop-blur-[1px] transition-opacity"
        onClick={closeCorrectionModal}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl border border-neutral-200 z-10 overflow-hidden text-xs text-neutral-800">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-neutral-200 flex items-center justify-between bg-neutral-50">
          <div className="flex items-center gap-2">
            <Edit3 className="w-4 h-4 text-neutral-800" />
            <span className="font-semibold text-neutral-900 font-mono uppercase tracking-wider text-[11px]">
              Fact Correction Override
            </span>
          </div>
          <button
            onClick={closeCorrectionModal}
            className="p-1 rounded text-neutral-400 hover:text-neutral-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {correctionTarget?.claim && (
            <div>
              <label className="block text-[10px] uppercase font-mono text-neutral-400 mb-1">
                Current Extracted Value / Claim
              </label>
              <div className="p-2.5 bg-neutral-100 rounded text-neutral-700 text-xs border border-neutral-200">
                {correctionTarget.claim}
              </div>
            </div>
          )}

          <div>
            <label className="block text-[10px] uppercase font-mono text-neutral-500 mb-1">
              Corrected Value <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={correctedValue}
              onChange={(e) => setCorrectedValue(e.target.value)}
              placeholder="e.g. 250 employees or Enterprise Data Platform"
              className="w-full bg-white border border-neutral-300 rounded px-3 py-1.5 text-xs text-neutral-900 outline-none focus:border-neutral-900 transition-colors"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-mono text-neutral-500 mb-1">
              Correction Reason & Justification <span className="text-rose-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain why the current value is inaccurate or superseded..."
              className="w-full bg-white border border-neutral-300 rounded px-3 py-2 text-xs text-neutral-900 outline-none focus:border-neutral-900 transition-colors resize-none"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-mono text-neutral-500 mb-1">
              Verification Proof / Reference URL (Optional)
            </label>
            <input
              type="url"
              value={sourceUrl}
              onChange={(e) => setSourceUrl(e.target.value)}
              placeholder="https://company.com/press-release"
              className="w-full bg-white border border-neutral-300 rounded px-3 py-1.5 text-xs text-neutral-900 outline-none focus:border-neutral-900 transition-colors"
            />
          </div>

          {error && (
            <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-rose-700 text-[11px] flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-emerald-700 text-[11px] flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Fact correction submitted and verified.</span>
            </div>
          )}

          {/* Buttons */}
          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={closeCorrectionModal}
              disabled={submitting}
              className="px-3 py-1.5 rounded text-neutral-600 hover:text-neutral-900 font-medium text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 transition-colors disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Apply Fact Override"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
