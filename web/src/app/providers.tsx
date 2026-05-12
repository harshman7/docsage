"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { useState } from "react";
import { AuthProvider } from "@/contexts/auth";
import { ChatSessionProvider } from "@/contexts/chat-session";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      storageKey="docsage-theme"
    >
      <QueryClientProvider client={client}>
        <AuthProvider>
          <ChatSessionProvider>{children}</ChatSessionProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
