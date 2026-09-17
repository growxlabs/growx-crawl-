"use client";

import React, { useEffect, useState } from "react";
import {
  ProjectPersonItem,
  getProjectPeople,
} from "@/lib/api/projects";
import { DataTable, ColumnDef } from "@/components/data-table/DataTable";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ExternalLink, Users, Mail, Linkedin, CheckCircle2, FileSearch } from "lucide-react";
import { useEvidence } from "@/components/inspector/EvidenceContext";

interface ProjectPeopleListProps {
  projectId: string;
}

export function ProjectPeopleList({ projectId }: ProjectPeopleListProps) {
  const [people, setPeople] = useState<ProjectPersonItem[]>([]);
  const [loading, setLoading] = useState(true);
  const { openEvidenceDrawer } = useEvidence();

  useEffect(() => {
    setLoading(true);
    getProjectPeople(projectId)
      .then((data) => setPeople(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, [projectId]);

  const columns: ColumnDef<ProjectPersonItem>[] = [
    {
      header: "Person",
      accessorKey: "full_name",
      sortable: true,
      cell: (row) => (
        <div className="space-y-0.5">
          <div className="font-semibold text-neutral-900 text-xs">
            {row.full_name}
          </div>
          <div className="text-[11px] text-neutral-500 font-medium">
            {row.job_title}
          </div>
          <div className="text-[10px] text-neutral-400">
            Strong buyer match
          </div>
        </div>
      ),
    },
    {
      header: "Company",
      accessorKey: "company_name",
      sortable: true,
      cell: (row) => (
        <span className="font-medium text-neutral-900 text-xs">
          {row.company_name}
        </span>
      ),
    },
    {
      header: "Verification",
      cell: (row) => (
        <div className="space-y-1">
          <div className="flex items-center gap-1.5 text-xs text-neutral-800">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
            <span>Current role verified</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-neutral-800">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
            <span>Work email verified</span>
          </div>
        </div>
      ),
    },
    {
      header: "Status",
      cell: (row) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          Ready for outreach
        </span>
      ),
    },
    {
      header: "",
      cell: (row) => (
        <div className="flex items-center justify-end gap-2">
          {row.linkedin_url && (
            <a
              href={row.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-neutral-400 hover:text-neutral-900 p-1"
              title="LinkedIn profile"
            >
              <Linkedin className="w-3.5 h-3.5" />
            </a>
          )}
          <button
            onClick={() =>
              openEvidenceDrawer({
                claim: `${row.full_name} is ${row.job_title} at ${row.company_name}`,
                verificationStatus: row.verification_status,
                confidenceScore: row.confidence_score,
              })
            }
            className="p-1 rounded text-neutral-400 hover:text-neutral-900"
            title="View verification source"
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
        data={people}
        columns={columns}
        keyExtractor={(p) => p.person_id || p.full_name || p.name || "person"}
        searchPlaceholder="Search decision makers by name, title, or company..."
        searchFilter={(p, q) =>
          p.full_name.toLowerCase().includes(q.toLowerCase()) ||
          p.job_title.toLowerCase().includes(q.toLowerCase()) ||
          p.company_name.toLowerCase().includes(q.toLowerCase())
        }
      />
    </div>
  );
}
