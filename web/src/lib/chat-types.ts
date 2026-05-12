export type SourceItem = {
  document_id?: number | null;
  filename?: string | null;
  chunk_index?: number | null;
  chunk_type?: string | null;
  score?: number | null;
};

export type ChatUserMsg = { role: "user"; text: string };

export type ChatAssistantMsg = {
  role: "assistant";
  text: string;
  sources?: SourceItem[];
  sql_query?: string | null;
  steps?: unknown[];
  tool_calls?: unknown[];
};

export type ChatMsg = ChatUserMsg | ChatAssistantMsg;
