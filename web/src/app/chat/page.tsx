"use client";

import { useMutation } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import {
  Loader2,
  MessageSquare,
  RotateCcw,
  Send,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useCallback, useEffect, useRef, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { useChatSession, type ChatMsg, type SourceItem } from "@/contexts/chat-session";
import { apiPostJson } from "@/lib/api";

type ChatResp = {
  answer: string;
  sources?: SourceItem[];
  sql_query?: string | null;
  steps?: unknown[];
  tool_calls?: unknown[];
};

const MAX_HISTORY = 20;

const SUGGESTED_PROMPTS = [
  "What did I spend on rent last quarter?",
  "Summarize my latest invoices.",
  "Top vendors by total spend this month?",
  "Any anomalies in recent transactions?",
] as const;

function formatSessionTime(ts: number): string {
  const d = new Date(ts);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString(undefined, {
      hour: "numeric",
      minute: "2-digit",
    });
  }
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

const easeApple = [0.25, 0.1, 0.25, 1] as const;

function formatSource(s: SourceItem): string {
  const parts: string[] = [];
  if (s.filename) parts.push(s.filename);
  if (s.document_id != null) parts.push(`id ${s.document_id}`);
  if (s.chunk_type) parts.push(s.chunk_type);
  if (typeof s.score === "number") parts.push(`score ${s.score.toFixed(3)}`);
  return parts.length ? parts.join(" · ") : JSON.stringify(s);
}

function AssistantMeta({
  sources,
  sql_query,
  steps,
  tool_calls,
}: {
  sources?: SourceItem[];
  sql_query?: string | null;
  steps?: unknown[];
  tool_calls?: unknown[];
}) {
  const hasSources = sources && sources.length > 0;
  const hasSql = Boolean(sql_query?.trim());
  const hasSteps = steps && steps.length > 0;
  const hasTools = tool_calls && tool_calls.length > 0;

  if (!hasSources && !hasSql && !hasSteps && !hasTools) return null;

  return (
    <div className="mt-3 space-y-1 border-t border-slate-200/90 pt-3 dark:border-neutral-700/80">
      {hasSources && (
        <details className="group rounded-lg bg-white/60 text-xs dark:bg-neutral-900/40">
          <summary className="cursor-pointer list-none px-2 py-1.5 font-medium text-slate-600 marker:content-none dark:text-neutral-400 [&::-webkit-details-marker]:hidden">
            <span className="underline decoration-slate-300 underline-offset-2 group-open:text-teal-700 dark:decoration-neutral-600 dark:group-open:text-teal-400">
              Sources ({sources!.length})
            </span>
          </summary>
          <ul className="max-h-40 space-y-1 overflow-y-auto px-2 pb-2 pl-4 text-slate-600 dark:text-neutral-400">
            {sources!.map((s, i) => (
              <li key={i} className="leading-snug">
                {formatSource(s)}
              </li>
            ))}
          </ul>
        </details>
      )}
      {hasSql && (
        <details className="group rounded-lg bg-white/60 text-xs dark:bg-neutral-900/40">
          <summary className="cursor-pointer list-none px-2 py-1.5 font-medium text-slate-600 marker:content-none dark:text-neutral-400 [&::-webkit-details-marker]:hidden">
            <span className="underline decoration-slate-300 underline-offset-2 group-open:text-teal-700 dark:decoration-neutral-600 dark:group-open:text-teal-400">
              SQL query
            </span>
          </summary>
          <pre className="max-h-48 overflow-x-auto overflow-y-auto px-2 pb-2 font-mono-ui text-[11px] leading-relaxed text-slate-700 dark:text-neutral-300">
            {sql_query}
          </pre>
        </details>
      )}
      {hasSteps && (
        <details className="group rounded-lg bg-white/60 text-xs dark:bg-neutral-900/40">
          <summary className="cursor-pointer list-none px-2 py-1.5 font-medium text-slate-600 marker:content-none dark:text-neutral-400 [&::-webkit-details-marker]:hidden">
            <span className="underline decoration-slate-300 underline-offset-2 group-open:text-teal-700 dark:decoration-neutral-600 dark:group-open:text-teal-400">
              Steps ({steps!.length})
            </span>
          </summary>
          <pre className="max-h-48 overflow-auto px-2 pb-2 font-mono-ui text-[11px] text-slate-600 dark:text-neutral-400">
            {JSON.stringify(steps, null, 2)}
          </pre>
        </details>
      )}
      {hasTools && (
        <details className="group rounded-lg bg-white/60 text-xs dark:bg-neutral-900/40">
          <summary className="cursor-pointer list-none px-2 py-1.5 font-medium text-slate-600 marker:content-none dark:text-neutral-400 [&::-webkit-details-marker]:hidden">
            <span className="underline decoration-slate-300 underline-offset-2 group-open:text-teal-700 dark:decoration-neutral-600 dark:group-open:text-teal-400">
              Tool calls ({tool_calls!.length})
            </span>
          </summary>
          <pre className="max-h-40 overflow-auto px-2 pb-2 font-mono-ui text-[11px] text-slate-600 dark:text-neutral-400">
            {JSON.stringify(tool_calls, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function MessageBubble({
  msg,
  reduceMotion,
}: {
  msg: ChatMsg;
  reduceMotion: boolean;
}) {
  const isUser = msg.role === "user";

  const inner = (
    <div
      className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      <div
        className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl shadow-sm ring-1 ring-black/5 dark:ring-white/10 ${
          isUser
            ? "bg-teal-600 text-white dark:bg-teal-600"
            : "border border-slate-200 bg-white text-teal-600 dark:border-neutral-700 dark:bg-[#111] dark:text-teal-400"
        }`}
        aria-hidden
      >
        {isUser ? (
          <MessageSquare className="h-4 w-4" strokeWidth={2} />
        ) : (
          <Sparkles className="h-4 w-4" strokeWidth={2} />
        )}
      </div>
      <div className="min-w-0 max-w-[min(100%,32rem)]">
        <div
          className={`rounded-2xl px-4 py-3 text-sm shadow-md ring-1 ring-black/[0.04] dark:ring-white/[0.06] ${
            isUser
              ? "bg-gradient-to-br from-teal-600 to-teal-700 text-white dark:from-teal-600 dark:to-teal-800"
              : "border border-slate-200/90 bg-slate-50/95 text-slate-800 backdrop-blur-sm dark:border-neutral-700 dark:bg-[#0c0c0c]/95 dark:text-neutral-100"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
          ) : (
            <>
              <div className="rich-md text-sm">
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
              <AssistantMeta
                sources={msg.sources}
                sql_query={msg.sql_query}
                steps={msg.steps}
                tool_calls={msg.tool_calls}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );

  if (reduceMotion) {
    return <div>{inner}</div>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: easeApple }}
    >
      {inner}
    </motion.div>
  );
}

export default function ChatPage() {
  const {
    hydrated,
    messages: msgs,
    setMessages: setMsgs,
    sessions,
    activeSessionId,
    newChat,
    selectSession,
    deleteSession,
  } = useChatSession();
  const [q, setQ] = useState("");
  const [errorDismissed, setErrorDismissed] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();

  const mut = useMutation({
    mutationFn: (payload: {
      query: string;
      history: { role: string; content: string }[];
    }) =>
      apiPostJson<ChatResp>("/chat/insights", {
        query: payload.query,
        use_rag: true,
        use_sql: true,
        history:
          payload.history.length > 0 ? payload.history : undefined,
      }),
    onSuccess: (data) =>
      setMsgs((m) => [
        ...m,
        {
          role: "assistant",
          text: data.answer,
          sources: data.sources,
          sql_query: data.sql_query,
          steps: data.steps,
          tool_calls: data.tool_calls,
        },
      ]),
    onMutate: () => {
      setErrorDismissed(false);
    },
  });

  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [msgs, mut.isPending, mut.isError, scrollToBottom]);

  const historyFromMsgs = (messages: ChatMsg[]) =>
    messages
      .slice(-MAX_HISTORY)
      .map((m) => ({ role: m.role, content: m.text }));

  const submitQuery = (query: string) => {
    const trimmed = query.trim();
    if (!trimmed || mut.isPending) return;
    const history = historyFromMsgs(msgs);
    setMsgs((m) => [...m, { role: "user", text: trimmed }]);
    setQ("");
    mut.mutate({ query: trimmed, history });
  };

  const clearChat = () => {
    newChat();
    mut.reset();
    setErrorDismissed(false);
    setQ("");
  };

  const showError = mut.isError && !errorDismissed;

  if (!hydrated) {
    return (
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4">
        <PageHeader
          title="Chat"
          description="Loading your saved conversations…"
        />
        <div className="h-96 animate-pulse rounded-2xl bg-slate-200/60 dark:bg-neutral-800/60" />
      </div>
    );
  }

  const sessionList = (
    <div className="space-y-1">
      <p className="mb-2 px-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-neutral-500">
        Previous chats
      </p>
      <ul className="max-h-[min(24rem,calc(100dvh-12rem))] space-y-1 overflow-y-auto overscroll-contain pr-0.5">
        {sessions.map((s) => {
          const active = s.id === activeSessionId;
          return (
            <li key={s.id} className="group relative">
              <button
                type="button"
                onClick={() => {
                  selectSession(s.id);
                  mut.reset();
                  setErrorDismissed(false);
                }}
                className={`flex w-full items-start gap-2 rounded-xl border px-3 py-2.5 text-left text-sm transition ${
                  active
                    ? "border-teal-500/50 bg-teal-50/90 text-slate-900 shadow-sm dark:border-teal-500/35 dark:bg-teal-950/40 dark:text-white"
                    : "border-transparent bg-white/50 text-slate-700 hover:border-slate-200 hover:bg-white dark:bg-neutral-900/30 dark:text-neutral-200 dark:hover:border-neutral-700 dark:hover:bg-neutral-900/70"
                }`}
              >
                <MessageSquare
                  className={`mt-0.5 h-4 w-4 shrink-0 ${active ? "text-teal-600 dark:text-teal-400" : "text-slate-400 dark:text-neutral-500"}`}
                  aria-hidden
                />
                <span className="min-w-0 flex-1">
                  <span className="line-clamp-2 font-medium leading-snug">{s.title}</span>
                  <span className="mt-0.5 block text-[11px] text-slate-500 dark:text-neutral-500">
                    {formatSessionTime(s.updatedAt)}
                    {s.messages.length > 0
                      ? ` · ${s.messages.length} messages`
                      : ""}
                  </span>
                </span>
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSession(s.id);
                  mut.reset();
                  setErrorDismissed(false);
                }}
                className="absolute right-1.5 top-1.5 rounded-lg p-1.5 text-slate-400 opacity-0 transition hover:bg-red-100 hover:text-red-600 group-hover:opacity-100 dark:hover:bg-red-950/60 dark:hover:text-red-400"
                aria-label="Delete conversation"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 min-h-[calc(100dvh-6rem)] md:min-h-[calc(100dvh-4.5rem)] lg:flex-row lg:items-stretch lg:gap-6">
      <aside className="hidden w-72 shrink-0 lg:block">{sessionList}</aside>

      <div className="min-w-0 flex flex-1 flex-col lg:min-h-0">
        <div className="mb-4 flex shrink-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <PageHeader
            title="Chat"
            description="Conversations are saved in this browser. Switch threads in the sidebar or chips; answers use RAG and SQL when available."
          />
          <button
            type="button"
            onClick={clearChat}
            className="inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm font-medium text-slate-700 shadow-sm backdrop-blur-sm transition hover:bg-slate-50 hover:text-slate-900 dark:border-neutral-700 dark:bg-neutral-900/80 dark:text-neutral-200 dark:hover:bg-neutral-800 dark:hover:text-white"
          >
            <RotateCcw className="h-4 w-4" aria-hidden />
            New chat
          </button>
        </div>

        <div className="lg:hidden">
          <div className="mb-3 flex gap-2 overflow-x-auto pb-1">{sessions.map((s) => {
            const active = s.id === activeSessionId;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => {
                  selectSession(s.id);
                  mut.reset();
                  setErrorDismissed(false);
                }}
                className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                  active
                    ? "border-teal-500 bg-teal-50 text-teal-900 dark:border-teal-500/50 dark:bg-teal-950/50 dark:text-teal-100"
                    : "border-slate-200 bg-white/80 text-slate-700 dark:border-neutral-700 dark:bg-neutral-900/80 dark:text-neutral-300"
                }`}
              >
                <span className="max-w-[10rem] truncate">{s.title}</span>
              </button>
            );
          })}</div>
        </div>

      <div className="flex min-h-[min(28rem,calc(100dvh-14rem))] flex-1 flex-col overflow-hidden rounded-2xl border border-slate-200/90 bg-white/40 shadow-[0_24px_48px_-24px_rgba(15,23,42,0.25)] backdrop-blur-xl dark:border-neutral-800 dark:bg-[#050505]/50 dark:shadow-[0_24px_56px_-24px_rgba(0,0,0,0.65)] lg:min-h-[min(32rem,calc(100dvh-11rem))]">
        <div
          ref={scrollRef}
          className="min-h-0 flex-1 space-y-6 overflow-y-auto overscroll-y-contain px-4 py-5 sm:px-6 sm:py-6"
        >
          {msgs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center sm:py-14">
              <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500/90 to-teal-700 text-white shadow-lg shadow-teal-900/20 dark:from-teal-600 dark:to-teal-900 dark:shadow-teal-950/40">
                <Sparkles className="h-8 w-8" strokeWidth={1.75} />
              </div>
              <p className="mb-5 max-w-md text-sm text-slate-600 dark:text-neutral-400">
                Start with a question about your uploads and transactions, or try
                one of the suggestions below.
              </p>
              <div className="flex max-w-lg flex-wrap justify-center gap-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => submitQuery(prompt)}
                    disabled={mut.isPending}
                    className="rounded-full border border-slate-200/90 bg-white/90 px-3.5 py-1.5 text-left text-xs font-medium text-slate-700 shadow-sm transition hover:border-teal-300 hover:text-teal-800 dark:border-neutral-700 dark:bg-neutral-900/90 dark:text-neutral-200 dark:hover:border-teal-600/60 dark:hover:text-teal-200"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {msgs.map((m, i) => (
            <MessageBubble key={`${i}-${m.role}`} msg={m} reduceMotion={!!reduceMotion} />
          ))}

          {mut.isPending && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50/95 px-4 py-3 text-sm text-slate-500 shadow-sm dark:border-neutral-700 dark:bg-neutral-900/80 dark:text-neutral-400">
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-teal-600 dark:text-teal-400" />
                <span>Thinking…</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {showError && (
        <div className="mt-3 flex shrink-0 items-start gap-2 rounded-xl border border-red-200 bg-red-50/95 px-3 py-2.5 text-sm text-red-800 shadow-sm dark:border-red-900/40 dark:bg-red-950/50 dark:text-red-200">
          <span className="flex-1">{(mut.error as Error).message}</span>
          <button
            type="button"
            onClick={() => setErrorDismissed(true)}
            className="rounded-lg p-1 text-red-700 hover:bg-red-100 dark:text-red-300 dark:hover:bg-red-900/40"
            aria-label="Dismiss error"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="mt-4 shrink-0 rounded-2xl border border-slate-200/90 bg-white/70 p-3 shadow-lg shadow-slate-900/5 backdrop-blur-xl dark:border-neutral-800 dark:bg-[#0a0a0a]/80 dark:shadow-black/40 sm:p-4">
        <form
          className="flex gap-2 sm:gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            submitQuery(q);
          }}
        >
          <input
            className="input-field min-h-[44px] flex-1"
            placeholder="Ask anything about your documents or spend…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Message"
          />
          <button
            type="submit"
            className="btn-primary flex min-h-[44px] shrink-0 items-center justify-center px-5"
            disabled={mut.isPending}
          >
            <Send className="h-4 w-4 sm:hidden" aria-hidden />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>
      </div>
    </div>
  );
}
