"use client";

import { useState } from "react";
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
    <div className="space-y-6 max-w-md">
      <h1 className="text-2xl font-semibold">Export</h1>
      <p className="text-sm text-zinc-600">
        Download Excel workbook or markdown summary from the API.
      </p>
      <div className="flex flex-col gap-3">
        <button
          type="button"
          className="rounded-md bg-zinc-900 text-white px-4 py-2 text-sm disabled:opacity-50"
          disabled={loading}
          onClick={downloadExcel}
        >
          Download Excel
        </button>
        <button
          type="button"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm disabled:opacity-50"
          disabled={loading}
          onClick={downloadSummary}
        >
          Download summary (.md)
        </button>
      </div>
      {err && <p className="text-red-600 text-sm">{err}</p>}
    </div>
  );
}
