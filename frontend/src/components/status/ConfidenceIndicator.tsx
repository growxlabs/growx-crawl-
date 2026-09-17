"use client";

import React from "react";

interface ConfidenceIndicatorProps {
  score?: number | null; // 0.0 to 1.0 or 0 to 100
  showValue?: boolean;
  label?: string;
  size?: "sm" | "md";
}

export function ConfidenceIndicator({
  score = 0,
  showValue = true,
  label,
  size = "sm",
}: ConfidenceIndicatorProps) {
  const safeScore = score ?? 0;
  // Normalize to 0 - 100
  const normalized = safeScore > 1 ? Math.min(100, Math.max(0, safeScore)) : Math.min(100, Math.max(0, safeScore * 100));
  const rounded = Math.round(normalized);

  let barColor = "bg-neutral-400";
  let textColor = "text-neutral-700";

  if (rounded >= 85) {
    barColor = "bg-emerald-500";
    textColor = "text-emerald-700 font-semibold";
  } else if (rounded >= 70) {
    barColor = "bg-blue-500";
    textColor = "text-blue-700 font-semibold";
  } else if (rounded >= 50) {
    barColor = "bg-amber-500";
    textColor = "text-amber-800 font-medium";
  } else {
    barColor = "bg-rose-500";
    textColor = "text-rose-700 font-medium";
  }

  const heightClass = size === "sm" ? "h-1.5 w-16" : "h-2 w-24";

  return (
    <div className="inline-flex items-center gap-2">
      {label && <span className="text-[11px] text-neutral-500">{label}</span>}
      <div
        className={`${heightClass} bg-neutral-100 rounded-full overflow-hidden border border-neutral-200/80`}
        title={`Confidence Score: ${rounded}%`}
      >
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${rounded}%` }}
        />
      </div>
      {showValue && (
        <span className={`text-xs font-mono tabular-nums ${textColor}`}>
          {rounded}%
        </span>
      )}
    </div>
  );
}
