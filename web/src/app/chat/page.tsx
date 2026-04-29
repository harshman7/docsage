"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
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
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Chat</h1>
      <div className="rounded-xl border border-zinc-200 bg-white p-4 min-h-[280px] space-y-4">
        {msgs.length === 0 && (
          <p className="text-zinc-500 text-sm">Ask anything about your documents or spend.</p>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <div
              className={`inline-block rounded-lg px-3 py-2 text-sm max-w-[90%] ${
                m.role === "user"
                  ? "bg-zinc-900 text-white"
                  : "bg-zinc-100 text-left text-sm"
              }`}
            >
              {m.role === "assistant" ? (
                <ReactMarkdown>{m.text}</ReactMarkdown>
              ) : (
                m.text
              )}
            </div>
          </div>
        ))}
        {mut.isPending && (
          <p className="text-sm text-zinc-500 animate-pulse">Thinking…</p>
        )}
        {mut.isError && (
          <p className="text-sm text-red-600">{(mut.error as Error).message}</p>
        )}
      </div>
      <form
        className="flex gap-2"
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
          className="flex-1 rounded-md border border-zinc-300 px-3 py-2 text-sm"
          placeholder="e.g. What did I spend on rent last quarter?"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          type="submit"
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-50"
          disabled={mut.isPending}
        >
          Send
        </button>
      </form>
    </div>
  );
}
