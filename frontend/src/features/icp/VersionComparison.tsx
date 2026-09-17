"use client";

import React, { useState } from "react";
import { ICPVersion, activateICPVersion } from "@/lib/api/icp";
import { GitCompare, CheckCircle2, ArrowRight, Zap, Clock } from "lucide-react";
import { StatusBadge } from "@/components/status/StatusBadge";

interface VersionComparisonProps {
  icpId: string;
  versions: ICPVersion[];
  onActivated?: () => void;
}

export function VersionComparison({
  icpId,
  versions,
  onActivated,
}: VersionComparisonProps) {
  const [leftIndex, setLeftIndex] = useState(0);
  const [rightIndex, setRightIndex] = useState(
    versions.length > 1 ? 1 : 0
  );
  const [activating, setActivating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const left = versions[leftIndex] || versions[0];
  const right = versions[rightIndex] || versions[0];

  const handleActivate = async (versionNumber: number) => {
    setActivating(true);
    setMessage(null);
    try {
      await activateICPVersion(icpId, versionNumber);
      setMessage(`Version v${versionNumber}.0 is now ACTIVE.`);
      if (onActivated) onActivated();
    } catch (err: any) {
      setMessage(err?.message || "Failed to activate version.");
    } finally {
      setActivating(false);
    }
  };

  return (
    <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs space-y-6 text-xs text-neutral-800">
      {/* Header & Selectors */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 pb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-neutral-800" />
          <h2 className="text-sm font-bold text-neutral-900 font-mono uppercase tracking-wide">
            ICP Version Differential Analyzer
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-neutral-400">Base:</span>
            <select
              value={leftIndex}
              onChange={(e) => setLeftIndex(Number(e.target.value))}
              className="bg-neutral-100 border border-neutral-300 rounded px-2 py-1 text-xs font-semibold"
            >
              {versions.map((v, idx) => (
                <option key={v.version_id || idx} value={idx}>
                  v{v.version_number}.0 ({v.status})
                </option>
              ))}
            </select>
          </div>

          <ArrowRight className="w-3.5 h-3.5 text-neutral-400" />

          <div className="flex items-center gap-1.5">
            <span className="text-[11px] text-neutral-400">Compare with:</span>
            <select
              value={rightIndex}
              onChange={(e) => setRightIndex(Number(e.target.value))}
              className="bg-neutral-100 border border-neutral-300 rounded px-2 py-1 text-xs font-semibold"
            >
              {versions.map((v, idx) => (
                <option key={v.version_id || idx} value={idx}>
                  v{v.version_number}.0 ({v.status})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Side-by-Side Comparison Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Version Column */}
        <div className="p-4 rounded border border-neutral-200 bg-neutral-50/40 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-neutral-900 font-mono text-sm">
                v{left.version_number}.0
              </span>
              <StatusBadge status={left.status} size="sm" />
            </div>
            {left.status !== "active" && (
              <button
                onClick={() => handleActivate(left.version_number)}
                disabled={activating}
                className="px-2.5 py-1 rounded bg-neutral-900 text-white font-medium text-[11px] hover:bg-neutral-800"
              >
                Set as Active
              </button>
            )}
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400">
              Reasoning
            </div>
            <p className="text-xs text-neutral-600 mt-0.5">{left.reasoning}</p>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400 mb-2">
              Criteria ({left.criteria.length})
            </div>
            <div className="space-y-1.5">
              {left.criteria.map((c) => (
                <div
                  key={c.criterion_id}
                  className="p-2 bg-white rounded border border-neutral-200 text-[11px] flex items-center justify-between"
                >
                  <span className="font-semibold text-neutral-800">
                    {c.dimension}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-neutral-500">
                      {c.target_value}
                    </span>
                    <span className="font-mono font-bold text-neutral-900">
                      {Math.round(c.weight * 100)}%
                    </span>
                    {c.is_dealbreaker && (
                      <span className="text-[9px] text-rose-600 font-bold uppercase">
                        Mandatory
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Version Column */}
        <div className="p-4 rounded border border-neutral-200 bg-neutral-50/40 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-bold text-neutral-900 font-mono text-sm">
                v{right.version_number}.0
              </span>
              <StatusBadge status={right.status} size="sm" />
            </div>
            {right.status !== "active" && (
              <button
                onClick={() => handleActivate(right.version_number)}
                disabled={activating}
                className="px-2.5 py-1 rounded bg-neutral-900 text-white font-medium text-[11px] hover:bg-neutral-800"
              >
                Set as Active
              </button>
            )}
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400">
              Reasoning
            </div>
            <p className="text-xs text-neutral-600 mt-0.5">{right.reasoning}</p>
          </div>

          <div>
            <div className="text-[10px] font-mono uppercase text-neutral-400 mb-2">
              Criteria ({right.criteria.length})
            </div>
            <div className="space-y-1.5">
              {right.criteria.map((c) => (
                <div
                  key={c.criterion_id}
                  className="p-2 bg-white rounded border border-neutral-200 text-[11px] flex items-center justify-between"
                >
                  <span className="font-semibold text-neutral-800">
                    {c.dimension}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-neutral-500">
                      {c.target_value}
                    </span>
                    <span className="font-mono font-bold text-neutral-900">
                      {Math.round(c.weight * 100)}%
                    </span>
                    {c.is_dealbreaker && (
                      <span className="text-[9px] text-rose-600 font-bold uppercase">
                        Mandatory
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
