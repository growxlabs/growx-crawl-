"use client";

import React, { useState } from "react";
import { Sun, Moon, Monitor, Palette } from "lucide-react";
import { useTheme, ThemeMode, AccentColor } from "@/context/ThemeContext";

export const ACCENTS: { id: AccentColor; label: string; bgClass: string }[] = [
  { id: "blue", label: "Electric Blue", bgClass: "bg-[#315EF5]" },
  { id: "green", label: "Emerald Green", bgClass: "bg-[#10B981]" },
  { id: "orange", label: "Sunset Orange", bgClass: "bg-[#F97316]" },
  { id: "pink", label: "Rose Pink", bgClass: "bg-[#EC4899]" },
  { id: "purple", label: "Royal Purple", bgClass: "bg-[#8B5CF6]" },
];

export const THEMES: { id: ThemeMode; label: string; icon: React.ReactNode }[] = [
  { id: "light", label: "Light", icon: <Sun className="w-3.5 h-3.5" /> },
  { id: "dark", label: "Dark", icon: <Moon className="w-3.5 h-3.5" /> },
  { id: "system", label: "System", icon: <Monitor className="w-3.5 h-3.5" /> },
];

export function AppearancePopover() {
  const [isOpen, setIsOpen] = useState(false);
  const { theme, setTheme, accent, setAccent } = useTheme();

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-gx-ink-secondary hover:text-gx-ink hover:bg-gx-surface-hover transition-colors group"
        title="Customize appearance (theme & accent colors)"
      >
        <Palette className="w-3.5 h-3.5 text-gx-ink-muted group-hover:text-gx-ink-secondary" />
        <span className="font-medium">Theme</span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-30"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute bottom-full left-0 mb-2 w-64 bg-gx-surface border border-gx-border rounded-xl p-3 shadow-xl z-40 space-y-3 text-xs animate-in fade-in-50 slide-in-from-bottom-2 duration-150">
            <div>
              <div className="text-[10px] font-semibold text-gx-ink-muted uppercase tracking-wider mb-1.5">
                Theme Mode
              </div>
              <div className="grid grid-cols-3 gap-1 bg-gx-surface-soft p-1 rounded-lg border border-gx-border">
                {THEMES.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    className={`flex items-center justify-center gap-1.5 py-1 px-1.5 rounded text-xs transition-colors ${
                      theme === t.id
                        ? "bg-gx-surface text-gx-ink font-semibold shadow-2xs"
                        : "text-gx-ink-muted hover:text-gx-ink"
                    }`}
                  >
                    {t.icon}
                    <span className="capitalize text-[10px]">{t.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-semibold text-gx-ink-muted uppercase tracking-wider mb-1.5">
                Accent Color
              </div>
              <div className="flex items-center justify-between bg-gx-surface-soft p-2 rounded-lg border border-gx-border">
                {ACCENTS.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => setAccent(a.id)}
                    title={a.label}
                    className={`w-6 h-6 rounded-full ${a.bgClass} flex items-center justify-center transition-all ${
                      accent === a.id
                        ? "ring-2 ring-offset-2 ring-offset-gx-surface ring-gx-primary scale-110"
                        : "opacity-80 hover:opacity-100 hover:scale-105"
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
        </>
      )}
    </div>
  );
}

export function ThemeSelector() {
  return <AppearancePopover />;
}
