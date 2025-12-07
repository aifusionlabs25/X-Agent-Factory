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
      <body className="bg-slate-50 text-slate-900 antialiased flex">
        {/* Main Content Area (Dynamic) - Adjusted width to account for fixed sidebar */}
        <main className="flex-1 min-h-screen mr-[500px] transition-all duration-300">
          {children}
        </main>

        {/* Fixed Right Sidebar */}
        <AgentSidebar />
      </body>
    </html>
  );
}
