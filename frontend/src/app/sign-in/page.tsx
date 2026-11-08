"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ErrorNote, Segmented } from "@/components/ui/primitives";
import { DEMO_EMAIL, DEMO_PASSWORD } from "@/lib/config";
import { useSession } from "@/lib/state/session";

type Mode = "signin" | "signup";

export default function SignInPage() {
  const router = useRouter();
  const { status, signIn, signUp } = useSession();
  const [mode, setMode] = useState<Mode>("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState<"demo" | "form" | null>(null);

  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard");
  }, [status, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNote(null);
    setBusy("form");
    try {
      if (mode === "signin") await signIn(email, password);
      else await signUp(email, password, name);
      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(null);
    }
  }

  async function handleDemo() {
    setError(null);
    setNote(null);
    setBusy("demo");
    try {
      await signIn(DEMO_EMAIL, DEMO_PASSWORD);
      router.replace("/dashboard");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? `${caught.message} — try running the demo seed on the backend.`
          : "Couldn't sign in to the demo account.",
      );
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app-column flex min-h-dvh flex-col bg-page px-6 pt-[max(3rem,env(safe-area-inset-top))] pb-[max(2rem,env(safe-area-inset-bottom))]">
      <div className="flex items-center gap-3">
        <span className="grid size-12 place-items-center rounded-2xl bg-ink text-lg font-semibold text-white">
          CM
        </span>
        <div>
          <p className="text-sm text-muted">CreditMate</p>
          <p className="text-base font-medium">Credit, made clear</p>
        </div>
      </div>

      <h1 className="mt-10 text-[2.1rem] leading-[1.15] font-semibold tracking-tight">
        {mode === "signin" ? "Welcome back" : "Create your account"}
      </h1>
      <p className="mt-2 text-sm text-muted">
        See what a purchase really costs, and how long your balance takes to clear.
      </p>

      <div className="mt-6">
        <Segmented<Mode>
          value={mode}
          onChange={(next) => {
            setMode(next);
            setError(null);
            setNote(null);
          }}
          options={[
            { value: "signin", label: "Sign in" },
            { value: "signup", label: "Create account" },
          ]}
        />
      </div>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        {mode === "signup" ? (
          <div>
            <label className="text-sm font-medium text-ink-soft" htmlFor="name">
              Your name
            </label>
            <input
              id="name"
              className="field mt-1.5"
              value={name}
              onChange={(event) => setName(event.target.value)}
              autoComplete="name"
              placeholder="Jamie Young"
            />
          </div>
        ) : null}

        <div>
          <label className="text-sm font-medium text-ink-soft" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            className="field mt-1.5"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label className="text-sm font-medium text-ink-soft" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={6}
            className="field mt-1.5"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
            placeholder="••••••••"
          />
        </div>

        {error ? <ErrorNote>{error}</ErrorNote> : null}
        {note ? <p className="text-sm text-positive">{note}</p> : null}

        <Button type="submit" className="w-full" loading={busy === "form"}>
          {mode === "signin" ? "Sign in" : "Create account"}
        </Button>
      </form>

      <div className="mt-auto pt-8">
        <div className="flex items-center gap-3">
          <span className="h-px flex-1 bg-surface-strong" />
          <span className="text-xs text-muted">or</span>
          <span className="h-px flex-1 bg-surface-strong" />
        </div>
        <Button
          variant="secondary"
          className="mt-4 w-full"
          onClick={handleDemo}
          loading={busy === "demo"}
        >
          Continue with the demo account
        </Button>
        <p className="mt-3 text-center text-xs text-muted">
          Demo data only — {DEMO_EMAIL}. Never enter real card details.
        </p>
      </div>
    </main>
  );
}
