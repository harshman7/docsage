"use client";

import type { LucideIcon } from "lucide-react";
import { FileText, Receipt, TrendingUp, Wallet } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useTheme } from "next-themes";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
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

type TimePreset = "all" | "last_12_months" | "last_3_years" | "last_5_years";

type TimeSeriesResponse = {
  monthly: { date: string; amount: number }[];
  yearly: { date: string; amount: number }[];
  daily: { date: string; amount: number }[];
  granularity: "month" | "year";
  range: { start: string | null; end: string | null };
  transactions_in_range: number;
  transactions_without_date: number;
  vendor_trends: Record<string, { date: string; amount: number }[]>;
};

type CategoryRow = {
  category: string;
  total_spend: number;
  transaction_count: number;
};

const PRESETS: { id: TimePreset; label: string }[] = [
  { id: "all", label: "All time" },
  { id: "last_12_months", label: "12 months" },
  { id: "last_3_years", label: "3 years" },
  { id: "last_5_years", label: "5 years" },
];

const MONTH_SHORT = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function formatSpendXTick(
  granularity: "month" | "year",
  raw: string,
  multiYear: boolean,
): string {
  if (granularity === "year") return raw;
  if (raw.length >= 7 && raw.includes("-")) {
    const [y, m] = raw.split("-");
    const mi = parseInt(m, 10) - 1;
    if (mi >= 0 && mi < 12) {
      return multiYear ? `${MONTH_SHORT[mi]} ${y}` : MONTH_SHORT[mi];
    }
  }
  return raw;
}

