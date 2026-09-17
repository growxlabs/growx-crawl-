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
      <body className="h-full antialiased text-[#111318] bg-[#F6F7F9] overflow-hidden">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
