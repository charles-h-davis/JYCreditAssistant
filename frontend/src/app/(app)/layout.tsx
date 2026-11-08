import type { ReactNode } from "react";
import { AuthGate } from "@/components/layout/auth-gate";

/**
 * The authenticated shell is entirely client-rendered (the session and every
 * query live in the browser), so opt this segment out of Next's instant-navigation
 * validation — otherwise the guard's loading state looks like a "dropped segment".
 */
export const instant = false;

export default function AppLayout({ children }: { children: ReactNode }) {
  return <AuthGate>{children}</AuthGate>;
}

