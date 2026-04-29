"use client";

import type { LucideIcon } from "lucide-react";
import { FileText, Receipt, TrendingUp, Wallet } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/PageHeader";
import { apiGet } from "@/lib/api";

type Summary = {
  total_transactions: number;
  total_spend: number;
  avg_transaction: number;
  document_count: number;
};

export default function DashboardPage() {
  const { data: summary } = useQuery({
    queryKey: ["summary"],
    queryFn: () => apiGet<Summary>("/analytics/summary"),
  });
  const { data: ts } = useQuery({
    queryKey: ["time-series"],
    queryFn: () =>
      apiGet<{
        monthly: { date: string; amount: number }[];
        daily: { date: string; amount: number }[];
      }>("/analytics/time-series"),
  });

  const monthly = ts?.monthly?.map((r) => ({
    date: r.date,
    amount: r.amount,
  })) ?? [];

  return (
    <div>
      <PageHeader
        title="Analytics"
        description="Track spend, volume, and trends across your processed documents."
      />
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        <Stat
          label="Transactions"
          value={summary?.total_transactions?.toLocaleString() ?? "—"}
          icon={Receipt}
          iconBg="from-sky-500/15 to-sky-600/5 text-sky-700 dark:from-sky-950 dark:to-slate-950 dark:text-sky-300"
        />
        <Stat
          label="Total spend"
          value={
            summary != null
              ? `$${summary.total_spend.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}`
              : "—"
          }
          icon={Wallet}
          iconBg="from-teal-500/15 to-teal-600/5 text-teal-700 dark:from-amber-500/25 dark:to-amber-950/50 dark:text-amber-300"
        />
        <Stat
          label="Avg transaction"
          value={
            summary != null
              ? `$${summary.avg_transaction.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}`
              : "—"
          }
          icon={TrendingUp}
          iconBg="from-violet-500/15 to-violet-600/5 text-violet-700 dark:from-violet-950 dark:to-neutral-950 dark:text-violet-300"
        />
        <Stat
          label="Documents"
          value={summary?.document_count?.toLocaleString() ?? "—"}
          icon={FileText}
          iconBg="from-amber-500/15 to-amber-600/5 text-amber-800 dark:from-amber-600/20 dark:to-amber-950 dark:text-amber-200"
        />
      </div>
      <section className="mt-10">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-neutral-500">
          Monthly spending
        </h2>
        <div className="card p-5 sm:p-6">
          {monthly.length > 0 ? (
            <MonthlyChart data={monthly} />
          ) : (
            <div className="flex h-72 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/80 dark:border-neutral-700 dark:bg-[#080808]">
              <p className="text-sm text-slate-500 dark:text-neutral-400">
                No time-series data yet. Upload documents to see trends.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function MonthlyChart({ data }: { data: { date: string; amount: number }[] }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const dark = mounted && resolvedTheme === "dark";
  const tickFill = dark ? "#d4d4d4" : "rgb(100 116 139)";
  const gridStroke = dark ? "rgba(64, 64, 64, 0.85)" : "rgb(148 163 184 / 0.25)";
  const lineColor = dark ? "#d4af37" : "#0d9488";
  const tooltipStyle = dark
    ? {
        borderRadius: 12,
        background: "#0a0a0a",
        border: "1px solid #404040",
        color: "#fafafa",
        boxShadow: "0 12px 40px rgba(0,0,0,0.75)",
      }
    : {
        borderRadius: 12,
        border: "1px solid rgb(226 232 240)",
        boxShadow: "0 4px 20px rgba(15,23,42,0.08)",
        color: "#0f172a",
      };

  return (
    <ResponsiveContainer width="100%" height={288}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: tickFill }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12, fill: tickFill }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${v}`}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={{ fontSize: 12, fontWeight: 600 }}
        />
        <Line
          type="monotone"
          dataKey="amount"
          stroke={lineColor}
          strokeWidth={2.5}
          dot={false}
          activeDot={{
            r: 5,
            fill: lineColor,
            stroke: dark ? "#050505" : "#fff",
            strokeWidth: 2,
          }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

function Stat({
  label,
  value,
  icon: Icon,
  iconBg,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  iconBg: string;
}) {
  return (
    <div className="card group relative overflow-hidden p-4 transition hover:shadow-md sm:p-5">
      <div
        className={`mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ring-1 ring-black/5 dark:ring-amber-500/20 ${iconBg}`}
      >
        <Icon className="h-5 w-5" strokeWidth={2} />
      </div>
      <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-neutral-500">
        {label}
      </div>
      <div className="mt-1.5 font-display text-xl font-semibold tracking-tight text-slate-900 tabular-nums dark:text-white sm:text-2xl">
        {value}
      </div>
    </div>
  );
}
