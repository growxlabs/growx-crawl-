"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Users,
  Key,
  CreditCard,
  Gift,
  Bell,
  HelpCircle,
  MessageSquare,
  LogOut,
  ChevronDown,
  Sun,
  Moon,
  Monitor,
  Terminal,
} from "lucide-react";
import { useTheme, ThemeMode, AccentColor } from "@/context/ThemeContext";

const ACCENTS: { id: AccentColor; label: string; bgClass: string }[] = [
  { id: "blue", label: "Electric Blue", bgClass: "bg-[#315EF5]" },
  { id: "green", label: "Emerald Green", bgClass: "bg-[#10B981]" },
  { id: "orange", label: "Sunset Orange", bgClass: "bg-[#F97316]" },
  { id: "pink", label: "Rose Pink", bgClass: "bg-[#EC4899]" },
  { id: "purple", label: "Royal Purple", bgClass: "bg-[#8B5CF6]" },
];

const THEMES: { id: ThemeMode; label: string; icon: React.ReactNode }[] = [
  { id: "light", label: "Light", icon: <Sun className="w-3.5 h-3.5" /> },
  { id: "system", label: "System", icon: <Monitor className="w-3.5 h-3.5" /> },
  { id: "dark", label: "Dark", icon: <Moon className="w-3.5 h-3.5" /> },
];

export function AccountPopover({ userEmail = "growxlabstech@gmail.com" }: { userEmail?: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const { theme, setTheme, accent, setAccent } = useTheme();

  return (
    <div className="relative">
      {/* Trigger Button matching Explee footer */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-gx-surface-hover text-left transition-colors group select-none"
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-6 h-6 rounded-full bg-gx-surface-soft border border-gx-border flex items-center justify-center text-xs font-semibold text-gx-ink flex-shrink-0">
            {userEmail.charAt(0).toUpperCase()}
          </div>
          <span className="text-xs text-gx-ink-secondary group-hover:text-gx-ink truncate max-w-[170px]">
            {userEmail}
          </span>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-gx-ink-muted flex-shrink-0 ml-1" />
      </button>

      {/* Popover Card matching Explee media_1789643485230.png */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute bottom-full left-0 mb-2 w-72 bg-gx-surface border border-gx-border rounded-xl p-2 shadow-2xl z-50 text-xs text-gx-ink space-y-1 animate-in fade-in-50 slide-in-from-bottom-2 duration-150 select-none">
            {/* User Header */}
            <div className="px-3 py-2 border-b border-gx-border-soft">
              <div className="font-semibold text-gx-ink truncate">{userEmail}</div>
            </div>

            {/* Menu Items */}
            <div className="py-1 space-y-0.5">
              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <Users className="w-4 h-4 text-gx-ink-muted" />
                <span>Team</span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <Key className="w-4 h-4 text-gx-ink-muted" />
                <span>API Keys</span>
              </button>

              <Link
                href="/ops"
                className="w-full flex items-center justify-between px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <div className="flex items-center gap-2.5">
                  <Terminal className="w-4 h-4 text-gx-ink-muted" />
                  <span>Operations Console</span>
                </div>
                <span className="text-[10px] font-mono text-gx-ink-muted">/ops</span>
              </Link>

              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <CreditCard className="w-4 h-4 text-gx-ink-muted" />
                <span>Billing</span>
              </button>

              <button
                type="button"
                className="w-full flex items-center justify-between px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <div className="flex items-center gap-2.5">
                  <Gift className="w-4 h-4 text-gx-ink-muted" />
                  <span>Refer a friend</span>
                </div>
                <span className="text-[10px] font-semibold bg-gx-success-soft text-gx-success border border-gx-success/30 px-1.5 py-0.5 rounded">
                  Earn $25
                </span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <Bell className="w-4 h-4 text-gx-ink-muted" />
                <span>Notifications</span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <HelpCircle className="w-4 h-4 text-gx-ink-muted" />
                <span>Help</span>
              </button>

              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <MessageSquare className="w-4 h-4 text-gx-ink-muted" />
                <span>Feedback</span>
              </button>
            </div>

            {/* Theme Setting Section */}
            <div className="pt-2 pb-1 border-t border-gx-border-soft px-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gx-ink-secondary">Theme</span>
                <div className="flex items-center bg-gx-surface-soft border border-gx-border p-0.5 rounded-lg">
                  {THEMES.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setTheme(t.id)}
                      title={`Mode: ${t.label}`}
                      className={`p-1 rounded text-xs transition-colors flex items-center justify-center ${
                        theme === t.id
                          ? "bg-gx-surface text-gx-ink shadow-2xs font-semibold"
                          : "text-gx-ink-muted hover:text-gx-ink"
                      }`}
                    >
                      {t.icon}
                    </button>
                  ))}
                </div>
              </div>

              {/* Accent Color Selection Row */}
              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] text-gx-ink-muted">Accent</span>
                <div className="flex items-center gap-1.5">
                  {ACCENTS.map((a) => (
                    <button
                      key={a.id}
                      type="button"
                      onClick={() => setAccent(a.id)}
                      title={a.label}
                      className={`w-4 h-4 rounded-full ${a.bgClass} flex items-center justify-center transition-all ${
                        accent === a.id
                          ? "ring-2 ring-offset-1 ring-offset-gx-surface ring-gx-primary scale-110"
                          : "opacity-75 hover:opacity-100 hover:scale-105"
                      }`}
                    >
                      {accent === a.id && (
                        <span className="w-1.5 h-1.5 rounded-full bg-white block" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Sign out */}
            <div className="pt-1 border-t border-gx-border-soft">
              <button
                type="button"
                className="w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-gx-surface-hover text-gx-ink-secondary hover:text-gx-ink text-left transition-colors"
                onClick={() => setIsOpen(false)}
              >
                <LogOut className="w-4 h-4 text-gx-ink-muted" />
                <span>Sign out</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
