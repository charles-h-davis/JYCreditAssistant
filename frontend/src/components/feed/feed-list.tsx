"use client";

import type { FeedEntry } from "@/lib/api/types";
import { formatRelativeTime, initials } from "@/lib/format";

/**
 * The friends feed list: avatar, who did what, and how long ago — newest first.
 * The caller's own rows get the indigo avatar so their activity stands out.
 */
export function FeedList({ entries }: { entries: FeedEntry[] }) {
  return (
    <ul className="space-y-2.5">
      {entries.map((entry) => (
        <li key={entry.id} className="surface flex items-start gap-3 p-3.5">
          <span
            aria-hidden
            className={`grid size-10 shrink-0 place-items-center rounded-full text-[0.8rem] font-semibold ${
              entry.is_self ? "bg-accent-soft text-ink" : "bg-surface-strong text-ink-soft"
            }`}
          >
            {initials(entry.actor)}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm leading-snug">
              <span className="font-semibold text-ink">{entry.actor}</span>{" "}
              <span className="text-ink-soft">{entry.action}</span>
            </p>
            {entry.detail ? (
              <p className="mt-0.5 text-xs text-muted">{entry.detail}</p>
            ) : null}
          </div>
          <span className="shrink-0 pt-0.5 text-xs text-muted">
            {formatRelativeTime(entry.occurred_at)}
          </span>
        </li>
      ))}
    </ul>
  );
}
