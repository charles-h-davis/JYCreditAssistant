"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import useSWR, { useSWRConfig } from "swr";
import { AppShell } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNote } from "@/components/ui/primitives";
import { RangeSlider } from "@/components/ui/slider";
import { createPurchasePlan, getMonthlyPayment } from "@/lib/api/endpoints";
import {
  amortise,
  minimumPayment,
  monthsToLabel,
  paymentCoversInterest,
  suggestPayment,
} from "@/lib/finance/credit";
import { formatMoney, formatPercent } from "@/lib/format";
import { useCards } from "@/lib/state/cards";
import { usePurchaseDraft } from "@/lib/state/purchase-draft";
import { useSession } from "@/lib/state/session";

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Total cost with interest: the slider re-prices the purchase live on the phone
 * using the same maths as the backend (see lib/finance/credit.ts).
 */
export default function PurchasePlanPage() {
  const router = useRouter();
  const { userId } = useSession();
  const { cards, selected } = useCards();
  const { draft, clearDraft } = usePurchaseDraft();
  const { mutate } = useSWRConfig();

  // Price the purchase against the card it was started on, not whatever happens to
  // be selected now.
  const card = useMemo(
    () => cards.find((entry) => entry.id === draft?.cardId) ?? selected ?? null,
    [cards, draft?.cardId, selected],
  );

  const cardId = card?.id;
  const { data: paymentRow } = useSWR(
    userId && cardId ? `monthly-payment:${userId}:${cardId}` : null,
    () => getMonthlyPayment(userId as string, cardId as string),
    // Always read the card's stored repayment fresh when this screen opens.
    { revalidateOnMount: true, revalidateIfStale: true },
  );

  const balance = card?.current_balance ?? 0;
  const apr = card?.purchase_apr ?? 0;
  const price = draft?.price ?? 0;
  const total = balance + price;
  // The slider runs from the minimum payment up to the whole balance, which
  // settles the card in a single month with no extra interest.
  const minPayment = minimumPayment(total, apr);
  const maxPayment = Math.max(Math.ceil(total * 100) / 100, minPayment + 1);
  const startPayment = clamp(
    paymentRow?.monthly_payment ?? suggestPayment(total, apr),
    minPayment,
    maxPayment,
  );

  // The dragged value belongs to one card, so switching cards falls straight back
  // to that card's stored repayment.
  const [drag, setDrag] = useState<{ cardId: string; value: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const payment = drag && drag.cardId === (card?.id ?? "") ? drag.value : null;
  const value = payment ?? startPayment;

  if (!draft) {
    return (
      <AppShell>
        <TopBar showCamera={false} />
        <div className="mt-6">
          <EmptyState
            title="No purchase in progress"
            body="Start with a photo or enter the details by hand."
            action={
              <button
                type="button"
                onClick={() => router.push("/purchase")}
                className="btn btn-primary mt-3 px-6"
              >
                Check a purchase
              </button>
            }
          />
        </div>
      </AppShell>
    );
  }

  const payable = paymentCoversInterest(balance + price, apr, value);
  const baseline = amortise(balance, apr, value);
  const withItem = amortise(balance + price, apr, value);
  const extraInterest = Math.max(withItem.totalInterest - baseline.totalInterest, 0);
  const totalCost = price + extraInterest;
  const extraMonths = Math.max(withItem.months - baseline.months, 0);

  async function addPurchase() {
    if (!userId || !card) return;
    setSaving(true);
    setError(null);
    try {
      await createPurchasePlan({
        user_id: userId,
        card_id: card.id,
        product_name: draft?.productName,
        purchase_amount: price,
        monthly_payment: value,
        months_to_payoff: payable ? withItem.months : null,
        total_interest: Math.round(extraInterest * 100) / 100,
      });
      await Promise.all([
        mutate(`purchase-plans:${userId}`),
        mutate(`monthly-payment:${userId}:${card.id}`),
        mutate(`cards:${userId}`),
      ]);
      clearDraft();
      router.push("/purchase");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn't save that purchase.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />

      <h1 className="mt-5 text-[1.9rem] leading-tight font-semibold tracking-tight">
        {draft.productName}
      </h1>

      <div className="mt-3 flex items-stretch gap-3">
        <div className="flex-1 text-center">
          <p className="text-sm text-ink-soft">Cost today</p>
          <p className="text-[1.75rem] leading-tight font-semibold tracking-tight">
            {formatMoney(price)}
          </p>
        </div>
        <div className="surface px-3 py-1 text-center">
          <p className="text-sm text-ink-soft">APR</p>
          <p className="text-[1.5rem] leading-tight font-semibold tracking-tight">
            {formatPercent(apr)}
          </p>
        </div>
      </div>

      <p className="mt-5 text-[1.05rem] text-ink-soft">Adjust Monthly Repayments:</p>
      <div className="mt-3">
        <RangeSlider
          label="Monthly repayment"
          min={minPayment}
          max={maxPayment}
          step={5}
          value={value}
          onChange={(next) => setDrag({ cardId: card?.id ?? "", value: next })}
          minLabel={`Min ${formatMoney(minPayment, { whole: true })}`}
          maxLabel={formatMoney(maxPayment, { whole: true })}
        />
        <p className="mt-3 text-center text-[2.25rem] leading-none font-semibold tracking-tight">
          {formatMoney(value, { whole: true })}
          <span className="ml-1 text-base font-normal text-muted">/month</span>
        </p>
      </div>

      <div className="mt-5">
        <p className="text-[1.05rem] text-ink-soft">Total Cost with interest</p>
        <p className="text-[2.4rem] leading-tight font-semibold tracking-tight">
          {formatMoney(totalCost)}
        </p>
        <p className="text-[1.05rem] text-ink-soft">Debt Free in</p>
        <p className="text-[1.6rem] leading-tight font-semibold tracking-tight">
          {payable ? monthsToLabel(withItem.months) : "—"}{" "}
          {payable && extraMonths > 0 ? (
            <span className="text-base font-normal text-muted">(+{extraMonths}m)</span>
          ) : null}
        </p>
        <p className="mt-1 text-xs text-muted">
          Includes {formatMoney(extraInterest)} of extra interest on this card.
        </p>
      </div>

      {!payable ? (
        <div className="mt-3">
          <ErrorNote>
            That payment doesn&apos;t cover the monthly interest, so the balance would
            never clear. Raise the slider.
          </ErrorNote>
        </div>
      ) : null}

      {error ? (
        <div className="mt-3">
          <ErrorNote>{error}</ErrorNote>
        </div>
      ) : null}

      <div className="mt-8 flex gap-3">
        <Button
          variant="secondary"
          className="flex-1"
          onClick={() => {
            clearDraft();
            router.push("/purchase");
          }}
        >
          Cancel
        </Button>
        <Button
          className="flex-1"
          onClick={addPurchase}
          loading={saving}
          disabled={!payable || !card}
        >
          Add Purchase
        </Button>
      </div>
    </AppShell>
  );
}
