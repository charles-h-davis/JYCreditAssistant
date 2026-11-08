"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { Flame } from "lucide-react";
import { ChartPager, type ChartSlide } from "@/components/charts/chart-pager";
import { tickIndices, type ChartPoint } from "@/components/charts/smooth-line-chart";
import { RepaymentEditor } from "@/components/dashboard/repayment-editor";
import { AppShell } from "@/components/layout/app-shell";
import { CardSwitcher } from "@/components/layout/card-switcher";
import { TopBar } from "@/components/layout/top-bar";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { EmptyState, ErrorNote, Skeleton, StatTile } from "@/components/ui/primitives";
import { getMonthlyPayment, getRoadmap, listCardTransactions } from "@/lib/api/endpoints";
import {
  amortise,
  balanceProjection,
  monthsToLabel,
  paymentCoversInterest,
  suggestPayment,
} from "@/lib/finance/credit";
import {
  balanceSeries,
  cumulativeSpend,
  dailyNet,
} from "@/lib/finance/transactions";
import { formatMoney } from "@/lib/format";
import { useCards } from "@/lib/state/cards";
import { useSession } from "@/lib/state/session";

function dayLabel(iso: string): string {
  return String(Number(iso.slice(8, 10)));
}

/**
 * X-axis labels for the payoff projection: month names, with the year added only
 * on the first rendered tick of each year (so a 1Y+ axis reads "Feb 27, May, Aug").
 */
function projectionSeries(
  points: { month: number; balance: number }[],
  today = new Date(),
): ChartPoint[] {
  const labelled = tickIndices(points.length);
  let seenYear: number | null = null;

  return points.map((point, index) => {
    if (point.month === 0) return { label: "Now", value: point.balance };
    const date = new Date(today.getFullYear(), today.getMonth() + point.month, 1);
    let label = date.toLocaleDateString("en-GB", { month: "short" });
    if (labelled.has(index) && seenYear !== date.getFullYear()) {
      label = `${label} ${String(date.getFullYear()).slice(2)}`;
      seenYear = date.getFullYear();
    }
    return { label, value: point.balance };
  });
}

