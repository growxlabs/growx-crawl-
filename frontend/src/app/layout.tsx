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
    <html lang="en" className="h-full">
      <body className="h-full antialiased text-neutral-900 bg-neutral-50/50">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
