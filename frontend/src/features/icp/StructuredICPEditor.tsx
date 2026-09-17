"use client";

import React, { useState } from "react";
import {
  ICPVersion,
  ICPCriterion,
  ICPPersona,
  ICPExclusion,
  createICPDraft,
} from "@/lib/api/icp";
import {
  Plus,
  Trash2,
  Save,
  X,
  Target,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

interface StructuredICPEditorProps {
  icpId: string;
  initialData: ICPVersion;
  onSaved: () => void;
  onCancel: () => void;
}

export function StructuredICPEditor({
  icpId,
  initialData,
  onSaved,
  onCancel,
}: StructuredICPEditorProps) {
  const [name, setName] = useState(initialData.name);
  const [reasoning, setReasoning] = useState(initialData.reasoning);
  const [changeSummary, setChangeSummary] = useState(
    "Updated criteria weights and added refined personas."
  );
  const [criteria, setCriteria] = useState<ICPCriterion[]>(initialData.criteria);
  const [personas, setPersonas] = useState<ICPPersona[]>(
    initialData.buyer_personas
  );
  const [exclusions, setExclusions] = useState<ICPExclusion[]>(
    initialData.exclusions
  );

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddCriterion = () => {
    const newCrit: ICPCriterion = {
      criterion_id: `crit_${Date.now()}`,
      category: "firmographic",
      dimension: "new_attribute",
      operator: "equals",
      target_value: "Value",
      weight: 0.5,
      is_dealbreaker: false,
      rationale: "Added in version draft.",
    };
    setCriteria([...criteria, newCrit]);
  };

  const handleRemoveCriterion = (id: string) => {
    setCriteria(criteria.filter((c) => c.criterion_id !== id));
  };

  const handleUpdateCriterion = (
    id: string,
    updates: Partial<ICPCriterion>
  ) => {
    setCriteria(
      criteria.map((c) => (c.criterion_id === id ? { ...c, ...updates } : c))
    );
  };

  const handleAddPersona = () => {
    const newPersona: ICPPersona = {
      persona_id: `per_${Date.now()}`,
      title: "New Buyer Role",
      seniority: "Director",
      departments: ["Sales"],
      priority: "Tier 1",
    };
    setPersonas([...personas, newPersona]);
  };

  const handleRemovePersona = (id: string) => {
    setPersonas(personas.filter((p) => p.persona_id !== id));
  };

  const handleAddExclusion = () => {
    const newEx: ICPExclusion = {
      exclusion_id: `ex_${Date.now()}`,
      dimension: "industry",
      rule: "Exclude non-target category",
      rationale: "Disqualified profile.",
    };
    setExclusions([...exclusions, newEx]);
  };

  const handleRemoveExclusion = (id: string) => {
    setExclusions(exclusions.filter((e) => e.exclusion_id !== id));
  };

  const handleSaveDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await createICPDraft(icpId, {
        name,
        reasoning,
        change_summary: changeSummary,
        criteria,
        buyer_personas: personas,
        exclusions,
      });
      onSaved();
    } catch (err: any) {
      setError(err?.message || "Failed to save draft version.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSaveDraft}
      className="bg-white border border-neutral-300 rounded p-6 shadow-sm space-y-6 text-xs text-neutral-800"
    >
      {/* Editor Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 pb-4">
        <div>
          <h2 className="text-sm font-bold text-neutral-900 font-mono uppercase tracking-wide">
            Drafting ICP Version {(initialData.version_number || 1) + 1}.0
          </h2>
          <p className="text-neutral-500 text-xs mt-0.5">
            Modify qualification criteria, dealbreaker constraints, and buyer
            personas before publishing.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={saving}
            className="px-3 py-1.5 rounded border border-neutral-200 text-neutral-700 hover:bg-neutral-100 font-medium text-xs"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded bg-neutral-900 text-white font-medium text-xs hover:bg-neutral-800 transition-colors shadow-2xs disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            <span>{saving ? "Saving Draft..." : "Save as Draft Version"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metadata Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-[10px] font-mono uppercase text-neutral-500 mb-1">
            ICP Profile Name
          </label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full bg-neutral-50 border border-neutral-300 rounded px-3 py-1.5 text-xs text-neutral-900 outline-none focus:border-neutral-900"
          />
        </div>
        <div>
          <label className="block text-[10px] font-mono uppercase text-neutral-500 mb-1">
            Change Summary Log
          </label>
          <input
            type="text"
            required
            value={changeSummary}
            onChange={(e) => setChangeSummary(e.target.value)}
            className="w-full bg-neutral-50 border border-neutral-300 rounded px-3 py-1.5 text-xs text-neutral-900 outline-none focus:border-neutral-900"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-[10px] font-mono uppercase text-neutral-500 mb-1">
            Strategic Reasoning / Thesis
          </label>
          <textarea
            rows={2}
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            className="w-full bg-neutral-50 border border-neutral-300 rounded px-3 py-2 text-xs text-neutral-900 outline-none focus:border-neutral-900 resize-none"
          />
        </div>
      </div>

      {/* Criteria Table Editor */}
      <div className="space-y-3 pt-2 border-t border-neutral-200">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-xs uppercase font-mono text-neutral-900">
            Qualification Criteria ({criteria.length})
          </h3>
          <button
            type="button"
            onClick={handleAddCriterion}
            className="inline-flex items-center gap-1 text-xs text-neutral-900 font-semibold bg-neutral-100 hover:bg-neutral-200 px-2.5 py-1 rounded border border-neutral-300"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Criterion</span>
          </button>
        </div>

        <div className="space-y-2">
          {criteria.map((c) => (
            <div
              key={c.criterion_id}
              className="p-3 bg-neutral-50 rounded border border-neutral-200 grid grid-cols-1 sm:grid-cols-12 gap-3 items-center"
            >
              <div className="sm:col-span-2">
                <label className="block text-[9px] uppercase font-mono text-neutral-400">
                  Category
                </label>
                <select
                  value={c.category}
                  onChange={(e) =>
                    handleUpdateCriterion(c.criterion_id, {
                      category: e.target.value as any,
                    })
                  }
                  className="w-full bg-white border border-neutral-300 rounded px-2 py-1 text-xs"
                >
                  <option value="firmographic">Firmographic</option>
                  <option value="technographic">Technographic</option>
                  <option value="geographic">Geographic</option>
                  <option value="timing_signal">Timing Signal</option>
                  <option value="intent">Intent</option>
                </select>
              </div>

              <div className="sm:col-span-3">
                <label className="block text-[9px] uppercase font-mono text-neutral-400">
                  Dimension
                </label>
                <input
                  type="text"
                  value={c.dimension}
                  onChange={(e) =>
                    handleUpdateCriterion(c.criterion_id, {
                      dimension: e.target.value,
                    })
                  }
                  className="w-full bg-white border border-neutral-300 rounded px-2 py-1 text-xs"
                />
              </div>

              <div className="sm:col-span-3">
                <label className="block text-[9px] uppercase font-mono text-neutral-400">
                  Target Value
                </label>
                <input
                  type="text"
                  value={c.target_value}
                  onChange={(e) =>
                    handleUpdateCriterion(c.criterion_id, {
                      target_value: e.target.value,
                    })
                  }
                  className="w-full bg-white border border-neutral-300 rounded px-2 py-1 text-xs"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-[9px] uppercase font-mono text-neutral-400">
                  Weight: {Math.round(c.weight * 100)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  value={c.weight}
                  onChange={(e) =>
                    handleUpdateCriterion(c.criterion_id, {
                      weight: parseFloat(e.target.value),
                    })
                  }
                  className="w-full cursor-pointer accent-neutral-900"
                />
              </div>

              <div className="sm:col-span-1 flex items-center pt-3 justify-center">
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={c.is_dealbreaker}
                    onChange={(e) =>
                      handleUpdateCriterion(c.criterion_id, {
                        is_dealbreaker: e.target.checked,
                      })
                    }
                    className="rounded border-neutral-300 text-rose-600 focus:ring-0"
                  />
                  <span className="text-[10px] text-rose-700 font-bold">Deal?</span>
                </label>
              </div>

              <div className="sm:col-span-1 flex items-center pt-3 justify-end">
                <button
                  type="button"
                  onClick={() => handleRemoveCriterion(c.criterion_id)}
                  className="text-neutral-400 hover:text-rose-600 p-1"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Buyer Personas Editor */}
      <div className="space-y-3 pt-2 border-t border-neutral-200">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-xs uppercase font-mono text-neutral-900">
            Buyer Personas ({personas.length})
          </h3>
          <button
            type="button"
            onClick={handleAddPersona}
            className="inline-flex items-center gap-1 text-xs text-neutral-900 font-semibold bg-neutral-100 hover:bg-neutral-200 px-2.5 py-1 rounded border border-neutral-300"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Persona</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {personas.map((p) => (
            <div
              key={p.persona_id}
              className="p-3 bg-neutral-50 rounded border border-neutral-200 flex items-center justify-between gap-2"
            >
              <div className="flex-1 space-y-1">
                <input
                  type="text"
                  value={p.title}
                  onChange={(e) =>
                    setPersonas(
                      personas.map((item) =>
                        item.persona_id === p.persona_id
                          ? { ...item, title: e.target.value }
                          : item
                      )
                    )
                  }
                  className="w-full font-semibold text-xs bg-white border border-neutral-300 rounded px-2 py-0.5"
                />
                <input
                  type="text"
                  placeholder="Departments (comma-separated)"
                  value={p.departments.join(", ")}
                  onChange={(e) =>
                    setPersonas(
                      personas.map((item) =>
                        item.persona_id === p.persona_id
                          ? {
                              ...item,
                              departments: e.target.value
                                .split(",")
                                .map((s) => s.trim()),
                            }
                          : item
                      )
                    )
                  }
                  className="w-full text-[11px] text-neutral-500 bg-white border border-neutral-300 rounded px-2 py-0.5"
                />
              </div>

              <button
                type="button"
                onClick={() => handleRemovePersona(p.persona_id)}
                className="text-neutral-400 hover:text-rose-600 p-1"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </form>
  );
}
