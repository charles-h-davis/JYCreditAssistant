"use client";

import { useState } from "react";
import useSWR from "swr";
import { Pencil } from "lucide-react";
import { RepaymentEditor } from "@/components/dashboard/repayment-editor";
import { getMonthlyPayment } from "@/lib/api/endpoints";
import type { CreditCard } from "@/lib/api/types";
import { formatMoney, formatPercent } from "@/lib/format";
import { useSession } from "@/lib/state/session";

/** One card's details plus its editable monthly repayment. */
export function CardPanel({ card }: { card: CreditCard }) {
  const { userId } = useSession();
  const [editorOpen, setEditorOpen] = useState(false);
  const { data } = useSWR(userId ? `monthly-payment:${userId}:${card.id}` : null, () =>
    getMonthlyPayment(userId as string, card.id),
  );
  const payment = data?.monthly_payment ?? null;

  return (
    <section className="surface p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-medium">{card.nickname}</p>
          <p className="text-sm text-muted">
            {card.issuer} ···· {card.last_four}
            {card.is_secured ? " · secured" : ""}
          </p>
        </div>
        <p className="shrink-0 text-lg font-semibold tabular-nums">
          {formatMoney(card.current_balance)}
        </p>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
        <Row
          label="Credit limit"
          value={card.credit_limit ? formatMoney(card.credit_limit) : "—"}
        />
        <Row label="APR" value={card.purchase_apr ? formatPercent(card.purchase_apr) : "—"} />
        <Row
          label="Statement closes"
          value={card.closing_day ? `Day ${card.closing_day}` : "—"}
        />
        <Row
          label="Payment due"
          value={card.statement_day ? `Day ${card.statement_day}` : "—"}
        />
      </dl>

      <button
        type="button"
        onClick={() => setEditorOpen(true)}
        className="mt-3 flex w-full items-center justify-between rounded-2xl bg-surface-strong/60 px-3.5 py-2.5 text-left"
      >
        <span className="text-sm text-ink-soft">Monthly repayment</span>
        <span className="flex items-center gap-2">
          <span className="text-sm font-semibold">
            {payment === null ? "Not set" : formatMoney(payment, { whole: true })}
          </span>
          <Pencil size={13} className="text-muted" aria-hidden />
        </span>
      </button>

      <RepaymentEditor
        card={card}
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        current={payment}
      />
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="font-medium tabular-nums">{value}</dd>
    </div>
  );
}
