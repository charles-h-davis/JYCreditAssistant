import type { CardTransaction } from "@/lib/api/types";
import { formatMonth } from "@/lib/format";

/** Plaid `personal_finance_category.primary` -> display label. */
export const CATEGORY_LABELS: Record<string, string> = {
  FOOD_AND_DRINK: "Food & Drink",
  GROCERIES: "Groceries",
  TRANSPORTATION: "Transport",
  TRAVEL: "Travel",
  GENERAL_MERCHANDISE: "Shopping",
  RENT_AND_UTILITIES: "Bills",
  ENTERTAINMENT: "Entertainment",
  PERSONAL_CARE: "Health",
  MEDICAL: "Medical",
  LOAN_PAYMENTS: "Payments",
  BANK_FEES: "Fees",
  INCOME: "Income",
  TRANSFER_IN: "Transfers",
  TRANSFER_OUT: "Transfers",
  OTHER: "Other",
};

export function categoryLabel(category: string | null): string {
  if (!category) return "Other";
  return CATEGORY_LABELS[category] ?? titleCase(category);
}

function titleCase(value: string): string {
  return value
    .toLowerCase()
    .split(/[\s_]+/)
    .filter(Boolean)
    .map((word) => (word[0]?.toUpperCase() ?? "") + word.slice(1))
    .join(" ");
}

export function transactionTitle(transaction: CardTransaction): string {
  return transaction.merchant_name ?? transaction.description ?? "Transaction";
}

export function transactionDate(transaction: CardTransaction): string {
  return transaction.authorized_date ?? transaction.posted_date ?? "";
}

/** `2026-11` for a transaction, or "" when it has no date. */
export function monthKeyOf(transaction: CardTransaction): string {
  return transactionDate(transaction).slice(0, 7);
}

export interface MonthGroup {
  key: string;
  label: string;
  transactions: CardTransaction[];
  net: number;
  spent: number;
  /** Balance at the end of this month (needs `currentBalance` to be supplied). */
  closing: number | null;
}

/**
 * Group transactions into months, newest first. `net` keeps Plaid's sign
 * convention (positive = money left the account), so a net refund is negative.
 * Passing `currentBalance` also works out each month's closing balance, so the
 * history adds up to the balance shown on the dashboard.
 */
export function groupByMonth(
  transactions: CardTransaction[],
  currentBalance?: number,
): MonthGroup[] {
  const groups = new Map<string, CardTransaction[]>();
  for (const transaction of transactions) {
    const key = monthKeyOf(transaction);
    if (!key) continue;
    const bucket = groups.get(key);
    if (bucket) bucket.push(transaction);
    else groups.set(key, [transaction]);
  }

  const ordered = [...groups.entries()]
    .sort((a, b) => (a[0] < b[0] ? 1 : -1))
    .map(([key, items]) => {
      const sorted = items.sort((a, b) => transactionDate(b).localeCompare(transactionDate(a)));
      const net = sorted.reduce((sum, item) => sum + item.amount, 0);
      const spent = sorted.reduce((sum, item) => sum + Math.max(item.amount, 0), 0);
      return {
        key,
        label: formatMonth(key),
        transactions: sorted,
        net: Math.round(net * 100) / 100,
        spent: Math.round(spent * 100) / 100,
      };
    });

  let running = typeof currentBalance === "number" ? currentBalance : null;
  return ordered.map((group) => {
    const closing = running;
    if (running !== null) running = Math.round((running - group.net) * 100) / 100;
    return { ...group, closing };
  });
}

/** Distinct categories present in a month, ordered by spend. */
export function categoriesFor(transactions: CardTransaction[]): string[] {
  const totals = new Map<string, number>();
  for (const transaction of transactions) {
    const key = transaction.category ?? "OTHER";
    totals.set(key, (totals.get(key) ?? 0) + Math.abs(transaction.amount));
  }
  return [...totals.entries()].sort((a, b) => b[1] - a[1]).map(([key]) => key);
}

export interface DayValue {
  date: string;
  value: number;
}

function isoDay(date: Date): string {
  // Local (not UTC) day key so the buckets match the user's phone.
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function windowStart(today: Date, days: number): Date {
  const start = new Date(today);
  start.setHours(12, 0, 0, 0);
  start.setDate(start.getDate() - (days - 1));
  return start;
}

function dayBuckets(
  transactions: CardTransaction[],
  days: number,
  today: Date,
  pick: (amount: number) => number,
): { buckets: Map<string, number>; start: Date } {
  const start = windowStart(today, days);
  const startKey = isoDay(start);
  const endKey = isoDay(today);
  const buckets = new Map<string, number>();
  for (const transaction of transactions) {
    const day = transactionDate(transaction).slice(0, 10);
    if (!day || day < startKey || day > endKey) continue;
    buckets.set(day, (buckets.get(day) ?? 0) + pick(transaction.amount));
  }
  return { buckets, start };
}

function walk(start: Date, days: number, step: (key: string) => number): DayValue[] {
  const series: DayValue[] = [];
  for (let offset = 0; offset < days; offset += 1) {
    const day = new Date(start);
    day.setDate(day.getDate() + offset);
    const key = isoDay(day);
    series.push({ date: key, value: Math.round(step(key) * 100) / 100 });
  }
  return series;
}

/**
 * Reconstruct the balance for each of the last `days` days.
 *
 * `currentBalance` is "now" and Plaid amounts are positive for spend, so the
 * balance at the start of the window is `current - sum(amounts in the window)`.
 */
export function balanceSeries(
  transactions: CardTransaction[],
  currentBalance: number,
  days = 30,
  today = new Date(),
): DayValue[] {
  const { buckets, start } = dayBuckets(transactions, days, today, (amount) => amount);
  const net = [...buckets.values()].reduce((sum, value) => sum + value, 0);
  let running = currentBalance - net;
  return walk(start, days, (key) => {
    running += buckets.get(key) ?? 0;
    return running;
  });
}

/** Cumulative spend across the window (payments ignored). */
export function cumulativeSpend(
  transactions: CardTransaction[],
  days = 30,
  today = new Date(),
): DayValue[] {
  const { buckets, start } = dayBuckets(transactions, days, today, (amount) =>
    Math.max(amount, 0),
  );
  let running = 0;
  return walk(start, days, (key) => {
    running += buckets.get(key) ?? 0;
    return running;
  });
}

/** Cumulative net spend across the window (payments subtract). */
export function cumulativeNet(
  transactions: CardTransaction[],
  days = 30,
  today = new Date(),
): DayValue[] {
  const { buckets, start } = dayBuckets(transactions, days, today, (amount) => amount);
  let running = 0;
  return walk(start, days, (key) => {
    running += buckets.get(key) ?? 0;
    return running;
  });
}

/**
 * Net spend *per day* (not cumulative) across the window — the values behind the
 * net-spending bar chart.
 */
export function dailyNet(
  transactions: CardTransaction[],
  days = 30,
  today = new Date(),
): DayValue[] {
  const { buckets, start } = dayBuckets(transactions, days, today, (amount) => amount);
  return walk(start, days, (key) => buckets.get(key) ?? 0);
}

