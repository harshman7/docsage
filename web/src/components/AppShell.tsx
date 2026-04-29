"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/chat", label: "Chat" },
  { href: "/documents", label: "Documents" },
  { href: "/anomalies", label: "Anomalies" },
  { href: "/compare", label: "Compare" },
  { href: "/insights", label: "Insights" },
  { href: "/receipt-matching", label: "Receipts" },
  { href: "/export", label: "Export" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-zinc-50 text-zinc-900">
      <aside className="w-full md:w-56 shrink-0 border-b md:border-b-0 md:border-r border-zinc-200 bg-white p-4">
        <div className="font-semibold tracking-tight mb-6">DocSage</div>
        <nav className="flex flex-row md:flex-col gap-1 flex-wrap">
          {links.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`rounded-md px-3 py-2 text-sm ${
                  active
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-700 hover:bg-zinc-100"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <main className="flex-1 p-6 max-w-6xl mx-auto w-full">{children}</main>
    </div>
  );
}
