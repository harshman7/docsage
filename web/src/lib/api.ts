const base = (): string =>
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiPostJson<T>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiPatchJson<T>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiUploadExcel(): Promise<Blob> {
  const res = await fetch(`${base()}/api/v1/exports/excel`);
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

export async function apiUploadDocument(path: string, file: File): Promise<unknown> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "POST",
    body: fd,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
