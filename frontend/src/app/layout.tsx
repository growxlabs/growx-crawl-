import React from "react";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata = {
  title: "GrowX AutoGTM Platform",
  description: "Autonomous GTM intelligence, ICP definition, and verified prospect prioritization.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('growx_theme') || 'light';
                  var accent = localStorage.getItem('growx_accent') || 'blue';
                  var actual = theme;
                  if (theme === 'system') {
                    actual = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  document.documentElement.setAttribute('data-theme', actual);
                  document.documentElement.setAttribute('data-accent', accent);
                  if (actual === 'dark') {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }
                } catch(e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="h-full antialiased text-gx-ink bg-gx-canvas overflow-hidden">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
