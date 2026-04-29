"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

export default function AnomaliesPage() {
  const { data, isFetching } = useQuery({
    queryKey: ["anomalies"],
    queryFn: () => apiGet<{ anomalies: Record<string, unknown>[] }>(`/anomalies`),
  });

  const list = data?.anomalies ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Anomalies</h1>
      {isFetching && <p className="text-sm text-zinc-500">Loading…</p>}
      <ul className="space-y-2">
        {list.map((a, i) => (
          <li
            key={i}
            className="rounded-lg border border-zinc-200 bg-white p-3 text-sm"
          >
            <div className="font-medium capitalize">{String(a.severity ?? "—")}</div>
            <div className="text-zinc-600">{String(a.message ?? a.type ?? "")}</div>
          </li>
        ))}
        {!list.length && !isFetching && (
          <p className="text-zinc-500 text-sm">No anomalies detected.</p>
        )}
      </ul>
    </div>
  );
}
