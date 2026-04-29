"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileUp, File } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { apiGet, apiUploadDocument } from "@/lib/api";

type Doc = {
  id: number;
  filename: string;
  file_path: string;
  document_type: string;
  created_at: string;
};

export default function DocumentsPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["documents"],
    queryFn: () => apiGet<Doc[]>("/documents"),
  });
  const upload = useMutation({
    mutationFn: (file: File) => apiUploadDocument("/documents", file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });

  return (
    <div>
      <PageHeader
        title="Documents"
        description="Upload PDFs and images for parsing. Supported: PDF, PNG, JPEG."
      />
      <div className="card border-2 border-dashed border-slate-200/90 bg-gradient-to-b from-white to-slate-50/80 p-8 transition hover:border-teal-300/60 dark:border-neutral-700 dark:from-neutral-950 dark:to-[#0a0a0a] dark:hover:border-teal-600/45">
        <label className="flex cursor-pointer flex-col items-center text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-100 text-teal-700 dark:bg-teal-950/55 dark:text-teal-400 dark:ring-1 dark:ring-teal-600/25">
            <FileUp className="h-7 w-7" strokeWidth={1.75} />
          </div>
          <span className="text-sm font-semibold text-slate-900 dark:text-white">
            Drop files or click to upload
          </span>
          <span className="mt-1 text-xs text-slate-500 dark:text-neutral-400">
            PDF, PNG, JPG — max size depends on API limits
          </span>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            disabled={upload.isPending}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload.mutate(f);
              e.target.value = "";
            }}
            className="sr-only"
          />
        </label>
        {upload.isPending && (
          <p className="mt-4 text-center text-sm text-teal-600 dark:text-teal-400">
            Uploading…
          </p>
        )}
        {upload.isError && (
          <p className="mt-4 text-center text-sm text-red-600 dark:text-red-400">
            {(upload.error as Error).message}
          </p>
        )}
      </div>
      <ul className="card mt-8 divide-y divide-slate-100 p-0 dark:divide-neutral-800">
        {data?.length ? (
          data.map((d) => (
            <li
              key={d.id}
              className="flex items-center justify-between gap-4 px-4 py-4 transition hover:bg-slate-50/80 dark:hover:bg-neutral-900 sm:px-5"
            >
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-600 dark:bg-neutral-800 dark:text-neutral-200">
                  <File className="h-5 w-5" />
                </div>
                <span className="truncate font-medium text-slate-900 dark:text-white">
                  {d.filename}
                </span>
              </div>
              <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-neutral-800 dark:text-neutral-300">
                {d.document_type}
              </span>
            </li>
          ))
        ) : (
          <li className="px-4 py-12 text-center text-sm text-slate-500 dark:text-neutral-400">
            No documents yet. Upload above to get started.
          </li>
        )}
      </ul>
    </div>
  );
}
