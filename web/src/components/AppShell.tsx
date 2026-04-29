"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";
import {
  AlertTriangle,
  Download,
  FileStack,
  GitCompare,
  LayoutDashboard,
  MessageSquare,
  Receipt,
  Sparkles,
} from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

const easeApple = [0.25, 0.1, 0.25, 1] as const;

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/documents", label: "Documents", icon: FileStack },
  { href: "/anomalies", label: "Anomalies", icon: AlertTriangle },
  { href: "/compare", label: "Compare", icon: GitCompare },
  { href: "/insights", label: "Insights", icon: Sparkles },
  { href: "/receipt-matching", label: "Receipts", icon: Receipt },
  { href: "/export", label: "Export", icon: Download },
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const reduce = useReducedMotion();

  return (
    <div className="mesh-bg min-h-screen text-slate-900 dark:text-neutral-100">
      <div className="flex min-h-screen flex-col md:flex-row">
        <aside className="sticky top-0 z-20 w-full shrink-0 border-b border-slate-200/60 bg-white/90 px-4 py-4 backdrop-blur-xl dark:border-neutral-800 dark:bg-[#030303] dark:backdrop-blur-none md:h-screen md:w-64 md:border-b-0 md:border-r md:px-4 md:py-7">
          <div className="mb-4 flex items-start justify-between gap-2 md:mb-6">
            <motion.div
              className="min-w-0 flex-1"
              initial={reduce ? false : { opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease: easeApple }}
            >
              <motion.div
                whileHover={reduce ? undefined : { scale: 1.03 }}
                whileTap={reduce ? undefined : { scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                <Link
                  href="/"
                  className="flex items-center gap-3 rounded-xl px-1.5 py-1.5 transition hover:bg-slate-50/90 dark:hover:bg-neutral-900"
                >
                  <Image
                    src="/logo.png"
                    alt="DocSage"
                    width={176}
                    height={48}
                    className="h-10 w-auto sm:h-11"
                  />
                  <div className="min-w-0 leading-tight">
                    <div className="font-display truncate text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
                      DocSage
                    </div>
                    <div className="text-[11px] font-medium text-slate-500 dark:text-neutral-500">
                      Document intelligence
                    </div>
                  </div>
                </Link>
              </motion.div>
            </motion.div>
            <ThemeToggle className="md:mt-1" />
          </div>
          <nav className="flex flex-row gap-1 overflow-x-auto pb-1 md:flex-col md:overflow-visible md:pb-0">
            {links.map(({ href, label, icon: Icon }, i) => {
              const active = pathname === href;
              return (
                <motion.div
                  key={href}
                  initial={reduce ? false : { opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    delay: reduce ? 0 : 0.05 + i * 0.045,
                    duration: 0.48,
                    ease: easeApple,
                  }}
                >
                  <Link
                    href={href}
                    className={`flex items-center gap-2.5 whitespace-nowrap rounded-xl px-3 py-2.5 text-sm font-medium transition hover:scale-[1.01] active:scale-[0.99] ${
                      active
                        ? "bg-teal-600 text-white shadow-sm shadow-teal-900/15 dark:bg-amber-500/20 dark:text-amber-300 dark:shadow-[0_0_28px_-6px_rgba(212,175,55,0.45)] dark:ring-1 dark:ring-amber-500/50"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-neutral-400 dark:hover:bg-neutral-900/90 dark:hover:text-amber-100"
                    }`}
                  >
                    <Icon
                      className="h-4 w-4 shrink-0 opacity-90"
                      strokeWidth={active ? 2.25 : 2}
                    />
                    {label}
                  </Link>
                </motion.div>
              );
            })}
          </nav>
        </aside>
        <main className="relative flex-1 px-4 py-8 sm:px-6 lg:px-10">
          <motion.div
            className="mx-auto w-full max-w-6xl"
            initial={reduce ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.08, ease: easeApple }}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </div>
  );
}
