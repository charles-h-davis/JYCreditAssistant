"use client";

import {
  ArrowDownLeft,
  Car,
  Film,
  HeartPulse,
  MoreHorizontal,
  Receipt,
  ShoppingBag,
  ShoppingCart,
  Utensils,
} from "lucide-react";
import type { CardTransaction } from "@/lib/api/types";
import { transactionDate, transactionTitle } from "@/lib/finance/transactions";
import { formatDayOrDateTime, formatMoney } from "@/lib/format";

const ICONS: Record<string, typeof ShoppingCart> = {
  FOOD_AND_DRINK: Utensils,
  GROCERIES: ShoppingCart,
  TRANSPORTATION: Car,
  TRAVEL: Car,
  GENERAL_MERCHANDISE: ShoppingBag,
  RENT_AND_UTILITIES: Receipt,
  ENTERTAINMENT: Film,
  PERSONAL_CARE: HeartPulse,
  MEDICAL: HeartPulse,
  LOAN_PAYMENTS: ArrowDownLeft,
  INCOME: ArrowDownLeft,
  TRANSFER_IN: ArrowDownLeft,
};

/**
 * One transaction row: rounded pale tile, category glyph, merchant and amount.
 * Money out is shown as a debit; payments back to the card are green and signed +.
 */
export function TransactionRow({ transaction }: { transaction: CardTransaction }) {
  const Icon = ICONS[transaction.category ?? "OTHER"] ?? MoreHorizontal;
  const isCredit = transaction.amount < 0;

  return (
    <li className="flex items-center gap-3 rounded-2xl bg-surface px-3 py-2.5">
      <span
        className="grid size-9 shrink-0 place-items-center rounded-xl bg-surface-strong/80 text-ink"
        aria-hidden
      >
        <Icon size={18} strokeWidth={1.8} />
      </span>

      <div className="min-w-0 flex-1">
        <p className="truncate text-[0.95rem] leading-tight font-medium text-ink">
          {transactionTitle(transaction)}
        </p>
        <p className="text-xs text-muted">
          {formatDayOrDateTime(transactionDate(transaction))}
          {transaction.pending ? " · pending" : ""}
        </p>
      </div>

      <p
        className={`shrink-0 text-[0.95rem] font-medium tabular-nums ${
          isCredit ? "text-positive" : "text-ink"
        }`}
      >
        {isCredit ? "+" : "−"}
        {formatMoney(Math.abs(transaction.amount))}
      </p>
    </li>
  );
}
