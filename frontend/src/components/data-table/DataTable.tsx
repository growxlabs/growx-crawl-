"use client";

import React, { useState, useMemo } from "react";
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Search,
  Filter,
} from "lucide-react";

export interface ColumnDef<T> {
  header: string;
  accessorKey?: keyof T | string;
  cell?: (row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
}

interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T>[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  selectable?: boolean;
  selectedKeys?: Set<string>;
  onSelectionChange?: (keys: Set<string>) => void;
  searchPlaceholder?: string;
  searchFilter?: (row: T, query: string) => boolean;
  emptyMessage?: string;
  actions?: React.ReactNode;
}

export function DataTable<T>({
  data,
  columns,
  keyExtractor,
  onRowClick,
  selectable = false,
  selectedKeys = new Set(),
  onSelectionChange,
  searchPlaceholder = "Filter records...",
  searchFilter,
  emptyMessage = "No records found.",
  actions,
}: DataTableProps<T>) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  // Filtered rows
  const filteredData = useMemo(() => {
    if (!query.trim()) return data;
    if (searchFilter) {
      return data.filter((row) => searchFilter(row, query));
    }
    // Default search against stringified values
    return data.filter((row) =>
      JSON.stringify(row).toLowerCase().includes(query.toLowerCase())
    );
  }, [data, query, searchFilter]);

  // Sorted rows
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = (a as any)[sortKey];
      const bVal = (b as any)[sortKey];
      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      const cmp = aVal > bVal ? 1 : -1;
      return sortAsc ? cmp : -cmp;
    });
  }, [filteredData, sortKey, sortAsc]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!onSelectionChange) return;
    if (e.target.checked) {
      const all = new Set<string>(filteredData.map(keyExtractor));
      onSelectionChange(all);
    } else {
      onSelectionChange(new Set());
    }
  };

  const handleSelectRow = (key: string) => {
    if (!onSelectionChange) return;
    const next = new Set(selectedKeys);
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
    }
    onSelectionChange(next);
  };

  const handleSort = (key?: string) => {
    if (!key) return;
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  const allSelected =
    filteredData.length > 0 &&
    filteredData.every((row) => selectedKeys.has(keyExtractor(row)));

  return (
    <div className="w-full flex flex-col bg-white border border-neutral-200 rounded">
      {/* Table Toolbar */}
      <div className="p-3 border-b border-neutral-200 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2 flex-1 max-w-sm relative">
          <Search className="w-3.5 h-3.5 text-neutral-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full bg-neutral-50 border border-neutral-200 rounded pl-8 pr-3 py-1 text-xs placeholder:text-neutral-400 text-neutral-800 outline-none focus:border-neutral-400 focus:bg-white transition-colors"
          />
        </div>

        <div className="flex items-center gap-2">
          {selectable && selectedKeys.size > 0 && (
            <span className="text-[11px] font-mono text-neutral-500 bg-neutral-100 border border-neutral-200 px-2 py-0.5 rounded">
              {selectedKeys.size} selected
            </span>
          )}
          {actions}
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-neutral-700">
          <thead className="bg-neutral-50 border-b border-neutral-200 text-neutral-500 text-[11px] uppercase tracking-wider font-semibold select-none">
            <tr>
              {selectable && (
                <th className="w-9 px-3 py-2 text-center">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={handleSelectAll}
                    className="rounded border-neutral-300 text-neutral-900 focus:ring-0 cursor-pointer"
                  />
                </th>
              )}
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  onClick={() =>
                    col.sortable && handleSort(col.accessorKey as string)
                  }
                  className={`px-3 py-2 ${
                    col.sortable ? "cursor-pointer hover:text-neutral-900" : ""
                  } ${col.className || ""}`}
                >
                  <div className="flex items-center gap-1">
                    <span>{col.header}</span>
                    {col.sortable && (
                      <span className="text-neutral-400">
                        {sortKey === col.accessorKey ? (
                          sortAsc ? (
                            <ChevronUp className="w-3 h-3 text-neutral-900" />
                          ) : (
                            <ChevronDown className="w-3 h-3 text-neutral-900" />
                          )
                        ) : (
                          <ChevronsUpDown className="w-3 h-3" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 bg-white">
            {sortedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0)}
                  className="px-4 py-8 text-center text-xs text-neutral-400 font-mono"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              sortedData.map((row) => {
                const key = keyExtractor(row);
                const isSelected = selectedKeys.has(key);
                return (
                  <tr
                    key={key}
                    onClick={() => onRowClick && onRowClick(row)}
                    className={`transition-colors ${
                      isSelected
                        ? "bg-neutral-50/80"
                        : "hover:bg-neutral-50/60"
                    } ${onRowClick ? "cursor-pointer" : ""}`}
                  >
                    {selectable && (
                      <td
                        className="px-3 py-2.5 text-center"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleSelectRow(key)}
                          className="rounded border-neutral-300 text-neutral-900 focus:ring-0 cursor-pointer"
                        />
                      </td>
                    )}
                    {columns.map((col, cIdx) => (
                      <td
                        key={cIdx}
                        className={`px-3 py-2.5 ${col.className || ""}`}
                      >
                        {col.cell
                          ? col.cell(row)
                          : col.accessorKey
                          ? String((row as any)[col.accessorKey] ?? "-")
                          : null}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="p-2.5 border-t border-neutral-200 flex items-center justify-between text-[11px] text-neutral-400 font-mono">
        <span>Showing {sortedData.length} entries</span>
        {query && <span>Filtered from {data.length} total</span>}
      </div>
    </div>
  );
}
