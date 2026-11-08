"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface PurchaseDraft {
  productName: string;
  price: number;
  source: "photo" | "manual";
  imagePreview: string | null;
  extractionNote: string | null;
  /** The card this purchase is being considered for — pinned when the flow starts. */
  cardId: string | null;
}

interface DraftValue {
  draft: PurchaseDraft | null;
  startDraft: (draft: PurchaseDraft) => void;
  updateDraft: (patch: Partial<PurchaseDraft>) => void;
  clearDraft: () => void;
}

const STORAGE_KEY = "creditmate-purchase-draft";
const DraftContext = createContext<DraftValue | null>(null);

export function PurchaseDraftProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState<PurchaseDraft | null>(null);

  // Rehydrate the draft once on mount. sessionStorage is an external store, so a
  // mount-time read is the correct pattern here — the initial render stays null so
  // server and client markup match.
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const restored = JSON.parse(raw) as PurchaseDraft;
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDraft(restored);
    } catch {
      // Ignore unreadable storage — the flow just starts empty.
    }
  }, []);

  const persist = useCallback((next: PurchaseDraft | null) => {
    setDraft(next);
    try {
      if (next) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      else sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // Storage can be unavailable in private mode; state still works in-session.
    }
  }, []);

  const startDraft = useCallback(
    (next: PurchaseDraft) => persist(next),
    [persist],
  );

  const updateDraft = useCallback(
    (patch: Partial<PurchaseDraft>) => {
      setDraft((current) => {
        if (!current) return current;
        const next = { ...current, ...patch };
        persist(next);
        return next;
      });
    },
    [persist],
  );

  const clearDraft = useCallback(() => persist(null), [persist]);

  const value = useMemo<DraftValue>(
    () => ({ draft, startDraft, updateDraft, clearDraft }),
    [draft, startDraft, updateDraft, clearDraft],
  );

  return <DraftContext.Provider value={value}>{children}</DraftContext.Provider>;
}

export function usePurchaseDraft(): DraftValue {
  const context = useContext(DraftContext);
  if (!context) {
    throw new Error("usePurchaseDraft must be used inside <PurchaseDraftProvider>.");
  }
  return context;
}