export default function DashboardPage() {
  const [preset, setPreset] = useState<TimePreset>("all");

  const { data: summary } = useQuery({
    queryKey: ["summary"],
    queryFn: () => apiGet<Summary>("/analytics/summary"),
  });

  const { data: ts } = useQuery({
    queryKey: ["time-series", preset],
    queryFn: () =>
      apiGet<TimeSeriesResponse>(
        `/analytics/time-series?preset=${encodeURIComponent(preset)}&granularity=auto`,
      ),
  });

  const { data: categories } = useQuery({
    queryKey: ["category-breakdown"],
    queryFn: () => apiGet<CategoryRow[]>("/analytics/category-breakdown"),
  });

  const chartSeries = useMemo(() => {
    if (!ts) return [];
    return ts.granularity === "year" ? ts.yearly : ts.monthly;
  }, [ts]);

  const multiYear = useMemo(() => {
    if (!ts || ts.granularity !== "month" || chartSeries.length < 2) return false;
    const y0 = chartSeries[0].date.slice(0, 4);
    const y1 = chartSeries[chartSeries.length - 1].date.slice(0, 4);
    return y0 !== y1;
  }, [ts, chartSeries]);

  const categoryChartData = useMemo(() => {
    const rows = categories ?? [];
    return rows.slice(0, 10).map((r) => ({
      label:
        r.category.length > 42
          ? `${r.category.slice(0, 40)}…`
          : r.category,
      fullLabel: r.category,
      total_spend: r.total_spend,
      transaction_count: r.transaction_count,
    }));
  }, [categories]);

  const hasChartPoints = chartSeries.length > 0;

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
          iconBg="from-teal-500/15 to-teal-600/5 text-teal-700 dark:from-teal-950/80 dark:to-slate-950 dark:text-teal-300"
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
          iconBg="from-amber-500/15 to-amber-600/5 text-amber-800 dark:from-teal-800/25 dark:to-teal-950/60 dark:text-teal-200"
        />
      </div>

      <section className="mt-10">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-neutral-500">
              Spending over time
            </h2>
            {ts?.range?.start && ts?.range?.end && (
              <p className="mt-1 text-xs text-slate-500 dark:text-neutral-500">
                Range:{" "}
                <span className="font-medium text-slate-700 dark:text-neutral-300">
                  {new Date(ts.range.start).toLocaleDateString()} —{" "}
                  {new Date(ts.range.end).toLocaleDateString()}
                </span>
                {ts.granularity === "year"
                  ? " (yearly totals)"
                  : " (monthly totals)"}
                {ts.transactions_in_range != null && (
                  <>
                    {" "}
                    · {ts.transactions_in_range} dated transaction
                    {ts.transactions_in_range === 1 ? "" : "s"} in view
                  </>
                )}
              </p>
            )}
          </div>
          <div
            className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/90 p-1 dark:border-neutral-700 dark:bg-neutral-900/60"
            role="tablist"
            aria-label="Time range"
          >
            {PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                role="tab"
                aria-selected={preset === p.id}
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition sm:text-sm ${
                  preset === p.id
                    ? "bg-white text-slate-900 shadow-sm dark:bg-neutral-800 dark:text-white"
                    : "text-slate-600 hover:text-slate-900 dark:text-neutral-400 dark:hover:text-white"
                }`}
                onClick={() => setPreset(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="card p-5 sm:p-6">
          {hasChartPoints ? (
            <SpendingLineChart
              data={chartSeries}
              granularity={ts?.granularity ?? "month"}
              multiYear={multiYear}
            />
          ) : (
            <div className="flex min-h-72 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/80 px-4 text-center dark:border-neutral-700 dark:bg-[#080808]">
              <p className="text-sm text-slate-600 dark:text-neutral-400">
                No dated transactions in this range.
              </p>
              <p className="mt-2 text-xs text-slate-500 dark:text-neutral-500">
                Try &quot;All time&quot; for historical data, or upload documents with
                transaction dates.
              </p>
            </div>
          )}
          {ts && ts.transactions_without_date > 0 && (
            <p className="mt-3 text-xs text-amber-800 dark:text-amber-200/90 border-t border-slate-200/80 dark:border-neutral-700 pt-3">
              {ts.transactions_without_date} transaction
              {ts.transactions_without_date === 1 ? "" : "s"} have no date and are
              omitted from this chart (totals in stat cards still include them).
            </p>
          )}
        </div>
      </section>

      <section className="mt-10">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-neutral-500">
          Spending by category
        </h2>
        <div className="card p-5 sm:p-6">
          {categoryChartData.length > 0 ? (
            <CategoryBarChart data={categoryChartData} />
          ) : (
            <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/80 text-sm text-slate-500 dark:border-neutral-700 dark:bg-[#080808] dark:text-neutral-400">
              No category data yet.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function SpendingLineChart({
  data,
  granularity,
  multiYear,
}: {
  data: { date: string; amount: number }[];
  granularity: "month" | "year";
  multiYear: boolean;
}) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const dark = mounted && resolvedTheme === "dark";
  const tickFill = dark ? "#d4d4d4" : "rgb(100 116 139)";
  const gridStroke = dark ? "rgba(64, 64, 64, 0.85)" : "rgb(148 163 184 / 0.25)";
  const lineColor = "#0d9488";
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

  const tickFormatter = (v: string) =>
    formatSpendXTick(granularity, v, multiYear);

  return (
    <ResponsiveContainer width="100%" height={288}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 4, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: tickFill }}
          axisLine={false}
          tickLine={false}
          interval="preserveStartEnd"
          minTickGap={16}
          tickFormatter={tickFormatter}
        />
        <YAxis
          tick={{ fontSize: 12, fill: tickFill }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${Number(v).toLocaleString()}`}
          width={56}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          labelStyle={{ fontSize: 12, fontWeight: 600 }}
          labelFormatter={(label) =>
            granularity === "year"
              ? `Year ${label}`
              : formatSpendXTick("month", String(label), true)
          }
          formatter={(value) => [
            `$${Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
            "Spend",
          ]}
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

type CatDatum = {
  label: string;
  fullLabel: string;
  total_spend: number;
  transaction_count: number;
};

function CategoryBarChart({ data }: { data: CatDatum[] }) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const dark = mounted && resolvedTheme === "dark";
  const tickFill = dark ? "#d4d4d4" : "rgb(100 116 139)";
  const gridStroke = dark ? "rgba(64, 64, 64, 0.85)" : "rgb(148 163 184 / 0.25)";
  const barFill = "#0d9488";
  const tooltipStyle = dark
    ? {
        borderRadius: 12,
        background: "#0a0a0a",
        border: "1px solid #404040",
        color: "#fafafa",
        maxWidth: 320,
      }
    : {
        borderRadius: 12,
        border: "1px solid rgb(226 232 240)",
        maxWidth: 320,
      };

  const chartData = [...data].reverse();

  return (
    <ResponsiveContainer width="100%" height={Math.max(280, data.length * 36)}>
      <BarChart
        layout="vertical"
        data={chartData}
        margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={gridStroke} horizontal={false} />
        <XAxis
          type="number"
          tick={{ fontSize: 11, fill: tickFill }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${Number(v).toLocaleString()}`}
        />
        <YAxis
          type="category"
          dataKey="label"
          width={148}
          tick={{ fontSize: 11, fill: tickFill }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={tooltipStyle}
          formatter={(value) => [
            `$${Number(value ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`,
            "Spend",
          ]}
          labelFormatter={(_, payload) => {
            const row = payload?.[0]?.payload as CatDatum | undefined;
            return row?.fullLabel ?? "";
          }}
        />
        <Bar dataKey="total_spend" fill={barFill} radius={[0, 6, 6, 0]} />
      </BarChart>
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
        className={`mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ring-1 ring-black/5 dark:ring-teal-500/25 ${iconBg}`}
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
