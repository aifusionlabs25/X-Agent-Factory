import type { Metadata } from "next";
import "./globals.css";
import AgentSidebar from "@/components/AgentSidebar";

export const metadata: Metadata = {
  title: "X Agent Factory | Forge",
  description: "Advanced Agentic Coding Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">
        {/* Main Content Area - Full width now, sidebar controlled per-page */}
        <main className="min-h-screen transition-all duration-300">
          {children}
        </main>
      </body>
    </html>
  );
}
