"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { motion } from "motion/react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { CardSwitcher } from "@/components/layout/card-switcher";
import { TopBar } from "@/components/layout/top-bar";
import { CategoryFilter } from "@/components/transactions/category-filter";
import { TransactionRow } from "@/components/transactions/transaction-row";
import { EmptyState, ErrorNote, Skeleton } from "@/components/ui/primitives";
import { listCardTransactions } from "@/lib/api/endpoints";
import type { CardTransaction } from "@/lib/api/types";
import { groupByMonth, type MonthGroup } from "@/lib/finance/transactions";
import { formatMoney } from "@/lib/format";
import { useCards } from "@/lib/state/cards";
import { useSession } from "@/lib/state/session";

export default function TransactionsPage() {
  const { userId } = useSession();
  const { selected: card, isLoading: cardsLoading } = useCards();
  const [category, setCategory] = useState<string | null>(null);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [direction, setDirection] = useState(1);

  const cardId = card?.id;
  const { data, error, isLoading } = useSWR(
    cardId && userId ? `transactions:${userId}:${cardId}` : null,
    () => listCardTransactions(userId as string, cardId as string),
  );

  // Closing balances are derived from the card's current balance, so the months
  // add up to exactly the number on the dashboard. `groupByMonth` returns newest
  // first (it walks backwards from today), so display it reversed: oldest on the
  // left, the current month on the right.
  const months = useMemo(() => {
    const newestFirst = groupByMonth(data ?? [], card?.current_balance);
    return [...newestFirst].reverse();
  }, [data, card?.current_balance]);

  // Selected by key, so the async first load simply lands on the newest month.
  const activeIndex = useMemo(() => {
    if (months.length === 0) return -1;
    const found = selectedKey ? months.findIndex((entry) => entry.key === selectedKey) : -1;
    return found >= 0 ? found : months.length - 1;
  }, [months, selectedKey]);

  const month = months[activeIndex] ?? null;

  const visible = useMemo(() => {
    if (!month) return [];
    if (!category) return month.transactions;
    return month.transactions.filter((item) => (item.category ?? "OTHER") === category);
  }, [month, category]);

  function goTo(index: number) {
    if (months.length === 0) return;
    const clamped = Math.max(0, Math.min(index, months.length - 1));
    if (clamped === activeIndex) return;
    setDirection(clamped > activeIndex ? 1 : -1);
    setSelectedKey(months[clamped].key);
    setCategory(null);
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <h1 className="mt-5 text-[2rem] leading-tight font-semibold tracking-tight">
        Transactions
      </h1>

      <div className="mt-3">
        <CardSwitcher />
      </div>

      {isLoading || cardsLoading ? (
        <Skeleton className="mt-4 h-72 w-full" />
      ) : error ? (
        <div className="mt-4">
          <ErrorNote>{error.message}</ErrorNote>
        </div>
      ) : months.length === 0 ? (
        <div className="mt-4">
          <EmptyState
            title="No transactions yet"
            body="Spending on this card will show up here, month by month."
          />
        </div>
      ) : (
        <MonthPanel
          months={months}
          activeIndex={activeIndex}
          month={month}
          direction={direction}
          goTo={goTo}
          category={category}
          setCategory={setCategory}
          visible={visible}
        />
      )}
    </AppShell>
  );
}

function MonthPanel({
  months,
  activeIndex,
  month,
  direction,
  goTo,
  category,
  setCategory,
  visible,
}: {
  months: MonthGroup[];
  activeIndex: number;
  month: MonthGroup | null;
  direction: number;
  goTo: (index: number) => void;
  category: string | null;
  setCategory: (value: string | null) => void;
  visible: CardTransaction[];
}) {
  const atOldest = activeIndex <= 0;
  const atNewest = activeIndex >= months.length - 1;

  return (
    <section className="surface mt-4 p-4">
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => goTo(activeIndex - 1)}
          disabled={atOldest}
          aria-label="Previous month"
          className="grid size-9 place-items-center rounded-full bg-surface-strong/70 text-ink-soft transition active:scale-90 disabled:opacity-30"
        >
          <ChevronLeft size={17} strokeWidth={2.2} aria-hidden />
        </button>

        <div className="flex flex-col items-center">
          <p className="text-sm font-medium text-ink-soft">{month?.label}</p>
          <div className="mt-1.5 flex items-center gap-1.5" role="tablist" aria-label="Month">
            {months.map((entry, index) => {
              const active = index === activeIndex;
              return (
                <button
                  key={entry.key}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  aria-label={entry.label}
                  onClick={() => goTo(index)}
                  className={`h-1.5 rounded-full transition-all duration-200 ${
                    active ? "w-5 bg-ink-soft/70" : "w-1.5 bg-surface-strong"
                  }`}
                />
              );
            })}
          </div>
        </div>

        <button
          type="button"
          onClick={() => goTo(activeIndex + 1)}
          disabled={atNewest}
          aria-label="Next month"
          className="grid size-9 place-items-center rounded-full bg-surface-strong/70 text-ink-soft transition active:scale-90 disabled:opacity-30"
        >
          <ChevronRight size={17} strokeWidth={2.2} aria-hidden />
        </button>
      </div>

      <motion.div
        key={month?.key ?? "empty"}
        initial={{ opacity: 0, x: direction * 18 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      >
        <div className="mt-3">
          <p className="text-[2rem] leading-tight font-semibold tracking-tight">
            {formatMoney(month?.net ?? 0)}
          </p>
          <p className="text-xs text-muted">
            {formatMoney(month?.spent ?? 0)} spent · net of payments
          </p>
          {month?.closing !== null && month?.closing !== undefined ? (
            <p className="mt-1 text-xs text-muted">
              Balance after {month.label}:{" "}
              <span className="font-medium text-ink-soft">
                {formatMoney(month.closing)}
              </span>
            </p>
          ) : null}
        </div>

        <div className="mt-3">
          <CategoryFilter
            selected={category}
            onSelect={setCategory}
            visibleTransactions={month?.transactions ?? []}
          />
        </div>

        <ul className="mt-3 space-y-2">
          {visible.length === 0 ? (
            <li>
              <EmptyState title="Nothing in this category" />
            </li>
          ) : (
            visible.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))
          )}
        </ul>
      </motion.div>
    </section>
  );
}
