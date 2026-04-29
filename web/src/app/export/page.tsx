"use client";

import { useState } from "react";
import { Download, FileSpreadsheet, FileText } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { apiUploadExcel } from "@/lib/api";

export default function ExportPage() {
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function downloadExcel() {
    setErr(null);
    setLoading(true);
    try {
      const blob = await apiUploadExcel();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "docsage_export.xlsx";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function downloadSummary() {
    setErr(null);
    setLoading(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${base}/api/v1/exports/summary`);
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "summary_report.md";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <PageHeader
        title="Export"
        description="Pull a spreadsheet or markdown summary from the API for offline analysis."
      />
      <div className="card divide-y divide-slate-100 p-0 dark:divide-slate-600">
        <button
          type="button"
          className="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-slate-50 disabled:opacity-45 dark:hover:bg-slate-700/40"
          disabled={loading}
          onClick={downloadExcel}
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-100 text-teal-700 dark:bg-teal-950 dark:text-teal-400">
            <FileSpreadsheet className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <div className="font-medium text-slate-900 dark:text-white">
              Excel workbook
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-300">
              .xlsx export
            </div>
          </div>
          <Download className="h-4 w-4 text-slate-400" />
        </button>
        <button
          type="button"
          className="flex w-full items-center gap-4 px-5 py-4 text-left transition hover:bg-slate-50 disabled:opacity-45 dark:hover:bg-slate-700/40"
          disabled={loading}
          onClick={downloadSummary}
        >
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
            <FileText className="h-5 w-5" />
          </div>
          <div className="flex-1">
            <div className="font-medium text-slate-900 dark:text-white">
              Summary report
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-300">
              Markdown (.md)
            </div>
          </div>
          <Download className="h-4 w-4 text-slate-400" />
        </button>
      </div>
      {err && (
        <p className="mt-4 text-sm text-red-600 dark:text-red-400">{err}</p>
      )}
    </div>
  );
}
