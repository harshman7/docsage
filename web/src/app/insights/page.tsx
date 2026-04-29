"use client";

import { useMutation } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import { Loader2, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
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
    <div>
      <PageHeader
        title="AI insights report"
        description="Generate a markdown narrative summarizing patterns in your data."
      />
      <button
        type="button"
        className="btn-primary"
        disabled={mut.isPending}
        onClick={() => mut.mutate()}
      >
        {mut.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Generating…
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            Generate report
          </>
        )}
      </button>
      {mut.error && (
        <p className="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
          {(mut.error as Error).message}
        </p>
      )}
      {mut.data && (
        <article className="card rich-md mt-8 p-6 sm:p-8">
          <ReactMarkdown>{mut.data.report_markdown}</ReactMarkdown>
        </article>
      )}
    </div>
  );
}
