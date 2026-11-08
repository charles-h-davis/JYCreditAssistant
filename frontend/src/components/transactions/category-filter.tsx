"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { CardTransaction } from "@/lib/api/types";
import { categoriesFor, categoryLabel } from "@/lib/finance/transactions";

/** Distance in px before a press counts as a drag rather than a tap. */
const DRAG_THRESHOLD = 4;
/** Width of the fade at each end of the strip. */
const FADE = 22;

/**
 * Horizontally scrollable filter strip from the transactions design ref.
 *
 * It scrolls in place rather than wrapping, so the month summary above never
 * moves. Three ways to reach the chips off-screen: drag it with the mouse, scroll
 * the wheel over it (translated to horizontal), or swipe on a touch screen. Edge
 * fades show there is more to the left or right.
 */
export function CategoryFilter({
  selected,
  onSelect,
  visibleTransactions,
}: {
  selected: string | null;
  onSelect: (category: string | null) => void;
  visibleTransactions: CardTransaction[];
}) {
  const categories = categoriesFor(visibleTransactions);
  const categoryKey = categories.join("|");
  const scroller = useRef<HTMLDivElement>(null);
  const drag = useRef({ active: false, startX: 0, startScroll: 0, moved: 0 });
  const [edges, setEdges] = useState({ atStart: true, atEnd: true });

  const updateEdges = useCallback(() => {
    const element = scroller.current;
    if (!element) return;
    const atStart = element.scrollLeft <= 2;
    const atEnd = element.scrollLeft + element.clientWidth >= element.scrollWidth - 2;
    setEdges((current) =>
      current.atStart === atStart && current.atEnd === atEnd
        ? current
        : { atStart, atEnd },
    );
  }, []);

  useEffect(() => {
    const element = scroller.current;
    updateEdges();
    if (!element) return;

    // React's onWheel is passive, so preventDefault needs a native listener; this
    // turns a vertical wheel over the strip into horizontal scrolling.
    const onWheel = (event: WheelEvent) => {
      if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
      if (element.scrollWidth <= element.clientWidth) return;
      event.preventDefault();
      element.scrollLeft += event.deltaY;
    };

    element.addEventListener("wheel", onWheel, { passive: false });
    const observer = new ResizeObserver(updateEdges);
    observer.observe(element);
    return () => {
      element.removeEventListener("wheel", onWheel);
      observer.disconnect();
    };
  }, [updateEdges, categoryKey]);

  function startDrag(event: React.PointerEvent<HTMLDivElement>) {
    // Touch already scrolls natively; dragging is for mice and pens.
    if (event.pointerType === "touch" || event.button !== 0) return;
    const element = scroller.current;
    if (!element) return;
    drag.current = {
      active: true,
      startX: event.clientX,
      startScroll: element.scrollLeft,
      moved: 0,
    };
  }

  function moveDrag(event: React.PointerEvent<HTMLDivElement>) {
    const element = scroller.current;
    if (!element || !drag.current.active) return;
    const offset = event.clientX - drag.current.startX;
    drag.current.moved = Math.max(drag.current.moved, Math.abs(offset));
    if (drag.current.moved > DRAG_THRESHOLD) {
      if (!element.hasPointerCapture(event.pointerId)) {
        element.setPointerCapture(event.pointerId);
      }
      element.scrollLeft = drag.current.startScroll - offset;
    }
  }

  function endDrag() {
    drag.current.active = false;
  }

  /** Swallow the click that ends a drag so it doesn't select a chip. */
  function suppressClickAfterDrag(event: React.MouseEvent<HTMLDivElement>) {
    if (drag.current.moved > DRAG_THRESHOLD) {
      event.preventDefault();
      event.stopPropagation();
    }
    drag.current.moved = 0;
  }

  const fadeStart = edges.atStart ? "black 0" : `transparent 0, black ${FADE}px`;
  const fadeEnd = edges.atEnd
    ? "black 100%"
    : `black calc(100% - ${FADE}px), transparent 100%`;
  const mask = `linear-gradient(to right, ${fadeStart}, ${fadeEnd})`;

  return (
    <div
      ref={scroller}
      className="no-scrollbar -mx-4 cursor-grab touch-pan-x overflow-x-auto px-4 pb-1 select-none active:cursor-grabbing"
      style={{ maskImage: mask, WebkitMaskImage: mask }}
      role="group"
      aria-label="Filter by category"
      onScroll={updateEdges}
      onPointerDown={startDrag}
      onPointerMove={moveDrag}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onPointerLeave={endDrag}
      onClickCapture={suppressClickAfterDrag}
    >
      <div className="flex w-max gap-2">
        <Chip active={selected === null} onClick={() => onSelect(null)}>
          All
        </Chip>
        {categories.map((category) => (
          <Chip
            key={category}
            active={selected === category}
            onClick={() => onSelect(selected === category ? null : category)}
          >
            {categoryLabel(category)}
          </Chip>
        ))}
      </div>
    </div>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm whitespace-nowrap transition ${
        active ? "bg-strong text-white" : "bg-surface-strong/70 text-ink-soft"
      }`}
    >
      {children}
    </button>
  );
}
