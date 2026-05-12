import type { ChatMsg } from "./chat-types";

export type StoredChatSession = {
  id: string;
  title: string;
  messages: ChatMsg[];
  updatedAt: number;
};

const STORAGE_KEY = "docsage-chat-sessions-v1";
const MAX_SESSIONS = 30;

function newId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `s-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export { newId };

export function deriveSessionTitle(messages: ChatMsg[]): string {
  const first = messages.find(
    (m): m is Extract<ChatMsg, { role: "user" }> => m.role === "user",
  );
  if (!first?.text?.trim()) return "New conversation";
  const t = first.text.trim().replace(/\s+/g, " ");
  return t.length > 56 ? `${t.slice(0, 54)}…` : t;
}

function isStoredSession(x: unknown): x is StoredChatSession {
  if (!x || typeof x !== "object") return false;
  const s = x as StoredChatSession;
  return (
    typeof s.id === "string" &&
    Array.isArray(s.messages) &&
    typeof s.updatedAt === "number"
  );
}

export function loadSessions(): StoredChatSession[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    const list = parsed.filter(isStoredSession).map((s) => ({
      ...s,
      title:
        typeof s.title === "string" ? s.title : deriveSessionTitle(s.messages),
    }));
    return list.sort((a, b) => b.updatedAt - a.updatedAt);
  } catch {
    return [];
  }
}

export function saveSessions(sessions: StoredChatSession[]): void {
  if (typeof window === "undefined") return;
  const sorted = [...sessions].sort((a, b) => b.updatedAt - a.updatedAt);
  const trimmed = sorted.slice(0, MAX_SESSIONS);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

export function createEmptySession(): StoredChatSession {
  return {
    id: newId(),
    title: "New conversation",
    messages: [],
    updatedAt: Date.now(),
  };
}
