"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ProjectProspectItem,
  getProjectProspects,
} from "@/lib/api/projects";
import { triggerBulkAction } from "@/lib/api/prospects";
import { DataTable, ColumnDef } from "@/components/data-table/DataTable";
import { StatusBadge } from "@/components/status/StatusBadge";
import {
  RefreshCw,
  Search,
  Flame,
  CheckCircle2,
  FileSearch,
} from "lucide-react";
import { useEvidence } from "@/components/inspector/EvidenceContext";
import {
  formatPriority,
  formatReadiness,
  formatScorePercent,
} from "@/lib/product-language";

interface ProjectProspectsTableProps {
  projectId: string;
}

export function ProjectProspectsTable({ projectId }: ProjectProspectsTableProps) {
  const router = useRouter();
  const [prospects, setProspects] = useState<ProjectProspectItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkActionRunning, setBulkActionRunning] = useState(false);
  const { openEvidenceDrawer } = useEvidence();

  const loadProspects = () => {
    setLoading(true);
    getProjectProspects(projectId)
      .then((data) => setProspects(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadProspects();
  }, [projectId]);

  const handleBulkAction = async (action: "reverify" | "research" | "mark_priority") => {
    if (selectedIds.size === 0) return;
    setBulkActionRunning(true);
    try {
      await triggerBulkAction({
        action,
        prospect_ids: Array.from(selectedIds),
      });
      setSelectedIds(new Set());
      loadProspects();
    } catch (err) {
      console.error("Bulk action failed", err);
    } finally {
      setBulkActionRunning(false);
    }
  };

  const columns: ColumnDef<ProjectProspectItem>[] = [
    {
      header: "Company",
      accessorKey: "company_name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-neutral-900 text-xs">
            {row.company_name}
          </div>
          <div className="text-[11px] text-neutral-400 mt-0.5">
            {row.domain}
          </div>
        </div>
      ),
    },
    {
      header: "Priority",
      accessorKey: "rank_tier",
      sortable: true,
      cell: (row) => {
        const p = formatPriority(row.rank_tier || row.priority);
        return <StatusBadge status={p.label} size="sm" />;
      },
    },
    {
      header: "Why now",
      cell: (row) => {
        const signalText =
          row.top_signal ||
          row.top_signals?.[0] ||
          row.reasons?.[0] ||
          "Target market alignment";
        return (
          <span className="text-xs text-neutral-700 max-w-xs truncate block" title={signalText}>
            {signalText}
          </span>
        );
      },
    },
    {
      header: "Best person",
      cell: (row) => {
        if (row.best_person && row.best_person.name) {
          return (
            <div>
              <div className="font-medium text-xs text-neutral-900">
                {row.best_person.name}
              </div>
              <div className="text-[11px] text-neutral-500">
                {row.best_person.title}
              </div>
            </div>
          );
        }
        return (
          <span className="text-xs text-neutral-600">
            {row.buyer_roles_count ? `${row.buyer_roles_count} personas matched` : "Head of Operations"}
          </span>
        );
      },
    },
    {
      header: "Fit",
      accessorKey: "final_score",
      sortable: true,
      cell: (row) => (
        <span className="text-xs font-semibold text-neutral-900">
          {formatScorePercent(row.final_score)}
        </span>
      ),
    },
    {
      header: "Readiness",
      accessorKey: "verification_status",
      sortable: true,
      cell: (row) => {
        const r = formatReadiness(row.verification_status, row.requires_reverification);
        return <StatusBadge status={r.label} size="sm" />;
      },
    },
    {
      header: "Status",
      accessorKey: "status",
      sortable: true,
      cell: (row) => (
        <span className="text-xs text-neutral-600 capitalize">
          {row.status || "Ready"}
        </span>
      ),
    },
    {
      header: "",
      cell: (row) => (
        <div
          className="flex items-center justify-end"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() =>
              openEvidenceDrawer({
                claim: `${row.company_name} Priority Qualification (${formatScorePercent(
                  row.final_score
                )})`,
                sourceUrl: `https://${row.domain}`,
                verificationStatus: row.verification_status,
                confidenceScore: row.final_score,
              })
            }
            className="p-1 rounded text-neutral-400 hover:text-neutral-800"
            title="View verification sources"
          >
            <FileSearch className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <DataTable
        data={prospects}
        columns={columns}
        keyExtractor={(r) => r.prospect_id}
        onRowClick={(r) => router.push(`/prospects/${r.prospect_id}`)}
        selectable
        selectedKeys={selectedIds}
        onSelectionChange={setSelectedIds}
        searchPlaceholder="Filter prospects by company, person, or signal..."
        searchFilter={(r, q) =>
          r.company_name.toLowerCase().includes(q.toLowerCase()) ||
          r.domain.toLowerCase().includes(q.toLowerCase()) ||
          r.industry.toLowerCase().includes(q.toLowerCase()) ||
          (r.top_signals || []).some((s) => s.toLowerCase().includes(q.toLowerCase()))
        }
        actions={
          selectedIds.size > 0 && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => handleBulkAction("reverify")}
                disabled={bulkActionRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-neutral-100 hover:bg-neutral-200 border border-neutral-300 text-neutral-800 text-xs font-medium"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh data</span>
              </button>
              <button
                onClick={() => handleBulkAction("research")}
                disabled={bulkActionRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-neutral-100 hover:bg-neutral-200 border border-neutral-300 text-neutral-800 text-xs font-medium"
              >
                <Search className="w-3 h-3" />
                <span>Research deeper</span>
              </button>
              <button
                onClick={() => handleBulkAction("mark_priority")}
                disabled={bulkActionRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-neutral-900 text-white text-xs font-medium hover:bg-neutral-800"
              >
                <Flame className="w-3 h-3" />
                <span>Mark priority</span>
              </button>
            </div>
          )
        }
      />
    </div>
  );
}
