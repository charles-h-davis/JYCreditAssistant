"use client";

import { useState } from "react";
import { useSWRConfig } from "swr";
import { Button } from "@/components/ui/button";
import { ErrorNote, Sheet } from "@/components/ui/primitives";
import { RangeSlider } from "@/components/ui/slider";
import { setMonthlyPayment } from "@/lib/api/endpoints";
import type { CreditCard } from "@/lib/api/types";
import {
  amortise,
  minimumPayment,
  monthsToLabel,
  paymentCoversInterest,
  suggestPayment,
} from "@/lib/finance/credit";
import { formatMoney } from "@/lib/format";
import { useSession } from "@/lib/state/session";

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * The dashboard's monthly-repayment editor: the same slider experience as the
 * purchase cost screen, but it also shows how much sooner the card clears.
 *
 * The range runs from the minimum payment (the lowest that still clears the
 * balance) up to the whole balance, which settles the card in one month.
 */
export function RepaymentEditor({
  card,
  open,
  onClose,
  current,
}: {
  card: CreditCard | null;
  open: boolean;
  onClose: () => void;
  current: number | null;
}) {
  const { userId } = useSession();
  const { mutate } = useSWRConfig();
  const [value, setValue] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const balance = card?.current_balance ?? 0;
  const apr = card?.purchase_apr ?? 0;
  const min = minimumPayment(balance, apr);
  const max = Math.max(Math.round(balance * 100) / 100, min + 1);

  // The stored repayment is where the user is today, so it doubles as the
  // baseline for "x months sooner".
  const baseline = clamp(current ?? suggestPayment(balance, apr, 12), min, max);
  const payment = value ?? baseline;

  const payable = paymentCoversInterest(balance, apr, payment);
  const payoff = payable ? amortise(balance, apr, payment) : null;
  const baselineMonths = amortise(balance, apr, baseline).months;
  const delta = payoff ? baselineMonths - payoff.months : 0;

  function close() {
    setValue(null);
    setError(null);
    onClose();
  }

  async function save() {
    if (!card || !userId) return;
    setSaving(true);
    setError(null);
    try {
      await setMonthlyPayment(userId, card.id, payment);
      await Promise.all([
        mutate(`monthly-payment:${userId}:${card.id}`),
        mutate(`cards:${userId}`),
      ]);
      close();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn't save that payment.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet open={open} onClose={close} title="Monthly repayment">
      <h2 className="text-xl font-semibold tracking-tight">Adjust your repayment</h2>
      <p className="mt-1 text-sm text-muted">
        Slide up to clear the card faster. The whole balance in one go means debt free
        next month, with no extra interest.
      </p>

      <div className="mt-5 text-center">
        <p className="text-[2.5rem] leading-none font-semibold tracking-tight">
          {formatMoney(payment, { whole: true })}
          <span className="ml-1 text-base font-normal text-muted">/month</span>
        </p>
        <p className="mt-2 text-sm text-ink-soft">
          {payoff ? `Debt free in ${monthsToLabel(payoff.months)}` : "Never clears"}
          {payoff && delta !== 0 ? (
            <span
              className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${
                delta > 0 ? "bg-positive/12 text-positive" : "bg-surface-strong text-ink-soft"
              }`}
            >
              {delta > 0
                ? `${delta} month${delta === 1 ? "" : "s"} sooner`
                : `${Math.abs(delta)} month${Math.abs(delta) === 1 ? "" : "s"} later`}
            </span>
          ) : null}
        </p>
        {payoff && payoff.totalInterest > 0 ? (
          <p className="mt-1 text-xs text-muted">
            {formatMoney(payoff.totalInterest)} of interest in total
          </p>
        ) : null}
      </div>

      <div className="mt-4">
        <RangeSlider
          label="Monthly repayment"
          min={min}
          max={max}
          step={5}
          value={payment}
          onChange={setValue}
          minLabel={`Min ${formatMoney(min, { whole: true })}`}
          maxLabel={formatMoney(max, { whole: true })}
        />
      </div>

      {error ? (
        <div className="mt-3">
          <ErrorNote>{error}</ErrorNote>
        </div>
      ) : null}

      <div className="mt-5 flex gap-3">
        <Button variant="secondary" className="flex-1" onClick={close}>
          Cancel
        </Button>
        <Button
          className="flex-1"
          onClick={save}
          loading={saving}
          disabled={payment === (current ?? null)}
        >
          Save
        </Button>
      </div>
    </Sheet>
  );
}
