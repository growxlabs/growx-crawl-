"use client";

import React, { useState } from "react";
import { createProject, Project } from "@/lib/api/projects";
import { X, FolderPlus, AlertCircle, CheckCircle2 } from "lucide-react";

interface ProjectCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (project: Project) => void;
}

export function ProjectCreateModal({
  isOpen,
  onClose,
  onCreated,
}: ProjectCreateModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [icpId, setIcpId] = useState("icp_us_midmarket_saas");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please specify a project name.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const proj = await createProject({
        name: name.trim(),
        description: description.trim(),
        icp_id: icpId,
        seller_company_id: "cmp_seller_growxlabs",
      });

      onCreated(proj);
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to create project.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-neutral-900/40 backdrop-blur-[1px] transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-md bg-white rounded-lg shadow-xl border border-neutral-200 z-10 overflow-hidden text-xs text-neutral-800">
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-neutral-200 flex items-center justify-between bg-neutral-50">
          <div className="flex items-center gap-2">
            <FolderPlus className="w-4 h-4 text-neutral-800" />
            <span className="font-semibold text-neutral-900 font-mono uppercase tracking-wider text-[11px]">
              Initialize AutoGTM Project
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-neutral-400 hover:text-neutral-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-[10px] uppercase font-mono text-neutral-500 mb-1">
              Project Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. EMEA Enterprise FinTech Outbound"
              className="w-full bg-white border border-neutral-300 rounded px-3 py-1.5 text-xs text-neutral-900 outline-none focus:border-neutral-900 transition-colors"
            />
          </div>

          <div>
            <label className="block text-[10px] uppercase font-mono text-neutral-500 mb-1">
              Attached ICP Profile
            </label>
            <select
              value={icpId}
              onChange={(e) => setIcpId(e.target.value)}
              className="w-full bg-white border border-neutral-300 rounded px-2.5 py-1.5 text-xs text-neutral-900 outline-none focus:border-neutral-900 transition-colors"
            >
              <option value="icp_us_midmarket_saas">
                US Mid-Market B2B SaaS ICP (v1.0)
              </option>
              <option value="icp_enterprise_fintech">
                Enterprise FinTech & Payments ICP (v1.0)
              </option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] uppercase font-mono text-neutral-500 mb-1">
              Project Scope & Outbound Strategy
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detail target companies, buyer intent criteria, and outreach purpose..."
              className="w-full bg-white border border-neutral-300 rounded px-3 py-2 text-xs text-neutral-900 outline-none focus:border-neutral-900 transition-colors resize-none"
            />
          </div>

          {error && (
            <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-rose-700 text-[11px] flex items-center gap-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Footer Buttons */}
          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-3 py-1.5 rounded text-neutral-600 hover:text-neutral-900 font-medium text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-1.5 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 transition-colors disabled:opacity-50"
            >
              {saving ? "Creating..." : "Initialize Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
