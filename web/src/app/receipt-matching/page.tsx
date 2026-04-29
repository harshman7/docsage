"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Receipt, Search } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
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
    <div>
      <PageHeader
        title="Receipt matching"
        description="Link unmatched receipts to transactions the model suggests."
      />
      <ul className="space-y-3">
        {rows.map((r) => (
          <li
            key={String(r.receipt_id)}
            className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5"
          >
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-200">
                <Receipt className="h-5 w-5" />
              </div>
              <span className="truncate font-medium text-slate-900 dark:text-white">
                {String(r.filename)}
              </span>
            </div>
            <button
              type="button"
              className="btn-primary shrink-0 py-2 text-xs sm:text-sm"
              disabled={match.isPending}
              onClick={() => match.mutate(Number(r.receipt_id))}
            >
              <Search className="h-3.5 w-3.5" />
              Find match
            </button>
          </li>
        ))}
        {!rows.length && (
          <div className="card py-14 text-center text-sm text-slate-500 dark:text-slate-300">
            No unmatched receipts in the queue.
          </div>
        )}
      </ul>
      {match.data && (
        <pre className="card mt-6 max-h-64 overflow-auto bg-slate-950 p-4 font-mono text-xs text-teal-100">
          {JSON.stringify(match.data, null, 2)}
        </pre>
      )}
    </div>
  );
}
