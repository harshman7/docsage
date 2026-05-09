"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Copy,
  FileSearch,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { useCallback, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { apiGet, apiPost, getApiOrigin } from "@/lib/api";

type DocumentDetail = {
  id: number;
  filename: string;
  file_path: string;
  document_type: string;
  raw_text: string | null;
  extracted_data: Record<string, unknown>;
  created_at: string;
};

type ExtractionDebug = {
  document_id: number;
  filename: string;
  document_type: string;
  file_path: string | null;
  raw_text_length: number;
  raw_text_preview: string;
  file_exists: boolean;
  synthetic_source: boolean;
  preview_available: boolean;
  preview_note: string | null;
  confidence: Record<string, number>;
  heuristics_from_raw_text: {
    amounts: number[];
    dates: string[];
    vendor_guess: string | null;
  };
  stored_extracted_data: Record<string, unknown>;
};

export default function DocumentDebugPage() {
  const params = useParams();
  const idParam = params?.id;
  const docId =
    typeof idParam === "string"
      ? Number(idParam)
      : Array.isArray(idParam)
        ? Number(idParam[0])
        : NaN;

  const qc = useQueryClient();
  const [previewBust, setPreviewBust] = useState(0);
  const [previewFailed, setPreviewFailed] = useState(false);

  const { data: detail, isFetching: loadingDetail } = useQuery({
    queryKey: ["document-detail", docId],
    queryFn: () => apiGet<DocumentDetail>(`/documents/${docId}/detail`),
    enabled: Number.isFinite(docId) && docId > 0,
  });

  const { data: dbg, isFetching: loadingDbg } = useQuery({
    queryKey: ["document-extraction-debug", docId],
    queryFn: () => apiGet<ExtractionDebug>(`/documents/${docId}/extraction-debug`),
    enabled: Number.isFinite(docId) && docId > 0,
  });

  const reparse = useMutation({
    mutationFn: (replaceTx: boolean) =>
      apiPost<{
        ok: boolean;
        document_type: string;
        transactions_inserted: number | null;
      }>(
        `/documents/${docId}/reparse?replace_transactions=${replaceTx ? "true" : "false"}`,
      ),
    onSuccess: () => {
      setPreviewBust(Date.now());
      setPreviewFailed(false);
      qc.invalidateQueries({ queryKey: ["document-detail", docId] });
      qc.invalidateQueries({ queryKey: ["document-extraction-debug", docId] });
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["summary"] });
      qc.invalidateQueries({ queryKey: ["time-series"] });
      qc.invalidateQueries({ queryKey: ["category-breakdown"] });
      qc.invalidateQueries({ queryKey: ["anomalies"] });
    },
  });

  const copyRaw = useCallback(async () => {
    const t = detail?.raw_text ?? "";
    if (!t) return;
    await navigator.clipboard.writeText(t);
  }, [detail?.raw_text]);

  if (!Number.isFinite(docId) || docId <= 0) {
    return (
      <div>
        <PageHeader title="Document" description="Invalid document id." />
        <Link href="/documents" className="text-sm text-teal-600 hover:underline">
          Back to documents
        </Link>
      </div>
    );
  }

  const previewSrc =
    dbg?.preview_available && !dbg.synthetic_source
      ? `${getApiOrigin()}/api/v1/documents/${docId}/preview${previewBust ? `?t=${previewBust}` : ""}`
      : null;

  const canReparse =
    dbg &&
    !dbg.synthetic_source &&
    dbg.file_exists &&
    !reparse.isPending;

  return (
    <div>
      <Link
        href="/documents"
        className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-teal-600 dark:text-neutral-400 dark:hover:text-teal-400"
      >
        <ArrowLeft className="h-4 w-4" />
        Documents
      </Link>

      <PageHeader
        title={detail?.filename ?? `Document #${docId}`}
        description="Inspect OCR/raw text, structured extraction, heuristics, and annotated preview."
      />

      {(loadingDetail || loadingDbg) && (
        <div className="mb-6 flex items-center gap-2 text-sm text-slate-500 dark:text-neutral-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </div>
      )}

      <div className="mb-8 flex flex-wrap items-center gap-3">
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50 disabled:opacity-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-white dark:hover:bg-neutral-800"
          disabled={!canReparse}
          onClick={() => {
            if (
              !window.confirm(
                "Re-run extraction from the saved file on disk? This updates raw text and extracted fields, and replaces all transactions tied to this document (avoids duplicate totals while you tune the pipeline).",
              )
            ) {
              return;
            }
            reparse.mutate(true);
          }}
        >
          <RefreshCw
            className={`h-4 w-4 ${reparse.isPending ? "animate-spin" : ""}`}
          />
          Re-parse from file
        </button>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 disabled:opacity-50 dark:border-neutral-600 dark:text-neutral-300 dark:hover:bg-neutral-800"
          disabled={!canReparse || reparse.isPending}
          onClick={() => {
            if (
              !window.confirm(
                "Re-parse only the document fields (raw text + extracted_data) and keep existing transactions? Use this if you are editing structure but not amounts.",
              )
            ) {
              return;
            }
            reparse.mutate(false);
          }}
        >
          Re-parse (keep transactions)
        </button>
        {!dbg?.synthetic_source && !dbg?.file_exists && (
          <span className="text-xs text-amber-700 dark:text-amber-300">
            Re-parse needs a file on disk.
          </span>
        )}
        {dbg?.synthetic_source && (
          <span className="text-xs text-slate-500 dark:text-neutral-400">
            Synthetic row — re-parse disabled.
          </span>
        )}
        {reparse.isError && (
          <span className="text-xs text-red-600 dark:text-red-400">
            {(reparse.error as Error).message}
          </span>
        )}
        {reparse.isSuccess && (
          <span className="text-xs text-emerald-700 dark:text-emerald-400">
            Updated
            {reparse.data.transactions_inserted != null
              ? ` · ${reparse.data.transactions_inserted} transaction(s) inserted`
              : " · transactions unchanged"}
            .
          </span>
        )}
      </div>

      <section className="card mb-8 p-5 sm:p-6">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
          <FileSearch className="h-4 w-4 text-teal-600 dark:text-teal-400" />
          Summary
        </div>
        {dbg && (
          <dl className="grid gap-2 text-sm text-slate-600 dark:text-neutral-300 sm:grid-cols-2">
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400 dark:text-neutral-500">
                Type
              </dt>
              <dd className="font-medium">{dbg.document_type}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase tracking-wide text-slate-400 dark:text-neutral-500">
                Raw text length
              </dt>
              <dd className="font-medium tabular-nums">{dbg.raw_text_length}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-xs uppercase tracking-wide text-slate-400 dark:text-neutral-500">
                Confidence (heuristic)
              </dt>
              <dd className="mt-1 max-h-32 overflow-auto rounded bg-slate-100/80 p-2 font-mono text-[11px] leading-relaxed dark:bg-neutral-900/80">
                {Object.keys(dbg.confidence).length
                  ? JSON.stringify(dbg.confidence, null, 2)
                  : "—"}
              </dd>
            </div>
          </dl>
        )}
      </section>

      <section className="card mb-8 p-5 sm:p-6">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
            Raw text
          </h2>
          <button
            type="button"
            onClick={() => void copyRaw()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-neutral-600 dark:text-neutral-200 dark:hover:bg-neutral-800"
          >
            <Copy className="h-3.5 w-3.5" />
            Copy all
          </button>
        </div>
        <pre className="max-h-96 overflow-auto rounded-lg border border-slate-100 bg-slate-50/90 p-4 text-xs text-slate-800 dark:border-neutral-800 dark:bg-[#0a0a0a] dark:text-neutral-200">
          {detail?.raw_text?.length ? detail.raw_text : "—"}
        </pre>
      </section>

      <section className="card mb-8 p-5 sm:p-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">
          Stored extracted_data
        </h2>
        <pre className="max-h-96 overflow-auto rounded-lg border border-slate-100 bg-slate-50/90 p-4 text-xs text-slate-800 dark:border-neutral-800 dark:bg-[#0a0a0a] dark:text-neutral-200">
          {detail?.extracted_data
            ? JSON.stringify(detail.extracted_data, null, 2)
            : "—"}
        </pre>
      </section>

      {dbg && (
        <section className="card mb-8 p-5 sm:p-6">
          <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">
            Heuristics from raw text (debug)
          </h2>
          <p className="mb-3 text-xs text-slate-500 dark:text-neutral-500">
            Regex / lightweight parsers run on the same raw text for comparison with stored
            fields.
          </p>
          <pre className="max-h-72 overflow-auto rounded-lg border border-slate-100 bg-slate-50/90 p-4 text-xs text-slate-800 dark:border-neutral-800 dark:bg-[#0a0a0a] dark:text-neutral-200">
            {JSON.stringify(dbg.heuristics_from_raw_text, null, 2)}
          </pre>
          {dbg.preview_note && (
            <p className="mt-3 text-xs text-slate-600 dark:text-neutral-400">
              {dbg.preview_note}
            </p>
          )}
        </section>
      )}

      <section className="card mb-8 p-5 sm:p-6">
        <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-white">
          Annotated preview
        </h2>
        {previewSrc && !previewFailed ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewSrc}
            alt="Annotated extraction preview"
            className="max-h-[480px] w-auto max-w-full rounded-lg border border-slate-200 dark:border-neutral-700"
            onError={() => setPreviewFailed(true)}
          />
        ) : (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50/80 p-8 text-center text-sm text-slate-600 dark:border-neutral-700 dark:bg-[#080808] dark:text-neutral-400">
            {previewFailed
              ? "Preview failed to load (PDF or unsupported format is common)."
              : dbg?.preview_note ?? "No preview available."}
          </div>
        )}
      </section>
    </div>
  );
}
