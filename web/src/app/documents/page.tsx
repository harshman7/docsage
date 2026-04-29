"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Documents</h1>
      <div className="rounded-xl border border-dashed border-zinc-300 bg-white p-6">
        <label className="block text-sm font-medium mb-2">Upload PDF / image</label>
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          disabled={upload.isPending}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) upload.mutate(f);
            e.target.value = "";
          }}
          className="text-sm"
        />
        {upload.isError && (
          <p className="text-red-600 text-sm mt-2">{(upload.error as Error).message}</p>
        )}
      </div>
      <ul className="divide-y divide-zinc-200 rounded-xl border border-zinc-200 bg-white">
        {data?.length ? (
          data.map((d) => (
            <li key={d.id} className="px-4 py-3 text-sm flex justify-between gap-4">
              <span className="font-medium">{d.filename}</span>
              <span className="text-zinc-500">{d.document_type}</span>
            </li>
          ))
        ) : (
          <li className="px-4 py-6 text-zinc-500 text-sm text-center">
            No documents yet.
          </li>
        )}
      </ul>
    </div>
  );
}
