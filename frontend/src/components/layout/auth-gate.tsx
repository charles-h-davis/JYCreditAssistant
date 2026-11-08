"use client";

import type { ReactNode } from "react";
import { RequireAuth } from "@/components/layout/app-shell";

/**
 * Thin client boundary so `(app)/layout.tsx` can stay a server component and
 * still opt out of instant-navigation validation via a route segment export.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
