/**
 * Normalize FastAPI error bodies for display (detail: string | object | array).
 */
export function formatApiErrorDetail(detail: unknown): string {
  if (detail == null) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((entry) => {
        if (entry && typeof entry === "object" && "msg" in entry) {
          const loc = "loc" in entry && Array.isArray((entry as { loc?: unknown }).loc)
            ? String((entry as { loc: unknown[] }).loc.join("."))
            : "";
          const msg = String((entry as { msg?: unknown }).msg ?? "");
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(entry);
      })
      .filter(Boolean)
      .join("; ");
  }
  if (typeof detail === "object" && detail !== null) {
    return JSON.stringify(detail);
  }
  return String(detail);
}

export async function readApiErrorMessage(res: Response, fallback: string): Promise<string> {
  const text = await res.text();
  if (!text) return fallback;
  try {
    const body = JSON.parse(text) as { detail?: unknown };
    if (body.detail !== undefined) {
      return formatApiErrorDetail(body.detail);
    }
  } catch {
    return text.slice(0, 200);
  }
  return fallback;
}

/** User-facing message when fetch() rejects (offline, CORS, wrong URL, etc.). */
export function networkErrorMessage(err: unknown): string {
  if (err instanceof TypeError) {
    return (
      "Cannot reach the API. Check that the backend is running and " +
      "NEXT_PUBLIC_API_URL matches the server (e.g. http://127.0.0.1:8000)."
    );
  }
  if (err instanceof Error && err.message) {
    const m = err.message.toLowerCase();
    if (m.includes("failed to fetch") || m.includes("load failed") || m.includes("network")) {
      return (
        "Cannot reach the API. Check that the backend is running and " +
        "NEXT_PUBLIC_API_URL matches the server (e.g. http://127.0.0.1:8000)."
      );
    }
    return err.message;
  }
  return "Something went wrong. Try again.";
}
