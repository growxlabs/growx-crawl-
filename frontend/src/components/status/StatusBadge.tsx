"use client";

import React from "react";
import {
  CheckCircle2,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Clock,
  Flame,
  XCircle,
  Search,
  RefreshCw,
  Sparkles,
} from "lucide-react";

export type StatusType =
  // Verification states
  | "Verified"
  | "Supported"
  | "Uncertain"
  | "Stale"
  | "Conflicting"
  | "Invalid"
  // Priority / Ranking states
  | "Priority"
  | "Strong"
  | "Possible"
  | "Research More"
  | "Reverify"
  | "Not Eligible"
  // General / Project / ICP states
  | "Active"
  | "Draft"
  | "Archived"
  | "running"
  | "completed"
  | "failed"
  | string;

interface StatusBadgeProps {
  status: StatusType;
  size?: "sm" | "md";
  showIcon?: boolean;
}

export function StatusBadge({
  status,
  size = "sm",
  showIcon = true,
}: StatusBadgeProps) {
  const norm = (status || "").toLowerCase().trim();

  let label = status;
  let bg = "bg-neutral-100";
  let text = "text-neutral-700";
  let border = "border-neutral-200";
  let IconComponent = HelpCircle;

  switch (norm) {
    case "verified":
    case "active":
    case "completed":
      bg = "bg-emerald-50";
      text = "text-emerald-700";
      border = "border-emerald-200";
      IconComponent = CheckCircle2;
      label = status === "completed" ? "Completed" : status;
      break;

    case "priority":
      bg = "bg-purple-50";
      text = "text-purple-700";
      border = "border-purple-200";
      IconComponent = Flame;
      label = "Priority";
      break;

    case "strong":
      bg = "bg-blue-50";
      text = "text-blue-700";
      border = "border-blue-200";
      IconComponent = ShieldCheck;
      label = "Strong";
      break;

    case "supported":
      bg = "bg-sky-50";
      text = "text-sky-700";
      border = "border-sky-200";
      IconComponent = ShieldCheck;
      label = "Supported";
      break;

    case "possible":
      bg = "bg-neutral-100";
      text = "text-neutral-800";
      border = "border-neutral-300";
      IconComponent = Sparkles;
      label = "Possible";
      break;

    case "research more":
      bg = "bg-amber-50";
      text = "text-amber-800";
      border = "border-amber-200";
      IconComponent = Search;
      label = "Research More";
      break;

    case "reverify":
    case "uncertain":
      bg = "bg-amber-50";
      text = "text-amber-800";
      border = "border-amber-200";
      IconComponent = RefreshCw;
      label = norm === "reverify" ? "Reverify" : "Uncertain";
      break;

    case "stale":
      bg = "bg-orange-50";
      text = "text-orange-700";
      border = "border-orange-200";
      IconComponent = Clock;
      label = "Stale";
      break;

    case "conflicting":
    case "invalid":
    case "failed":
    case "not eligible":
      bg = "bg-rose-50";
      text = "text-rose-700";
      border = "border-rose-200";
      IconComponent = XCircle;
      label =
        norm === "not eligible"
          ? "Not Eligible"
          : norm === "failed"
          ? "Failed"
          : status;
      break;

    case "draft":
      bg = "bg-neutral-100";
      text = "text-neutral-600";
      border = "border-neutral-200";
      IconComponent = Clock;
      label = "Draft";
      break;

    case "running":
      bg = "bg-indigo-50";
      text = "text-indigo-700";
      border = "border-indigo-200";
      IconComponent = RefreshCw;
      label = "Running";
      break;

    default:
      bg = "bg-neutral-100";
      text = "text-neutral-700";
      border = "border-neutral-200";
      IconComponent = HelpCircle;
  }

  const sizeClasses =
    size === "sm"
      ? "px-2 py-0.5 text-[11px] gap-1"
      : "px-2.5 py-1 text-xs gap-1.5";

  return (
    <span
      className={`inline-flex items-center font-medium rounded border ${bg} ${text} ${border} ${sizeClasses} select-none leading-none`}
    >
      {showIcon && (
        <IconComponent
          className={`w-3 h-3 flex-shrink-0 ${
            norm === "running" ? "animate-spin" : ""
          }`}
        />
      )}
      <span>{label}</span>
    </span>
  );
}
