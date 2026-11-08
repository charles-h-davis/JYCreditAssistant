"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Session } from "@supabase/supabase-js";
import { isSupabaseConfigured, getSupabaseBrowserClient } from "@/lib/supabase/browser";

export type SessionStatus = "loading" | "authenticated" | "anonymous";

interface SessionValue {
  status: SessionStatus;
  session: Session | null;
  userId: string | null;
  displayName: string;
  email: string;
  /** Throws an `Error` with a phone-friendly message when auth fails. */
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  signOut: () => Promise<void>;
  updateDisplayName: (name: string) => Promise<void>;
  authConfigured: boolean;
}

const SessionContext = createContext<SessionValue | null>(null);

function nameFromSession(session: Session | null): string {
  const metadata = (session?.user?.user_metadata ?? {}) as Record<string, unknown>;
  const candidate = metadata.display_name ?? metadata.full_name ?? metadata.name;
  if (typeof candidate === "string" && candidate.trim()) return candidate.trim();
  const email = session?.user?.email ?? "";
  const local = email.split("@")[0] ?? "";
  return local ? local.charAt(0).toUpperCase() + local.slice(1) : "You";
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<SessionStatus>(
    isSupabaseConfigured ? "loading" : "anonymous",
  );

  useEffect(() => {
    const client = getSupabaseBrowserClient();
    if (!client) return;

    let active = true;
    client.auth.getSession().then(({ data }) => {
      if (!active) return;
      setSession(data.session ?? null);
      setStatus(data.session ? "authenticated" : "anonymous");
    });

    const { data: subscription } = client.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      setStatus(next ? "authenticated" : "anonymous");
    });

    return () => {
      active = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const client = getSupabaseBrowserClient();
    if (!client) throw new Error("Supabase isn't configured. Check frontend/.env.local.");
    const { error } = await client.auth.signInWithPassword({
      email: email.trim(),
      password,
    });
    if (error) throw new Error(error.message);
  }, []);

  const signUp = useCallback(async (email: string, password: string, name?: string) => {
    const client = getSupabaseBrowserClient();
    if (!client) throw new Error("Supabase isn't configured. Check frontend/.env.local.");
    const { data, error } = await client.auth.signUp({
      email: email.trim(),
      password,
      options: { data: { display_name: name?.trim() || undefined } },
    });
    if (error) throw new Error(error.message);
    if (!data.session) {
      // Email confirmation is on for this project: tell the caller to sign in.
      throw new Error("Check your inbox to confirm the account, then sign in.");
    }
  }, []);

  const signOut = useCallback(async () => {
    const client = getSupabaseBrowserClient();
    await client?.auth.signOut();
    setSession(null);
    setStatus("anonymous");
    router.replace("/sign-in");
  }, [router]);

  const updateDisplayName = useCallback(async (name: string) => {
    const client = getSupabaseBrowserClient();
    if (!client) throw new Error("Supabase isn't configured.");
    const { data, error } = await client.auth.updateUser({
      data: { display_name: name.trim() },
    });
    if (error) throw new Error(error.message);
    if (data.user) {
      setSession((current) => (current ? { ...current, user: data.user } : current));
    }
  }, []);

  const value = useMemo<SessionValue>(
    () => ({
      status,
      session,
      userId: session?.user?.id ?? null,
      displayName: nameFromSession(session),
      email: session?.user?.email ?? "",
      signIn,
      signUp,
      signOut,
      updateDisplayName,
      authConfigured: isSupabaseConfigured,
    }),
    [status, session, signIn, signUp, signOut, updateDisplayName],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const context = useContext(SessionContext);
  if (!context) throw new Error("useSession must be used inside <SessionProvider>.");
  return context;
}
