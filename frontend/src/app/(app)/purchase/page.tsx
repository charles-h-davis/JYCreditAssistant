"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { Camera, Pencil, Trash2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { CardSwitcher } from "@/components/layout/card-switcher";
import { TopBar } from "@/components/layout/top-bar";
import { ErrorNote, Skeleton } from "@/components/ui/primitives";
import { deletePurchasePlan, listPurchasePlans } from "@/lib/api/endpoints";
import type { CreditCard, PurchasePlan } from "@/lib/api/types";
import { amortise } from "@/lib/finance/credit";
import { formatLongDateTime, formatMoney } from "@/lib/format";
import { useCards } from "@/lib/state/cards";
import { useSession } from "@/lib/state/session";

export default function PurchasePage() {
  const { userId } = useSession();
  const { cards, selected: card } = useCards();
  const [deleting, setDeleting] = useState<string | null>(null);

  const { data, error, isLoading, mutate } = useSWR(
    userId ? `purchase-plans:${userId}` : null,
    () => listPurchasePlans(userId as string),
  );

  // Planned purchases belong to a card, so the screen only shows the ones being
  // considered on the card selected above.
  const plans = (data ?? []).filter((plan) => !card || plan.card_id === card.id);
  const presentValue = plans.reduce((sum, plan) => sum + plan.purchase_amount, 0);

  async function remove(plan: PurchasePlan) {
    if (!userId) return;
    setDeleting(plan.id);
    try {
      await deletePurchasePlan(userId, plan.id);
      await mutate();
    } finally {
      setDeleting(null);
    }
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <h1 className="mt-5 text-[2rem] leading-tight font-semibold tracking-tight">
        Check a Purchase
      </h1>

      <div className="mt-3">
        <CardSwitcher />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <Link
          href="/purchase/photo"
          className="surface flex flex-col gap-4 p-4 transition active:scale-[0.99]"
        >
          <span className="text-[0.95rem] leading-tight text-ink-soft">
            Add with photo
          </span>
          <Camera size={34} strokeWidth={1.6} className="mx-auto" aria-hidden />
        </Link>
        <Link
          href="/purchase/details"
          className="surface flex flex-col gap-4 p-4 transition active:scale-[0.99]"
        >
          <span className="text-[0.95rem] leading-tight text-ink-soft">Enter Manually</span>
          <Pencil size={34} strokeWidth={1.6} className="mx-auto" aria-hidden />
        </Link>
      </div>

      <div className="mt-6">
        <p className="text-[1.05rem] font-medium text-ink-soft">Planned Purchases</p>
        <p className="text-[2rem] leading-tight font-semibold tracking-tight">
          {formatMoney(presentValue)}
        </p>
        <p className="text-sm text-muted">at present value</p>
      </div>

      <div className="surface mt-3 p-3">
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : error ? (
          <ErrorNote>{error.message}</ErrorNote>
        ) : plans.length === 0 ? (
          <p className="px-1 py-6 text-center text-sm text-muted">
            Nothing planned yet. Add a photo of a price tag to see what it really costs.
          </p>
        ) : (
          <ul className="space-y-2">
            {plans.map((plan) => (
              <PlanRow
                key={plan.id}
                plan={plan}
                card={cards.find((entry) => entry.id === plan.card_id) ?? null}
                onDelete={() => remove(plan)}
                deleting={deleting === plan.id}
              />
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
}

function PlanRow({
  plan,
  card,
  onDelete,
  deleting,
}: {
  plan: PurchasePlan;
  card: CreditCard | null;
  onDelete: () => void;
  deleting: boolean;
}) {
  const balance = card?.current_balance ?? 0;
  const apr = card?.purchase_apr ?? 0;
  const payment = plan.monthly_payment || 1;
  const withItem = amortise(balance + plan.purchase_amount, apr, payment);
  const withoutItem = amortise(balance, apr, payment);
  const extraInterest = Math.max(withItem.totalInterest - withoutItem.totalInterest, 0);
  const actualCost = plan.purchase_amount + extraInterest;

  return (
    <li className="rounded-2xl bg-surface-strong/60 p-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs text-muted">{formatLongDateTime(plan.created_at)}</p>
        <button
          type="button"
          onClick={onDelete}
          disabled={deleting}
          aria-label={`Delete ${plan.product_name ?? "purchase"}`}
          className="grid size-7 place-items-center rounded-full text-ink-soft transition active:scale-90 disabled:opacity-40"
        >
          <Trash2 size={15} strokeWidth={1.9} aria-hidden />
        </button>
      </div>
      <p className="mt-0.5 truncate text-[1.05rem] font-semibold">
        {plan.product_name ?? "Planned purchase"}
      </p>
      <div className="mt-0.5 flex items-baseline justify-between gap-2">
        <p className="text-sm text-ink-soft tabular-nums">
          {formatMoney(plan.purchase_amount)}
        </p>
        <p className="text-sm text-ink-soft tabular-nums">
          Actual cost: <span className="font-medium text-ink">{formatMoney(actualCost)}</span>
        </p>
      </div>
    </li>
  );
}