export default function DashboardPage() {
  const { userId } = useSession();
  const { selected: card, isLoading: cardsLoading, error: cardsError } = useCards();
  const [editorOpen, setEditorOpen] = useState(false);

  const cardId = card?.id;

  const { data: transactions, error: txError } = useSWR(
    cardId && userId ? `transactions:${userId}:${cardId}` : null,
    () => listCardTransactions(userId as string, cardId as string),
  );

  const { data: paymentRow } = useSWR(
    cardId && userId ? `monthly-payment:${userId}:${cardId}` : null,
    () => getMonthlyPayment(userId as string, cardId as string),
  );

  const { data: roadmap } = useSWR(userId ? `roadmap:${userId}` : null, () =>
    getRoadmap(userId as string),
  );

  if (cardsLoading) {
    return (
      <AppShell>
        <TopBar />
        <div className="mt-4 flex justify-center">
          <Skeleton className="h-8 w-44 rounded-full" />
        </div>
        <div className="mt-5 flex gap-3">
          <Skeleton className="h-24 flex-1" />
          <Skeleton className="h-24 flex-1" />
        </div>
        <Skeleton className="mt-4 h-64 w-full" />
        <div className="mt-4 flex gap-3">
          <Skeleton className="h-24 flex-1" />
          <Skeleton className="h-24 flex-1" />
        </div>
      </AppShell>
    );
  }

  if (!card) {
    return (
      <AppShell>
        <TopBar showCamera={false} />
        <div className="mt-6">
          <EmptyState
            title="No card on file yet"
            body={
              cardsError
                ? cardsError.message
                : "Add a credit card to see your balance, payoff date and spending."
            }
            action={
              <Link href="/account" className="btn btn-primary mt-3 px-6">
                Go to your account
              </Link>
            }
          />
        </div>
      </AppShell>
    );
  }

  const balance = card.current_balance;
  const apr = card.purchase_apr ?? 0;
  const storedPayment = paymentRow?.monthly_payment ?? null;
  const effectivePayment = storedPayment ?? suggestPayment(balance, apr);
  const payable = paymentCoversInterest(balance, apr, effectivePayment);
  const payoff = payable ? amortise(balance, apr, effectivePayment) : null;

  const rows = transactions ?? [];
  const balancePoints = balanceSeries(rows, balance).map((point) => ({
    label: dayLabel(point.date),
    value: point.value,
  }));
  const spentPoints = cumulativeSpend(rows).map((point) => ({
    label: dayLabel(point.date),
    value: point.value,
  }));
  const netPoints = dailyNet(rows).map((point) => ({
    label: dayLabel(point.date),
    value: point.value,
  }));
  const projectionPoints = payable
    ? projectionSeries(balanceProjection(balance, apr, effectivePayment, 96))
    : [];

  const netTotal =
    Math.round(netPoints.reduce((total, point) => total + point.value, 0) * 100) / 100;

  const latest = (points: { value: number }[]) => points.at(-1)?.value ?? 0;

  const slides: ChartSlide[] = [
    {
      key: "balance",
      title: "Balance",
      value: formatMoney(balance),
      caption: "Last 30 days",
      points: balancePoints,
    },
    {
      key: "spent",
      title: "Spent",
      value: formatMoney(latest(spentPoints)),
      caption: "Last 30 days",
      points: spentPoints,
    },
    {
      key: "payoff",
      title: "Balance to debt free",
      value: formatMoney(balance),
      caption: payable
        ? `At ${formatMoney(effectivePayment)}/month · debt free in ${monthsToLabel(
            payoff?.months ?? 0,
          )}`
        : "Raise your monthly repayment to see a debt-free date.",
      points: projectionPoints,
    },
    {
      key: "net",
      title: "Net spending",
      kind: "bars",
      value: formatMoney(netTotal),
      caption: "Daily net, last 30 days · payments shown in green",
      points: netPoints,
    },
  ];

  const streak = roadmap?.streak.current_streak ?? 0;

  return (
    <AppShell>
      <TopBar notifications={<NotificationBell />} />
      <div className="mt-4">
        <CardSwitcher />
      </div>

        {txError ? (
          <div className="mt-4">
            <ErrorNote>{txError.message}</ErrorNote>
          </div>
        ) : null}

        <div className="mt-5 flex gap-3">
          <StatTile
            label="Balance"
            value={formatMoney(balance)}
            hint={
              card.credit_limit
                ? `of ${formatMoney(card.credit_limit, { whole: true })} limit`
                : undefined
            }
          />
          <StatTile
            label="Debt Free In"
            value={payable ? monthsToLabel(payoff?.months ?? 0) : "—"}
            hint={payable ? `${formatMoney(effectivePayment)}/mo` : "Set a repayment"}
          />
        </div>

        <div className="mt-4">
          <ChartPager slides={slides} />
        </div>

        <div className="mt-4 flex gap-3">
          <button
            type="button"
            onClick={() => setEditorOpen(true)}
            className="surface flex-1 p-4 text-left transition active:scale-[0.99]"
          >
            <p className="text-[0.95rem] leading-tight text-ink-soft">Monthly Repayment</p>
            <p className="mt-1 text-2xl font-semibold tracking-tight">
              {formatMoney(effectivePayment, { whole: true })}
            </p>
            <p className="mt-1 text-xs text-muted">
              {storedPayment === null ? "Tap to set" : "Tap to adjust"}
            </p>
          </button>
          <Link
            href="/learning"
            className="surface flex-1 p-4 transition active:scale-[0.99]"
          >
            <p className="text-[0.95rem] leading-tight text-ink-soft">Learning Streak</p>
            <div className="mt-1 flex items-end justify-between">
              <p className="text-2xl font-semibold tracking-tight">{streak}d</p>
              <Flame size={22} strokeWidth={1.7} className="mb-1 text-ink-soft" aria-hidden />
            </div>
            <p className="mt-1 text-xs text-muted">
              {roadmap?.streak.active_today ? "Done today" : "Keep it going"}
            </p>
          </Link>
        </div>

      <RepaymentEditor
        card={card}
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        current={storedPayment}
      />
    </AppShell>
  );
}

