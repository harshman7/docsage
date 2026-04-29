"use client";

import { useMutation } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { apiPostJson } from "@/lib/api";

export default function InsightsPage() {
  const mut = useMutation({
    mutationFn: () =>
      apiPostJson<{ report_markdown: string }>(
        "/insights/generate-report",
        {}
      ),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">AI insights report</h1>
      <button
        type="button"
        className="rounded-md bg-zinc-900 text-white px-4 py-2 text-sm disabled:opacity-50"
        disabled={mut.isPending}
        onClick={() => mut.mutate()}
      >
        Generate report
      </button>
      {mut.error && (
        <p className="text-red-600 text-sm">{(mut.error as Error).message}</p>
      )}
      {mut.data && (
        <article className="rounded-xl border bg-white p-6 text-sm leading-relaxed max-w-none">
          <ReactMarkdown>{mut.data.report_markdown}</ReactMarkdown>
        </article>
      )}
    </div>
  );
}
