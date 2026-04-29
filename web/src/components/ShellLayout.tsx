"use client";

import { usePathname } from "next/navigation";
import { AppShell } from "@/components/AppShell";

export function ShellLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  if (pathname === "/") {
    return <>{children}</>;
  }
  return <AppShell>{children}</AppShell>;
}
