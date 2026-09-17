"use client";

import React, { useEffect, useState } from "react";
import { getSellerHistory, CompanyEvent } from "@/lib/api/company";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  Clock,
  FileSearch,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { formatPredicate } from "@/lib/product-language";

interface GroupedChanges {
  period: string;
  items: {
    id: string;
    title: string;
    description: string;
    actionLabel: string;
    evidenceId?: string;
    claim: string;
  }[];
}

export function CompanyHistory() {
  const [events, setEvents] = useState<CompanyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    getSellerHistory()
      .then((data) => setEvents(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const defaultGroups: GroupedChanges[] = [
    {
      period: "Today",
      items: [
        {
          id: "1",
          title: "Headquarters confirmed",
          description: "San Francisco, CA",
          actionLabel: "View source",
          evidenceId: "evi_hq_sf",
          claim: "Headquarters confirmed: San Francisco, CA",
        },
      ],
    },
    {
      period: "Yesterday",
      items: [
        {
          id: "2",
          title: "Company size updated",
          description: "10–50 → 50–200 team members",
          actionLabel: "View why",
          evidenceId: "evi_emp_growth",
          claim: "Company size updated: 10–50 → 50–200 team members based on career and team page updates.",
        },
      ],
    },
    {
      period: "14 Sep",
      items: [
        {
          id: "3",
          title: "Clay added as an adjacent competitor",
          description: "74% overlap with enrichment workflows",
          actionLabel: "View comparison",
          evidenceId: "evi_comp_clay",
          claim: "Clay mapped as adjacent competitor with 74% market and feature overlap.",
        },
      ],
    },
    {
      period: "12 Sep",
      items: [
        {
          id: "4",
          title: "Target customer profile updated",
          description: "Version 1.1 is now active",
          actionLabel: "View changes",
          evidenceId: "evi_icp_v11",
          claim: "Target customer profile updated: Version 1.1 activated with calibrated revenue and employee filters.",
        },
      ],
    },
  ];

  return (
    <div className="max-w-3xl space-y-8 py-2">
      {/* Page Header */}
      <div className="border-b border-neutral-200 pb-5">
        <h1 className="text-xl font-bold text-neutral-900 tracking-tight">
          Changes
        </h1>
        <p className="text-xs text-neutral-500 mt-1">
          Chronological record of verified company information and market updates.
        </p>
      </div>

      {/* Grouped Change Stream */}
      <div className="space-y-8">
        {defaultGroups.map((group) => (
          <div key={group.period} className="space-y-3">
            <div className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">
              {group.period}
            </div>

            <div className="space-y-3 border-l-2 border-neutral-200 pl-4 ml-1">
              {group.items.map((item) => (
                <div
                  key={item.id}
                  className="p-4 bg-white border border-neutral-200 rounded-md hover:border-neutral-300 transition-colors flex items-start justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="font-semibold text-xs text-neutral-900">
                      {item.title}
                    </div>
                    <div className="text-xs text-neutral-600 font-medium">
                      {item.description}
                    </div>
                  </div>

                  <button
                    onClick={() =>
                      openEvidenceDrawer({
                        claim: item.claim,
                        evidenceId: item.evidenceId,
                        verificationStatus: "Verified",
                      })
                    }
                    className="text-xs text-neutral-600 hover:text-neutral-900 underline flex items-center gap-1 flex-shrink-0 pt-0.5 font-medium"
                  >
                    <span>{item.actionLabel}</span>
                  </button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
