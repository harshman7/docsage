"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet } from "@/lib/api";

type Row = Record<string, unknown>;

export default function ReceiptMatchingPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["unmatched"],
    queryFn: () => apiGet<{ receipts: Row[] }>("/receipt-matching/unmatched"),
  });

  const match = useMutation({
    mutationFn: (id: number) =>
      fetch(
        `${
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        }/api/v1/receipt-matching/${id}/match`,
        { method: "POST" }
      ).then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["unmatched"] }),
  });

  const rows = data?.receipts ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Receipt matching</h1>
      <ul className="space-y-2">
        {rows.map((r) => (
          <li
            key={String(r.receipt_id)}
            className="flex items-center justify-between rounded-lg border bg-white p-3 text-sm"
          >
            <span>{String(r.filename)}</span>
            <button
              type="button"
              className="rounded bg-zinc-900 px-3 py-1 text-white text-xs"
              disabled={match.isPending}
              onClick={() => match.mutate(Number(r.receipt_id))}
            >
              Find match
            </button>
          </li>
        ))}
        {!rows.length && (
          <p className="text-zinc-500 text-sm">No receipt rows.</p>
        )}
      </ul>
      {match.data && (
        <pre className="text-xs bg-zinc-950 text-zinc-100 p-4 rounded-lg overflow-auto">
          {JSON.stringify(match.data, null, 2)}
        </pre>
      )}
    </div>
  );
}
