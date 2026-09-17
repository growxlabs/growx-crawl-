"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  const pathname = usePathname();

  // Auto-generate items if not explicitly provided
  const generatedItems: BreadcrumbItem[] = React.useMemo(() => {
    if (items && items.length > 0) return items;

    const segments = pathname.split("/").filter(Boolean);
    const crumbs: BreadcrumbItem[] = [];

    let accumulatedPath = "";
    for (const segment of segments) {
      accumulatedPath += `/${segment}`;
      let label = segment
        .replace(/-/g, " ")
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());

      // Format known ID patterns
      if (segment.startsWith("prj_")) {
        label = "Project Details";
      } else if (segment.startsWith("cmp_")) {
        label = "Company Details";
      } else if (segment.startsWith("prs_")) {
        label = "Person Details";
      } else if (segment.startsWith("icp_")) {
        label = "ICP Profile";
      }

      crumbs.push({
        label,
        href: accumulatedPath,
      });
    }

    return crumbs;
  }, [items, pathname]);

  if (generatedItems.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-1 text-xs text-neutral-400 select-none">
      <Link
        href="/projects"
        className="hover:text-neutral-700 transition-colors flex items-center gap-1"
      >
        <Home className="w-3 h-3" />
      </Link>
      {generatedItems.map((crumb, idx) => {
        const isLast = idx === generatedItems.length - 1;
        return (
          <React.Fragment key={crumb.href || idx}>
            <ChevronRight className="w-3 h-3 text-neutral-300 flex-shrink-0" />
            {isLast || !crumb.href ? (
              <span className="font-semibold text-neutral-900 truncate max-w-xs">
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="hover:text-neutral-700 transition-colors truncate max-w-xs"
              >
                {crumb.label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
