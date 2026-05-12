"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";
import type { ChatMsg } from "@/lib/chat-types";
import {
  createEmptySession,
  deriveSessionTitle,
  loadSessions,
  newId,
  saveSessions,
  type StoredChatSession,
} from "@/lib/chat-storage";
import { useAuth } from "@/contexts/auth";
import { apiDelete, apiGet, apiPostJson, apiPutJson } from "@/lib/api";

function sortByUpdated(a: StoredChatSession, b: StoredChatSession) {
  return b.updatedAt - a.updatedAt;
}

export type {
  ChatAssistantMsg,
  ChatMsg,
  ChatUserMsg,
  SourceItem,
} from "@/lib/chat-types";

type ChatSessionValue = {
  hydrated: boolean;
  messages: ChatMsg[];
  setMessages: Dispatch<SetStateAction<ChatMsg[]>>;
  sessions: StoredChatSession[];
  activeSessionId: string | null;
  newChat: () => void;
  selectSession: (id: string) => void;
  deleteSession: (id: string) => void;
};

const ChatSessionContext = createContext<ChatSessionValue | null>(null);

type ApiSession = {
  id: number;
  title: string;
  messages: ChatMsg[];
  created_at: string;
  updated_at: string;
};

export function ChatSessionProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [hydrated, setHydrated] = useState(false);
  const [sessions, setSessions] = useState<StoredChatSession[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const syncRef = useRef(false);

  // Load sessions: from API if authenticated, otherwise localStorage
  useEffect(() => {
    if (token) {
      apiGet<ApiSession[]>("/chat/sessions")
        .then((remote) => {
          const mapped: StoredChatSession[] = remote.map((r) => ({
            id: String(r.id),
            title: r.title,
            messages: r.messages || [],
            updatedAt: new Date(r.updated_at).getTime(),
          }));
          if (mapped.length === 0) {
            const fresh = createEmptySession();
            setSessions([fresh]);
            setActiveId(fresh.id);
          } else {
            const sorted = mapped.sort(sortByUpdated);
            setSessions(sorted);
            setActiveId(sorted[0].id);
          }
          syncRef.current = true;
          setHydrated(true);
        })
        .catch(() => {
          // Fallback to localStorage on network error
          _loadFromStorage();
        });
    } else {
      _loadFromStorage();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function _loadFromStorage() {
    const list = loadSessions();
    if (list.length === 0) {
      const fresh = createEmptySession();
      saveSessions([fresh]);
      setSessions([fresh]);
      setActiveId(fresh.id);
    } else {
      const sorted = [...list].sort(sortByUpdated);
      setSessions(sorted);
      setActiveId(sorted[0].id);
    }
    syncRef.current = false;
    setHydrated(true);
  }

  useEffect(() => {
    if (!hydrated || sessions.length === 0) return;
    if (!activeId || !sessions.some((s) => s.id === activeId)) {
      const sorted = [...sessions].sort(sortByUpdated);
      setActiveId(sorted[0].id);
    }
  }, [hydrated, sessions, activeId]);

  const messages = useMemo(() => {
    const s = sessions.find((x) => x.id === activeId);
    return s?.messages ?? [];
  }, [sessions, activeId]);

  const setMessages = useCallback(
    (updater: SetStateAction<ChatMsg[]>) => {
      if (!activeId) return;
      setSessions((prev) => {
        const idx = prev.findIndex((s) => s.id === activeId);
        if (idx === -1) return prev;
        const cur = prev[idx];
        const newMsgs =
          typeof updater === "function" ? updater(cur.messages) : updater;
        const updated: StoredChatSession = {
          ...cur,
          messages: newMsgs,
          updatedAt: Date.now(),
          title: deriveSessionTitle(newMsgs),
        };
        const others = prev.filter((s) => s.id !== activeId);
        const next = [updated, ...others].sort(sortByUpdated);

        // Persist
        if (token && syncRef.current) {
          apiPutJson(`/chat/sessions/${activeId}`, {
            title: updated.title,
            messages: updated.messages,
          }).catch(() => {});
        } else {
          saveSessions(next);
        }
        return next;
      });
    },
    [activeId, token],
  );

  const newChat = useCallback(() => {
    if (token && syncRef.current) {
      apiPostJson<ApiSession>("/chat/sessions", {
        title: "New conversation",
        messages: [],
      })
        .then((created) => {
          const fresh: StoredChatSession = {
            id: String(created.id),
            title: created.title,
            messages: [],
            updatedAt: new Date(created.updated_at).getTime(),
          };
          setSessions((prev) => {
            const trimmed = prev.filter((s) => s.messages.length > 0);
            return [fresh, ...trimmed].sort(sortByUpdated);
          });
          setActiveId(fresh.id);
        })
        .catch(() => {});
    } else {
      const id = newId();
      setSessions((prev) => {
        const trimmed = prev.filter((s) => s.messages.length > 0);
        const fresh: StoredChatSession = {
          id,
          title: "New conversation",
          messages: [],
          updatedAt: Date.now(),
        };
        const next = [fresh, ...trimmed].sort(sortByUpdated);
        saveSessions(next);
        return next;
      });
      setActiveId(id);
    }
  }, [token]);

  const selectSession = useCallback((id: string) => {
    setActiveId(id);
  }, []);

  const deleteSession = useCallback(
    (id: string) => {
      if (token && syncRef.current) {
        apiDelete(`/chat/sessions/${id}`).catch(() => {});
      }
      setSessions((prev) => {
        let next = prev.filter((s) => s.id !== id);
        if (next.length === 0) {
          next = [createEmptySession()];
        }
        const sorted = [...next].sort(sortByUpdated);
        if (!token) saveSessions(sorted);
        return sorted;
      });
      setActiveId((cur) => (cur === id ? null : cur));
    },
    [token],
  );

  const value = useMemo(
    () => ({
      hydrated,
      messages,
      setMessages,
      sessions,
      activeSessionId: activeId,
      newChat,
      selectSession,
      deleteSession,
    }),
    [
      hydrated,
      messages,
      setMessages,
      sessions,
      activeId,
      newChat,
      selectSession,
      deleteSession,
    ],
  );

  return (
    <ChatSessionContext.Provider value={value}>
      {children}
    </ChatSessionContext.Provider>
  );
}

export function useChatSession() {
  const ctx = useContext(ChatSessionContext);
  if (!ctx) {
    throw new Error("useChatSession must be used within ChatSessionProvider");
  }
  return ctx;
}
