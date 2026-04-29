"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiGet, apiPostJson } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

type Doc = { id: number; filename: string; document_type: string };

export default function ComparePage() {
  const { data: docs } = useQuery({
    queryKey: ["documents"],
    queryFn: () => apiGet<Doc[]>("/documents"),
  });

  const [a, setA] = useState<number | "">("");
  const [b, setB] = useState<number | "">("");
  const mut = useMutation({
    mutationFn: () =>
      apiPostJson<Record<string, unknown>>("/documents/compare", {
        document_id_1: Number(a),
        document_id_2: Number(b),
      }),
  });

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-semibold">Compare documents</h1>
      <div className="space-y-3">
        <label className="block text-sm font-medium">Document A</label>
        <select
          className="w-full rounded-md border px-3 py-2 text-sm bg-white"
          value={a === "" ? "" : String(a)}
          onChange={(e) =>
            setA(e.target.value ? Number(e.target.value) : "")
          }
        >
          <option value="">Choose…</option>
          {docs?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.filename}
            </option>
          ))}
        </select>
        <label className="block text-sm font-medium pt-2">Document B</label>
        <select
          className="w-full rounded-md border px-3 py-2 text-sm bg-white"
          value={b === "" ? "" : String(b)}
          onChange={(e) =>
            setB(e.target.value ? Number(e.target.value) : "")
          }
        >
          <option value="">Choose…</option>
          {docs?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.filename}
            </option>
          ))}
        </select>
        <button
          type="button"
          className="rounded-md bg-zinc-900 text-white px-4 py-2 text-sm disabled:opacity-50"
          disabled={!a || !b || mut.isPending}
          onClick={() => mut.mutate()}
        >
          Compare
        </button>
      </div>
      {mut.data && (
        <pre className="rounded-lg bg-zinc-950 text-zinc-100 p-4 text-xs overflow-auto max-h-[400px]">
          {JSON.stringify(mut.data, null, 2)}
        </pre>
      )}
      {mut.isError && (
        <p className="text-red-600 text-sm">{(mut.error as Error).message}</p>
      )}
    </div>
  );
}
