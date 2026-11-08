"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import useSWR from "swr";
import {
  Calculator,
  Check,
  ChevronRight,
  CreditCard,
  GraduationCap,
  RefreshCw,
  Scale,
  Users,
  Wallet,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { ActivityRing } from "@/components/learning/activity-ring";
import { CategorySheet } from "@/components/learning/category-sheet";
import { ErrorNote, Sheet, Skeleton } from "@/components/ui/primitives";
import { getRoadmap } from "@/lib/api/endpoints";
import type { CategoryProgress } from "@/lib/api/types";
import { completedCount } from "@/lib/learning";
import { useSession } from "@/lib/state/session";

const ICONS: Record<string, typeof Wallet> = {
  "credit-basics": CreditCard,
  "financial-arithmetic": Calculator,
  "budgeting-and-affordability": Wallet,
  "comparing-credit-options": Scale,
  "managing-repayments": GraduationCap,
};

/** Ring centres as percentages of the board (design ref: floating activity nodes). */
const POSITIONS = [
  { left: "22%", top: "13%" },
  { left: "68%", top: "31%" },
  { left: "20%", top: "50%" },
  { left: "62%", top: "68%" },
  { left: "30%", top: "86%" },
];

export default function LearningPage() {
  const { userId } = useSession();
  const [selected, setSelected] = useState<CategoryProgress | null>(null);

  const { data, error, isLoading, mutate } = useSWR(
    userId ? `roadmap:${userId}` : null,
    () => getRoadmap(userId as string),
  );

  const categories = useMemo(() => data?.categories ?? [], [data]);
  const completedCategories = categories.filter(
    (category) => completedCount(category) === category.lessons.length,
  ).length;
  const hasRecap = categories.some((category) => completedCount(category) > 0);
  const streak = data?.streak.current_streak ?? 0;

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <div className="mt-5 flex items-end justify-between">
        <h1 className="text-[2rem] leading-tight font-semibold tracking-tight">Learning</h1>
        <p className="pb-1 text-sm text-muted">
          {completedCategories}/{categories.length || 5} done · {streak}d streak
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="mt-4 h-[38rem] w-full rounded-[26px]" />
      ) : error ? (
        <div className="mt-4">
          <ErrorNote>{error.message}</ErrorNote>
        </div>
      ) : (
        <div className="relative mt-4 overflow-hidden rounded-[26px] bg-surface px-4 py-5">
          <div className="relative h-[35rem] w-full">
            {categories.map((category, index) => {
              const done = completedCount(category);
              const complete = done === category.lessons.length;
              const Icon = ICONS[category.id] ?? Wallet;
              const position = POSITIONS[index] ?? { left: "40%", top: "40%" };
              // Nodes zig-zag, so the title goes on whichever side has room.
              const labelOnRight = Number.parseFloat(position.left) < 50;

              return (
                <button
                  key={category.id}
                  type="button"
                  onClick={() => setSelected(category)}
                  style={position}
                  className="absolute grid -translate-x-1/2 -translate-y-1/2 place-items-center transition active:scale-95"
                  aria-label={`${category.title}: ${done} of ${category.lessons.length} lessons complete`}
                >
                  <span className="relative grid place-items-center">
                    <ActivityRing completed={done} total={category.lessons.length} />
                    <span
                      className={`absolute grid size-[62px] place-items-center rounded-full transition-colors ${
                        complete ? "bg-ink text-white" : "bg-white/70 text-ink-soft"
                      }`}
                    >
                      {complete ? (
                        <Check size={26} strokeWidth={2.4} aria-hidden />
                      ) : (
                        <Icon size={26} strokeWidth={1.7} aria-hidden />
                      )}
                    </span>
                    <span
                      className={`absolute top-1/2 w-[6.5rem] -translate-y-1/2 text-[0.7rem] leading-snug font-medium text-ink-soft ${
                        labelOnRight ? "left-full ml-2.5 text-left" : "right-full mr-2.5 text-right"
                      }`}
                    >
                      {category.title}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>

          <Link
            href={hasRecap ? "/learning/recap" : "/learning"}
            aria-disabled={!hasRecap}
            onClick={(event) => {
              if (!hasRecap) event.preventDefault();
            }}
            className={`absolute right-4 bottom-4 grid size-14 place-items-center rounded-full bg-white text-ink shadow-soft transition active:scale-95 ${
              hasRecap ? "" : "opacity-40"
            }`}
          >
            <RefreshCw size={22} strokeWidth={2} aria-hidden />
            <span className="sr-only">Refresh lesson: five random questions</span>
          </Link>
        </div>
      )}

      <Link
        href="/friends-feed"
        className="surface mt-4 flex items-center gap-3 px-4 py-3.5 transition active:scale-[0.99]"
      >
        <span className="grid size-10 shrink-0 place-items-center rounded-full bg-white/70 text-ink-soft">
          <Users size={20} strokeWidth={1.8} aria-hidden />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-medium text-ink">Friends feed</span>
          <span className="block text-xs text-muted">
            See what everyone else is working through
          </span>
        </span>
        <ChevronRight size={18} strokeWidth={2} aria-hidden className="shrink-0 text-ink-soft" />
      </Link>

      <Sheet
        open={selected !== null}
        onClose={() => setSelected(null)}
        title={selected?.title}
      >
        {selected ? (
          <CategorySheet category={selected} onChanged={() => void mutate()} />
        ) : null}
      </Sheet>
    </AppShell>
  );
}
