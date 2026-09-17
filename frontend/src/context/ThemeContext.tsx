"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type ThemeMode = "light" | "dark" | "system";
export type AccentColor = "blue" | "green" | "orange" | "pink" | "purple";

interface ThemeContextType {
  theme: ThemeMode;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: ThemeMode) => void;
  accent: AccentColor;
  setAccent: (accent: AccentColor) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>("light");
  const [accent, setAccentState] = useState<AccentColor>("blue");
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("light");

  // Initialize from localStorage
  useEffect(() => {
    try {
      const storedTheme = localStorage.getItem("growx_theme") as ThemeMode | null;
      const storedAccent = localStorage.getItem("growx_accent") as AccentColor | null;

      if (storedTheme && ["light", "dark", "system"].includes(storedTheme)) {
        setThemeState(storedTheme);
      }
      if (
        storedAccent &&
        ["blue", "green", "orange", "pink", "purple"].includes(storedAccent)
      ) {
        setAccentState(storedAccent);
      }
    } catch {
      // Ignore localStorage read errors
    }
  }, []);

  // Compute resolved theme and update DOM attributes
  useEffect(() => {
    const getSystemTheme = (): "light" | "dark" => {
      if (typeof window === "undefined") return "light";
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };

    const actual = theme === "system" ? getSystemTheme() : theme;
    setResolvedTheme(actual);

    const root = document.documentElement;
    root.setAttribute("data-theme", actual);
    root.setAttribute("data-accent", accent);

    if (actual === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }

    // Media query listener when in system mode
    if (theme === "system") {
      const media = window.matchMedia("(prefers-color-scheme: dark)");
      const handler = (e: MediaQueryListEvent) => {
        const newActual = e.matches ? "dark" : "light";
        setResolvedTheme(newActual);
        root.setAttribute("data-theme", newActual);
        if (newActual === "dark") {
          root.classList.add("dark");
        } else {
          root.classList.remove("dark");
        }
      };
      media.addEventListener("change", handler);
      return () => media.removeEventListener("change", handler);
    }
  }, [theme, accent]);

  const setTheme = (newTheme: ThemeMode) => {
    setThemeState(newTheme);
    try {
      localStorage.setItem("growx_theme", newTheme);
    } catch {
      // Ignore localStorage write errors
    }
  };

  const setAccent = (newAccent: AccentColor) => {
    setAccentState(newAccent);
    try {
      localStorage.setItem("growx_accent", newAccent);
    } catch {
      // Ignore localStorage write errors
    }
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        resolvedTheme,
        setTheme,
        accent,
        setAccent,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
