"use client";

import React, { useEffect, useState } from "react";
import {
  ProjectPersonItem,
  getProjectPeople,
} from "@/lib/api/projects";
import { DataTable, ColumnDef } from "@/components/data-table/DataTable";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ConfidenceIndicator } from "@/components/status/ConfidenceIndicator";
import { ExternalLink, Users, Mail, Linkedin } from "lucide-react";
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
      header: "Contact Name",
      accessorKey: "full_name",
      sortable: true,
      cell: (row) => (
        <div>
          <div className="font-semibold text-neutral-900 text-xs">
            {row.full_name}
          </div>
          <div className="text-[11px] text-neutral-500">{row.job_title}</div>
        </div>
      ),
    },
    {
      header: "Target Account",
      accessorKey: "company_name",
      sortable: true,
      cell: (row) => (
        <span className="font-medium text-neutral-900 text-xs">
          {row.company_name}
        </span>
      ),
    },
    {
      header: "Seniority & Dept",
      cell: (row) => (
        <div className="flex items-center gap-1.5 font-mono text-[11px]">
          <span className="px-1.5 py-0.5 rounded bg-neutral-100 text-neutral-700 border border-neutral-200">
            {row.seniority}
          </span>
          <span className="text-neutral-500">{row.department}</span>
        </div>
      ),
    },
    {
      header: "Verification",
      accessorKey: "verification_status",
      sortable: true,
      cell: (row) => <StatusBadge status={row.verification_status} size="sm" />,
    },
    {
      header: "Confidence",
      accessorKey: "confidence_score",
      sortable: true,
      cell: (row) => (
        <ConfidenceIndicator score={row.confidence_score} size="sm" />
      ),
    },
    {
      header: "Email Status",
      accessorKey: "email_status",
      cell: (row) => (
        <span
          className={`text-[11px] font-mono px-1.5 py-0.5 rounded border ${
            row.email_status === "verified"
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-neutral-100 text-neutral-600 border-neutral-200"
          }`}
        >
          {row.email_status || "Deliverable"}
        </span>
      ),
    },
    {
      header: "Profile",
      cell: (row) => (
        <div className="flex items-center gap-2">
          {row.linkedin_url && (
            <a
              href={row.linkedin_url}
              target="_blank"
              rel="noreferrer"
              className="text-neutral-400 hover:text-blue-600"
              title="LinkedIn Profile"
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
            className="text-[11px] text-blue-600 hover:underline"
          >
            Evidence
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
        searchPlaceholder="Filter contacts by name, title, company, or department..."
        searchFilter={(p, q) =>
          p.full_name.toLowerCase().includes(q.toLowerCase()) ||
          p.job_title.toLowerCase().includes(q.toLowerCase()) ||
          p.company_name.toLowerCase().includes(q.toLowerCase()) ||
          p.department.toLowerCase().includes(q.toLowerCase())
        }
      />
    </div>
  );
}
