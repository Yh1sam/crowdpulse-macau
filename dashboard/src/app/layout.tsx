import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/Nav";
import { StatusBar } from "@/components/StatusBar";

export const metadata: Metadata = {
  title: "CrowdPulse Macau — operator console",
  description: "Privacy-preserving smartphone crowd intelligence: decision support for crowd-management operators.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col bg-[#111110] text-zinc-100">
        <StatusBar />
        <div className="flex flex-1">
          <Nav />
          <main className="min-w-0 flex-1 p-4 md:p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
