"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/contexts/auth";

export default function AuthCallbackPage() {
  const { setTokenFromOAuth } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.replace(/^#/, ""));
    const token = params.get("access_token");

    if (token) {
      setTokenFromOAuth(token);
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [setTokenFromOAuth, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <p className="text-sm text-slate-500 dark:text-neutral-400">Completing sign-in...</p>
    </div>
  );
}
