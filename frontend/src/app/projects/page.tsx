"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { listProjects, Project } from "@/lib/api/projects";
import { StatusBadge } from "@/components/status/StatusBadge";
import { ProjectCreateModal } from "@/features/projects/ProjectCreateModal";
import {
  FolderGit2,
  Plus,
  ArrowRight,
  Flame,
  Users,
  Target,
  ShieldCheck,
} from "lucide-react";

export default function ProjectsDirectoryPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchProjects = () => {
    setLoading(true);
    listProjects()
      .then((data) => setProjects(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const defaultProjects: Project[] = [
    {
      id: "prj_us_saas_expansion",
      name: "US Mid-Market SaaS Expansion",
      description:
        "Targeting high-growth US B2B software companies between 50-1000 employees with active outbound SDR hiring and Salesforce/HubSpot CRMs.",
      seller_company_id: "cmp_seller_growxlabs",
      icp_id: "icp_us_midmarket_saas",
      status: "active",
      total_prospects: 48,
      verified_prospects: 42,
      high_priority_prospects: 14,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "prj_enterprise_fintech",
      name: "Enterprise FinTech & Infrastructure",
      description:
        "Accounts building financial APIs, compliance workflows, and banking automation requiring real-time identity & canonical verification.",
      seller_company_id: "cmp_seller_growxlabs",
      icp_id: "icp_enterprise_fintech",
      status: "draft",
      total_prospects: 24,
      verified_prospects: 19,
      high_priority_prospects: 7,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const list = projects.length > 0 ? projects : defaultProjects;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-neutral-200 rounded p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <FolderGit2 className="w-4 h-4 text-neutral-800" />
              <h1 className="text-base font-bold text-neutral-900">
                AutoGTM Projects
              </h1>
            </div>
            <p className="text-xs text-neutral-500 mt-1 max-w-xl">
              Coordinated outbound campaigns linking seller intelligence, custom ICP definitions,
              and algorithmically prioritized prospect accounts.
            </p>
          </div>

          <button
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 shadow-2xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create New Project</span>
          </button>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {list.map((proj) => (
          <div
            key={proj.id}
            onClick={() => router.push(`/projects/${proj.id}/overview`)}
            className="bg-white border border-neutral-200 hover:border-neutral-400 rounded p-6 shadow-2xs hover:shadow-xs transition-all cursor-pointer flex flex-col justify-between space-y-4"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h2 className="text-sm font-bold text-neutral-900">
                    {proj.name}
                  </h2>
                  <div className="text-[11px] font-mono text-neutral-400 mt-0.5">
                    {proj.id}
                  </div>
                </div>
                <StatusBadge status={proj.status} size="sm" />
              </div>

              <p className="text-xs text-neutral-600 mt-3 leading-relaxed">
                {proj.description}
              </p>
            </div>

            {/* Metrics Footer */}
            <div className="pt-4 border-t border-neutral-100 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-3">
                <span className="text-neutral-700 font-semibold">
                  {proj.total_prospects} Prospects
                </span>
                <span>•</span>
                <span className="text-purple-700 font-semibold flex items-center gap-1">
                  <Flame className="w-3 h-3 text-purple-600" />
                  {proj.high_priority_prospects} Priority
                </span>
              </div>

              <span className="text-neutral-900 flex items-center gap-1 font-sans text-xs font-medium group-hover:underline">
                <span>Open Project</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      <ProjectCreateModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={(newProj) => {
          fetchProjects();
          router.push(`/projects/${newProj.id}/overview`);
        }}
      />
    </div>
  );
}
