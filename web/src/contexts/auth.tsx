"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { networkErrorMessage, readApiErrorMessage } from "@/lib/api-errors";

const TOKEN_KEY = "docsage_access_token";

export type AuthUser = {
  id: number;
  email: string;
  name?: string | null;
  oauth_provider?: string | null;
};

type AuthContextValue = {
  token: string | null;
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  setTokenFromOAuth: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

const apiBase = () =>
  (process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000") + "/api/v1";

/** Unverified decode of JWT payload for UX fallback when /auth/me fails (network). */
function userFromJwt(accessToken: string): AuthUser | null {
  try {
    const parts = accessToken.split(".");
    if (parts.length < 2) return null;
    const json = atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"));
    const payload = JSON.parse(json) as { sub?: string; email?: string };
    const id = Number(payload.sub);
    const email = payload.email;
    if (!Number.isFinite(id) || !email) return null;
    return { id, email };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const persistToken = useCallback((t: string | null) => {
    setToken(t);
    if (t) {
      localStorage.setItem(TOKEN_KEY, t);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, []);

  const fetchMe = useCallback(
    async (t: string) => {
      try {
        const res = await fetch(`${apiBase()}/auth/me`, {
          headers: { Authorization: `Bearer ${t}` },
        });
        if (res.status === 401 || res.status === 403) {
          persistToken(null);
          setUser(null);
          return;
        }
        if (!res.ok) {
          const fromJwt = userFromJwt(t);
          if (fromJwt) setUser(fromJwt);
          else setUser(null);
          return;
        }
        const data = await res.json();
        setUser(data);
      } catch {
        const fromJwt = userFromJwt(t);
        if (fromJwt) setUser(fromJwt);
        else setUser(null);
      }
    },
    [persistToken]
  );

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      setToken(stored);
      fetchMe(stored).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      let res: Response;
      try {
        res = await fetch(`${apiBase()}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
      } catch (e) {
        throw new Error(networkErrorMessage(e));
      }
      if (!res.ok) {
        throw new Error(await readApiErrorMessage(res, "Login failed"));
      }
      const body = await res.json();
      const access_token = body.access_token as string;
      persistToken(access_token);
      await fetchMe(access_token);
    },
    [persistToken, fetchMe]
  );

  const register = useCallback(
    async (email: string, password: string, name?: string) => {
      let res: Response;
      try {
        res = await fetch(`${apiBase()}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, name }),
        });
      } catch (e) {
        throw new Error(networkErrorMessage(e));
      }
      if (!res.ok) {
        throw new Error(await readApiErrorMessage(res, "Registration failed"));
      }
      const body = await res.json();
      const access_token = body.access_token as string;
      persistToken(access_token);
      await fetchMe(access_token);
    },
    [persistToken, fetchMe]
  );

  const setTokenFromOAuth = useCallback(
    (t: string) => {
      persistToken(t);
      void fetchMe(t);
    },
    [persistToken, fetchMe]
  );

  const logout = useCallback(() => {
    persistToken(null);
    setUser(null);
  }, [persistToken]);

  const value = useMemo(
    () => ({ token, user, loading, login, register, setTokenFromOAuth, logout }),
    [token, user, loading, login, register, setTokenFromOAuth, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
