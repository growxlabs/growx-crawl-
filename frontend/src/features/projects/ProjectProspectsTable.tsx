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
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import {
  Building2,
  ExternalLink,
  RefreshCw,
  Search,
  Flame,
  CheckCircle2,
  AlertTriangle,
  FileSearch,
} from "lucide-react";
import { useEvidence } from "@/components/inspector/EvidenceContext";

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
      header: "Target Account",
      accessorKey: "company_name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-neutral-900 text-xs flex items-center gap-1.5">
            <span>{row.company_name}</span>
            {row.rank_tier === "Priority" && (
              <Flame className="w-3.5 h-3.5 text-purple-600 flex-shrink-0" />
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5 text-[11px] font-mono text-neutral-400">
            <span>{row.domain}</span>
            <span>•</span>
            <span>{row.industry}</span>
          </div>
        </div>
      ),
    },
    {
      header: "Rank Tier",
      accessorKey: "rank_tier",
      sortable: true,
      cell: (row) => <StatusBadge status={row.rank_tier} size="sm" />,
    },
    {
      header: "ICP Fit Score",
      accessorKey: "final_score",
      sortable: true,
      cell: (row) => (
        <ConfidenceIndicator score={row.final_score} size="sm" />
      ),
    },
    {
      header: "Verification",
      accessorKey: "verification_status",
      sortable: true,
      cell: (row) => (
        <div className="flex items-center gap-1.5">
          <StatusBadge status={row.verification_status} size="sm" />
          {row.requires_reverification && (
            <span className="text-[10px] text-amber-700 bg-amber-50 px-1 py-0.5 rounded border border-amber-200">
              Needs Sync
            </span>
          )}
        </div>
      ),
    },
    {
      header: "Top Signals",
      cell: (row) => (
        <div className="flex flex-wrap gap-1 max-w-xs">
          {row.top_signals && row.top_signals.length > 0 ? (
            row.top_signals.slice(0, 2).map((sig, sIdx) => (
              <span
                key={sIdx}
                className="text-[10px] bg-neutral-100 text-neutral-700 px-1.5 py-0.5 rounded border border-neutral-200 font-mono truncate max-w-[120px]"
              >
                {sig}
              </span>
            ))
          ) : (
            <span className="text-neutral-400 text-[11px] font-mono">-</span>
          )}
        </div>
      ),
    },
    {
      header: "Contacts",
      accessorKey: "buyer_roles_count",
      sortable: true,
      cell: (row) => (
        <span className="font-mono text-xs font-semibold text-neutral-800">
          {row.buyer_roles_count} personas
        </span>
      ),
    },
    {
      header: "Actions",
      cell: (row) => (
        <div
          className="flex items-center gap-2"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={() =>
              openEvidenceDrawer({
                claim: `${row.company_name} ICP Fit Score: ${Math.round(
                  row.final_score * 100
                )}%`,
                sourceUrl: `https://${row.domain}`,
                verificationStatus: row.verification_status,
                confidenceScore: row.final_score,
              })
            }
            className="p-1 rounded text-neutral-400 hover:text-neutral-800"
            title="Inspect Verification Evidence"
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
        searchPlaceholder="Filter prospects by name, domain, signal, or industry..."
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
                <span>Reverify</span>
              </button>
              <button
                onClick={() => handleBulkAction("research")}
                disabled={bulkActionRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-neutral-100 hover:bg-neutral-200 border border-neutral-300 text-neutral-800 text-xs font-medium"
              >
                <Search className="w-3 h-3" />
                <span>Deep Research</span>
              </button>
              <button
                onClick={() => handleBulkAction("mark_priority")}
                disabled={bulkActionRunning}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-neutral-900 text-white text-xs font-medium hover:bg-neutral-800"
              >
                <Flame className="w-3 h-3" />
                <span>Mark Priority</span>
              </button>
            </div>
          )
        }
      />
    </div>
  );
}
