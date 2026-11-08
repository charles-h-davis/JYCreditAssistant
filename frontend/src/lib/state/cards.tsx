"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import useSWR from "swr";
import { listCards } from "@/lib/api/endpoints";
import type { CreditCard } from "@/lib/api/types";
import { useSession } from "@/lib/state/session";

interface CardsValue {
  cards: CreditCard[];
  selected: CreditCard | null;
  selectedIndex: number;
  isLoading: boolean;
  error: Error | null;
  selectCard: (index: number) => void;
  nextCard: () => void;
  previousCard: () => void;
  refresh: () => void;
}

const CardsContext = createContext<CardsValue | null>(null);

export function CardsProvider({ children }: { children: ReactNode }) {
  const { userId, status } = useSession();
  const [selectedIndex, setSelectedIndex] = useState(0);

  const { data, error, isLoading, mutate } = useSWR<CreditCard[]>(
    userId ? ["cards", userId] : null,
    ([, id]: [string, string]) => listCards(id),
    { revalidateOnFocus: false },
  );

  const cards = useMemo(() => data ?? [], [data]);
  const safeIndex = cards.length === 0 ? 0 : Math.min(selectedIndex, cards.length - 1);

  const selectCard = useCallback(
    (index: number) => {
      if (cards.length === 0) return;
      setSelectedIndex(((index % cards.length) + cards.length) % cards.length);
    },
    [cards.length],
  );

  const nextCard = useCallback(() => {
    if (cards.length < 2) return;
    setSelectedIndex((current) => (current + 1) % cards.length);
  }, [cards.length]);

  const previousCard = useCallback(() => {
    if (cards.length < 2) return;
    setSelectedIndex((current) => (current - 1 + cards.length) % cards.length);
  }, [cards.length]);

  const value = useMemo<CardsValue>(
    () => ({
      cards,
      selected: cards[safeIndex] ?? null,
      selectedIndex: safeIndex,
      isLoading: status === "loading" || isLoading,
      error: error ?? null,
      selectCard,
      nextCard,
      previousCard,
      refresh: () => void mutate(),
    }),
    [cards, safeIndex, status, isLoading, error, selectCard, nextCard, previousCard, mutate],
  );

  return <CardsContext.Provider value={value}>{children}</CardsContext.Provider>;
}

export function useCards(): CardsValue {
  const context = useContext(CardsContext);
  if (!context) throw new Error("useCards must be used inside <CardsProvider>.");
  return context;
}
