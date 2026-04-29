"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <div
        className={`h-9 w-9 shrink-0 rounded-xl border border-transparent ${className}`}
        aria-hidden
      />
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/40 active:scale-95 border-slate-200/80 bg-white/80 text-slate-700 hover:border-teal-300/50 hover:bg-teal-50/80 hover:text-teal-800 dark:border-teal-800/50 dark:bg-black dark:text-teal-400 dark:shadow-[0_0_20px_-6px_rgba(13,148,136,0.35)] dark:hover:border-teal-600/55 dark:hover:bg-neutral-950 dark:hover:text-teal-300 dark:focus-visible:ring-teal-500/50 ${className}`}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      {isDark ? <Sun className="h-4 w-4" strokeWidth={2} /> : <Moon className="h-4 w-4" strokeWidth={2} />}
    </button>
  );
}
