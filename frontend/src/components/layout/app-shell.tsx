"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { BottomNav } from "@/components/layout/bottom-nav";
import { useSession } from "@/lib/state/session";

/** Mobile-first column: 430px on desktop, full width on a phone. */
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-column flex min-h-dvh flex-col bg-page">
      <div className="flex-1 px-4 pb-32">{children}</div>
      <BottomNav />
    </div>
  );
}

export function LoadingSplash({ label = "Loading your account" }: { label?: string }) {
  return (
    <div className="app-column grid place-items-center bg-page" aria-busy="true">
      <div className="flex flex-col items-center gap-3">
        <span className="size-8 animate-spin rounded-full border-2 border-surface-strong border-t-accent" />
        <p className="text-sm text-muted">{label}</p>
      </div>
    </div>
  );
}

/** Bounces to /sign-in when there is no session. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "anonymous") router.replace("/sign-in");
  }, [status, router]);

  if (status !== "authenticated") return <LoadingSplash />;
  return <>{children}</>;
}
