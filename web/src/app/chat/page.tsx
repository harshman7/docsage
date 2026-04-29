"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Loader2, Send } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { apiPostJson } from "@/lib/api";

type ChatResp = {
  answer: string;
  sources?: unknown[];
  sql_query?: string | null;
  steps?: unknown[];
  tool_calls?: unknown[];
};

export default function ChatPage() {
  const [q, setQ] = useState("");
  const [msgs, setMsgs] = useState<{ role: "user" | "assistant"; text: string }[]>(
    []
  );
  const mut = useMutation({
    mutationFn: (query: string) =>
      apiPostJson<ChatResp>("/chat/insights", {
        query,
        use_rag: true,
        use_sql: true,
      }),
    onSuccess: (data) =>
      setMsgs((m) => [...m, { role: "assistant", text: data.answer }]),
  });

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Chat"
        description="Ask questions about your documents and spending. Answers use RAG and SQL when available."
      />
      <div className="card flex min-h-[320px] flex-col p-5 sm:p-6">
        <div className="flex-1 space-y-6">
          {msgs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-100 text-teal-700 dark:bg-amber-950/60 dark:text-amber-400 dark:ring-1 dark:ring-amber-600/30">
                <Send className="h-5 w-5" strokeWidth={2} />
              </div>
              <p className="max-w-sm text-sm text-slate-600 dark:text-slate-300">
                Try: &ldquo;What did I spend on rent last quarter?&rdquo; or
                &ldquo;Summarize my latest invoices.&rdquo;
              </p>
            </div>
          )}
          {msgs.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[min(100%,28rem)] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                  m.role === "user"
                    ? "bg-gradient-to-br from-teal-600 to-teal-700 text-white dark:from-amber-700 dark:to-amber-950 dark:text-amber-50"
                    : "border border-slate-200 bg-slate-50 text-left text-slate-800 dark:border-neutral-700 dark:bg-[#0a0a0a] dark:text-neutral-100"
                }`}
              >
                {m.role === "assistant" ? (
                  <div className="rich-md text-sm">
                    <ReactMarkdown>{m.text}</ReactMarkdown>
                  </div>
                ) : (
                  m.text
                )}
              </div>
            </div>
          ))}
          {mut.isPending && (
            <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-300">
              <Loader2 className="h-4 w-4 animate-spin" />
              Thinking…
            </div>
          )}
          {mut.isError && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
              {(mut.error as Error).message}
            </p>
          )}
        </div>
      </div>
      <form
        className="mt-5 flex gap-2 sm:gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          const query = q.trim();
          if (!query) return;
          setMsgs((m) => [...m, { role: "user", text: query }]);
          setQ("");
          mut.mutate(query);
        }}
      >
        <input
          className="input-field flex-1"
          placeholder="Ask anything about your documents or spend…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          type="submit"
          className="btn-primary shrink-0 px-5"
          disabled={mut.isPending}
        >
          <Send className="h-4 w-4 sm:hidden" />
          <span className="hidden sm:inline">Send</span>
        </button>
      </form>
    </div>
  );
}
