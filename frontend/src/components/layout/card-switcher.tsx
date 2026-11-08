"use client";

import { motion } from "motion/react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useCards } from "@/lib/state/cards";

/**
 * Card carousel header from the design refs: shy pills either side of the card
 * name. Tapping a pill switches card; the parent page also accepts a horizontal
 * swipe for the same action.
 */
export function CardSwitcher() {
  const { cards, selected, selectedIndex, nextCard, previousCard, selectCard } = useCards();

  if (cards.length === 0 || !selected) {
    return (
      <div className="flex justify-center">
        <div className="h-8 w-40 animate-pulse rounded-full bg-surface" />
      </div>
    );
  }

  const multi = cards.length > 1;

  return (
    <div className="flex items-center justify-center gap-2">
      <button
        type="button"
        onClick={previousCard}
        disabled={!multi}
        aria-label="Previous card"
        className="grid h-7 w-10 place-items-center rounded-full bg-surface text-ink-soft/70 transition active:scale-95 disabled:opacity-40"
      >
        <ChevronLeft size={15} strokeWidth={2.2} aria-hidden />
      </button>

      <div className="relative min-w-[9.5rem] overflow-hidden rounded-full bg-surface px-4 py-1.5 text-center">
        <motion.span
          key={selected.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.18 }}
          className="block truncate text-sm font-medium text-ink"
        >
          {selected.nickname}
        </motion.span>
      </div>

      <button
        type="button"
        onClick={nextCard}
        disabled={!multi}
        aria-label="Next card"
        className="grid h-7 w-10 place-items-center rounded-full bg-surface text-ink-soft/70 transition active:scale-95 disabled:opacity-40"
      >
        <ChevronRight size={15} strokeWidth={2.2} aria-hidden />
      </button>

      {multi ? (
        <div className="sr-only" aria-live="polite">
          {`Card ${selectedIndex + 1} of ${cards.length}`}
        </div>
      ) : null}

      <div className="sr-only">
        {cards.map((card, index) => (
          <button key={card.id} type="button" onClick={() => selectCard(index)}>
            {card.nickname}
          </button>
        ))}
      </div>
    </div>
  );
}
