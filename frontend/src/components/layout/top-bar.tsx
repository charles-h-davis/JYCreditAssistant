"use client";

import Link from "next/link";
import { Camera } from "lucide-react";
import { IconButton } from "@/components/ui/primitives";
import { initials } from "@/lib/format";
import { useSession } from "@/lib/state/session";

/**
 * The top row from the design refs: profile avatar on the left, the "check a
 * purchase" camera on the right. There is no "+" button — the bottom nav's
 * Check Purchase tab is the single way into that flow.
 */
export function TopBar({
  showProfile = true,
  showCamera = true,
}: {
  showProfile?: boolean;
  showCamera?: boolean;
}) {
  const { displayName } = useSession();

  return (
    <header className="flex items-center justify-between pt-[max(0.75rem,env(safe-area-inset-top))]">
      {showProfile ? (
        <Link
          href="/account"
          aria-label="Your account"
          className="grid size-11 place-items-center rounded-full bg-surface-strong text-sm font-semibold text-ink-soft transition active:scale-95"
        >
          {initials(displayName)}
        </Link>
      ) : (
        <span aria-hidden className="size-11" />
      )}

      {showCamera ? (
        <Link href="/purchase/photo" aria-label="Check a purchase with a photo">
          <IconButton label="Check a purchase with a photo" tabIndex={-1}>
            <Camera size={20} strokeWidth={1.9} aria-hidden />
          </IconButton>
        </Link>
      ) : (
        <span aria-hidden className="size-11" />
      )}
    </header>
  );
}
