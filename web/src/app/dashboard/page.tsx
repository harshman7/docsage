"use client";

import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
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
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat
          label="Transactions"
          value={summary?.total_transactions?.toLocaleString() ?? "—"}
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
        />
        <Stat
          label="Documents"
          value={summary?.document_count?.toLocaleString() ?? "—"}
        />
      </div>
      <section>
        <h2 className="text-lg font-medium mb-4">Monthly spending</h2>
        <div className="h-72 w-full rounded-lg border border-zinc-200 bg-white p-4">
          {monthly.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#18181b" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-zinc-500 text-sm">No time-series data yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="text-xl font-semibold mt-1">{value}</div>
    </div>
  );
}
