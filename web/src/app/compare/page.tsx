"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { GitCompare } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { apiGet, apiPostJson } from "@/lib/api";

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
    <div className="mx-auto max-w-xl">
      <PageHeader
        title="Compare documents"
        description="Select two processed documents to diff structured fields side by side."
      />
      <div className="card space-y-5 p-6">
        <div>
          <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Document A
          </label>
          <select
            className="select-field"
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
        </div>
        <div>
          <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-300">
            Document B
          </label>
          <select
            className="select-field"
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
        </div>
        <button
          type="button"
          className="btn-primary w-full"
          disabled={!a || !b || mut.isPending}
          onClick={() => mut.mutate()}
        >
          <GitCompare className="h-4 w-4" />
          Compare
        </button>
      </div>
      {mut.data && (
        <pre className="card mt-6 max-h-[400px] overflow-auto bg-slate-950 p-4 font-mono text-xs leading-relaxed text-teal-100">
          {JSON.stringify(mut.data, null, 2)}
        </pre>
      )}
      {mut.isError && (
        <p className="mt-4 text-sm text-red-600 dark:text-red-400">
          {(mut.error as Error).message}
        </p>
      )}
    </div>
  );
}
