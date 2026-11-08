"use client";

import type { ReactNode } from "react";
import { SessionProvider } from "@/lib/state/session";
import { CardsProvider } from "@/lib/state/cards";
import { PurchaseDraftProvider } from "@/lib/state/purchase-draft";
import { ThemeProvider } from "@/lib/state/theme";

/**
 * Client-side providers: colour scheme -> auth session -> card list -> purchase
 * draft. Ordered because the card list is keyed on the signed-in user id.
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <SessionProvider>
        <CardsProvider>
          <PurchaseDraftProvider>{children}</PurchaseDraftProvider>
        </CardsProvider>
      </SessionProvider>
    </ThemeProvider>
  );
}

