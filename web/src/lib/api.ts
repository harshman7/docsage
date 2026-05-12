const TOKEN_KEY = "docsage_access_token";

const base = (): string =>
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

/** Public API origin (same as fetch base) — for `<img src>` preview URLs. */
export function getApiOrigin(): string {
  return base();
}

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    cache: "no-store",
    headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "POST",
    headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiPostJson<T>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiPutJson<T>(
  path: string,
  body: unknown
): Promise<T> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
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
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export async function apiDelete(path: string): Promise<void> {
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "DELETE",
    headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await res.text());
}

export async function apiUploadExcel(): Promise<Blob> {
  const res = await fetch(`${base()}/api/v1/exports/excel`, {
    headers: { ...authHeaders() },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}

export async function apiUploadDocument(path: string, file: File): Promise<unknown> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${base()}/api/v1${path}`, {
    method: "POST",
    headers: { ...authHeaders() },
    body: fd,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
