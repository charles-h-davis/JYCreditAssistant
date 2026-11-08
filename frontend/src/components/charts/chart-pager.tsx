"use client";

import { motion } from "motion/react";
import { useCallback, useState } from "react";
import { BarChart, type BarPoint } from "@/components/charts/bar-chart";
import { SmoothLineChart, type ChartPoint } from "@/components/charts/smooth-line-chart";
import { swipedLeft, swipedRight, type PanInfoLike } from "@/lib/pan-info";

export interface ChartSlide {
  key: string;
  title: string;
  value: string;
  caption?: string;
  /** `bars` renders the non-cumulative bar chart; everything else is a line. */
  kind?: "line" | "bars";
  points: ChartPoint[] | BarPoint[];
}

/**
 * Swipeable chart card from the dashboard design ref. The drag handler stops
 * pointer events from reaching the page-level card swipe, so the two gestures
 * never fight: dragging here pages charts, dragging elsewhere switches cards.
 */
export function ChartPager({ slides }: { slides: ChartSlide[] }) {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const total = slides.length;
  const current = slides[Math.min(index, total - 1)];

  const go = useCallback(
    (next: number, dir: number) => {
      if (total === 0) return;
      setDirection(dir);
      setIndex(((next % total) + total) % total);
    },
    [total],
  );

  if (!current) {
    return <div className="surface h-56" />;
  }

  return (
    <section
      className="surface overflow-hidden p-4"
      data-testid="chart-pager"
      aria-roledescription="carousel"
      aria-label={`${current.title} chart, ${index + 1} of ${total}`}
    >
      <motion.div
        key={current.key}
        initial={{ opacity: 0, x: direction * 26 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        drag="x"
        dragDirectionLock
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.12}
        onDragEnd={(_event: unknown, info: PanInfoLike) => {
          if (swipedLeft(info)) go(index + 1, 1);
          else if (swipedRight(info)) go(index - 1, -1);
        }}
        className="touch-pan-y"
      >
        <p className="text-[0.95rem] text-ink-soft">{current.title}</p>
        <p className="mt-0.5 text-2xl font-semibold tracking-tight text-ink">
          {current.value}
        </p>
        <div className="mt-2">
          {current.kind === "bars" ? (
            <BarChart
              points={current.points as BarPoint[]}
              ariaLabel={`${current.title}: ${current.value}`}
              height={186}
            />
          ) : (
            <SmoothLineChart
              points={current.points as ChartPoint[]}
              ariaLabel={`${current.title}: ${current.value}`}
              height={186}
            />
          )}
        </div>
        {current.caption ? (
          <p className="mt-1 text-xs text-muted">{current.caption}</p>
        ) : null}
      </motion.div>

      <div className="mt-1 flex items-center justify-center gap-1.5" role="tablist">
        {slides.map((slide, slideIndex) => {
          const active = slideIndex === index;
          return (
            <button
              key={slide.key}
              type="button"
              role="tab"
              aria-selected={active}
              aria-label={slide.title}
              onClick={() => go(slideIndex, slideIndex > index ? 1 : -1)}
              className={`h-2 rounded-full transition-all duration-200 ${
                active ? "w-6 bg-ink-soft/70" : "w-2 bg-surface-strong"
              }`}
            />
          );
        })}
      </div>
    </section>
  );
}
