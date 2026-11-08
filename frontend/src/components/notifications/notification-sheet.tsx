"use client";

import { useState } from "react";
import { Check, X } from "lucide-react";
import { EmptyState, ErrorNote, Sheet, Skeleton } from "@/components/ui/primitives";
import type { PurchaseMatch } from "@/lib/api/types";
import { formatMoney, formatShortDate } from "@/lib/format";

/**
 * The bell's sheet: one suspected match per row with the two answers.
 * ✓ removes the planned purchase, ✗ keeps it and stops asking about that pair.
 */
export function NotificationSheet({
  open,
  onClose,
  matches,
  loading,
  error,
  onAccept,
  onDismiss,
}: {
  open: boolean;
  onClose: () => void;
  matches: PurchaseMatch[];
  loading: boolean;
  error: string | null;
  onAccept: (match: PurchaseMatch) => Promise<void>;
  onDismiss: (match: PurchaseMatch) => Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function answer(
    match: PurchaseMatch,
    action: (match: PurchaseMatch) => Promise<void>,
  ) {
    if (busyId) return;
    setBusyId(match.id);
    setActionError(null);
    try {
      await action(match);
    } catch (caught) {
      setActionError(
        caught instanceof Error ? caught.message : "Couldn't save that answer.",
      );
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Sheet open={open} onClose={onClose} title="Notifications">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-xl font-semibold tracking-tight">Did you buy these?</h2>
        <p className="text-xs text-muted">
          {matches.length} to review
        </p>
      </div>
      <p className="mt-1 text-sm text-ink-soft">
        A card transaction matches something you planned to buy. Tick it to clear the
        plan, or cross it to keep the plan and stop asking.
      </p>

      <div className="mt-3 max-h-[52vh] overflow-y-auto">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-28 w-full" />
          </div>
        ) : error ? (
          <ErrorNote>{error}</ErrorNote>
        ) : matches.length === 0 ? (
          <EmptyState
            title="Nothing to review"
            body="When a transaction matches a planned purchase, it shows up here."
          />
        ) : (
          <ul className="space-y-2.5">
            {matches.map((match) => {
              const title =
                match.product_name ?? match.merchant_name ?? "A planned purchase";
              const busy = busyId === match.id;
              return (
                <li key={match.id} className="rounded-2xl bg-surface p-3.5">
                  <p className="text-sm font-medium text-ink">{title}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    {formatMoney(match.amount)}
                    {match.merchant_name ? ` · ${match.merchant_name}` : ""}
                    {` · ${formatShortDate(match.transaction_date)}`}
                  </p>
                  <div className="mt-3 flex gap-2">
                    <button
                      type="button"
                      onClick={() => void answer(match, onAccept)}
                      disabled={busyId !== null}
                      aria-label={`Confirm: ${title} was bought`}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-positive px-3 py-2.5 text-sm font-medium text-white transition active:scale-[0.99] disabled:opacity-60"
                    >
                      <Check size={16} strokeWidth={2.4} aria-hidden />
                      It happened
                    </button>
                    <button
                      type="button"
                      onClick={() => void answer(match, onDismiss)}
                      disabled={busyId !== null}
                      aria-label={`Dismiss: ${title} was not bought`}
                      className="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-surface-strong px-3 py-2.5 text-sm font-medium text-ink transition active:scale-[0.99] disabled:opacity-60"
                    >
                      <X size={16} strokeWidth={2.4} aria-hidden />
                      Not that
                    </button>
                  </div>
                  {busy ? (
                    <p className="mt-2 text-center text-xs text-muted">Saving…</p>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {actionError ? (
        <div className="mt-2">
          <ErrorNote>{actionError}</ErrorNote>
        </div>
      ) : null}
    </Sheet>
  );
}
