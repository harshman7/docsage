"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { apiGet } from "@/lib/api";

const severityStyles: Record<string, string> = {
  high: "bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-300",
  medium:
    "bg-amber-100 text-amber-900 dark:bg-amber-950/50 dark:text-amber-200",
  low: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

export default function AnomaliesPage() {
  const { data, isFetching } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () => apiGet<{ anomalies: Record<string, unknown>[] }>(`/anomalies`),
  });

  const list = data?.anomalies ?? [];

  return (
    <div>
      <PageHeader
        title="Anomalies"
        description="Unusual patterns and flags surfaced from your transaction and document data."
      />
      {isFetching && (
        <div className="mb-6 flex items-center gap-2 text-sm text-slate-500 dark:text-slate-300">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </div>
      )}
      <ul className="space-y-3">
        {list.map((a, i) => {
          const sev = String(a.severity ?? "low").toLowerCase();
          const badgeClass =
            severityStyles[sev] ??
            "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
          return (
            <li key={i} className="card flex gap-4 p-4 sm:p-5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                <AlertTriangle className="h-5 w-5" strokeWidth={2} />
              </div>
              <div className="min-w-0 flex-1">
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${badgeClass}`}
                >
                  {String(a.severity ?? "—")}
                </span>
                <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-200">
                  {String(a.message ?? a.type ?? "")}
                </p>
              </div>
            </li>
          );
        })}
        {!list.length && !isFetching && (
          <div className="card flex flex-col items-center py-14 text-center">
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400">
              <AlertTriangle className="h-6 w-6 opacity-40" />
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300">
              No anomalies detected. You&apos;re all clear.
            </p>
          </div>
        )}
      </ul>
    </div>
  );
}
