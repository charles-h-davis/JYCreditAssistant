"use client";

import { useState } from "react";
import useSWR, { mutate as mutateKeys } from "swr";
import { Bell } from "lucide-react";
import { NotificationSheet } from "@/components/notifications/notification-sheet";
import { IconButton } from "@/components/ui/primitives";
import {
  deletePurchasePlan,
  dismissPurchaseMatch,
  getNotifications,
} from "@/lib/api/endpoints";
import type { PurchaseMatch } from "@/lib/api/types";
import { useSession } from "@/lib/state/session";

/**
 * How often the bell re-checks while the dashboard is open. Short enough that a
 * transaction inserted behind the scenes (a live demo, a Plaid sync) badges up on
 * its own; SWR pauses polling while the tab is hidden.
 */
const REFRESH_MS = 15_000;

/**
 * The dashboard bell: a badge with the number of suspected matches, and a sheet
 * listing them with a tick / cross per row.
 */
export function NotificationBell() {
  const { userId } = useSession();
  const [open, setOpen] = useState(false);

  const { data, error, isLoading, mutate: refresh } = useSWR(
    userId ? `notifications:${userId}` : null,
    () => getNotifications(userId as string),
    { refreshInterval: REFRESH_MS },
  );

  const matches = data?.matches ?? [];
  const count = data?.count ?? 0;

  /** ✓ it happened — deleting the plan is the answer, so the match goes with it. */
  async function accept(match: PurchaseMatch) {
    if (!userId) return;
    await deletePurchasePlan(userId, match.plan_id);
    await Promise.all([refresh(), mutateKeys(`purchase-plans:${userId}`)]);
  }

  /** ✗ not that — keep the plan and remember the pair so it stops asking. */
  async function dismiss(match: PurchaseMatch) {
    if (!userId) return;
    await dismissPurchaseMatch({
      user_id: userId,
      plan_id: match.plan_id,
      transaction_id: match.transaction_id,
    });
    await refresh();
  }

  return (
    <>
      <IconButton
        label={count > 0 ? `Notifications, ${count} new` : "Notifications"}
        onClick={() => setOpen(true)}
        className="relative"
      >
        <Bell size={20} strokeWidth={1.9} aria-hidden />
        {count > 0 ? (
          <span
            aria-hidden
            className="absolute -top-0.5 -right-0.5 grid h-[1.15rem] min-w-[1.15rem] place-items-center rounded-full bg-accent px-1 text-[0.65rem] font-semibold text-white"
          >
            {count > 9 ? "9+" : count}
          </span>
        ) : null}
      </IconButton>

      <NotificationSheet
        open={open}
        onClose={() => setOpen(false)}
        matches={matches}
        loading={isLoading}
        error={error ? (error as Error).message : null}
        onAccept={accept}
        onDismiss={dismiss}
      />
    </>
  );
}
