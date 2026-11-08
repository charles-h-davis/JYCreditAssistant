"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { UserPlus, Users, X } from "lucide-react";
import { FeedList } from "@/components/feed/feed-list";
import { FriendsSheet } from "@/components/feed/friends-sheet";
import { ErrorNote, Skeleton } from "@/components/ui/primitives";
import {
  addFriend,
  getFriendsFeed,
  listFriends,
  removeFriend,
} from "@/lib/api/endpoints";
import { useSession } from "@/lib/state/session";

/** How many entries the feed asks for (the API caps at 40). */
const FEED_LIMIT = 12;

/**
 * Full-screen friends feed, opened from the Learning tab. Like the lesson
 * runner there is no bottom nav — the X in the corner goes back to Learning.
 * The friends list and add-by-email live in a bottom sheet from the two pills.
 */
export default function FriendsFeedPage() {
  const router = useRouter();
  const { userId } = useSession();
  const [sheet, setSheet] = useState<{ open: boolean; focusEmail: boolean }>({
    open: false,
    focusEmail: false,
  });

  const { data, error, isLoading } = useSWR(userId ? `feed:${userId}` : null, () =>
    getFriendsFeed(userId as string, FEED_LIMIT),
  );

  const {
    data: friendData,
    error: friendError,
    isLoading: friendsLoading,
    mutate: mutateFriends,
  } = useSWR(userId ? `friends:${userId}` : null, () => listFriends(userId as string));

  const entries = data?.entries ?? [];
  const friends = friendData ?? [];

  async function handleAdd(email: string) {
    if (!userId) return;
    await addFriend({ user_id: userId, email });
    await mutateFriends();
  }

  async function handleRemove(friendId: string) {
    if (!userId) return;
    await removeFriend(userId, friendId);
    await mutateFriends();
  }

  return (
    <main className="app-column flex min-h-dvh flex-col bg-page px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => router.push("/learning")}
          aria-label="Back to learning"
          className="grid size-11 shrink-0 place-items-center rounded-full bg-surface-strong text-ink transition active:scale-95"
        >
          <X size={20} strokeWidth={2.2} aria-hidden />
        </button>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setSheet({ open: true, focusEmail: false })}
            className="flex h-11 items-center gap-1.5 rounded-full bg-surface-strong px-3.5 text-sm font-medium text-ink transition active:scale-95"
          >
            <Users size={17} strokeWidth={1.9} aria-hidden />
            Friends
            {friends.length > 0 ? (
              <span className="text-ink-soft">· {friends.length}</span>
            ) : null}
          </button>
          <button
            type="button"
            onClick={() => setSheet({ open: true, focusEmail: true })}
            aria-label="Add a friend"
            className="grid size-11 place-items-center rounded-full bg-surface-strong text-ink transition active:scale-95"
          >
            <UserPlus size={19} strokeWidth={1.9} aria-hidden />
          </button>
        </div>
      </div>

      <div className="mt-5">
        <h1 className="text-[1.9rem] leading-tight font-semibold tracking-tight">
          Friends feed
        </h1>
        <p className="mt-1 text-sm text-ink-soft">
          {entries.length
            ? `What your friends are working through — latest ${entries.length}`
            : "What your friends are working through — and your own lesson activity."}
        </p>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto pb-2">
        {isLoading ? (
          <div className="space-y-2.5">
            <Skeleton className="h-[4.25rem] w-full" />
            <Skeleton className="h-[4.25rem] w-full" />
            <Skeleton className="h-[4.25rem] w-full" />
            <Skeleton className="h-[4.25rem] w-full" />
            <Skeleton className="h-[4.25rem] w-full" />
          </div>
        ) : error ? (
          <ErrorNote>{error.message}</ErrorNote>
        ) : entries.length === 0 ? (
          <p className="text-sm text-muted">
            No activity yet. Add a friend or finish a lesson and it shows up here.
          </p>
        ) : (
          <FeedList entries={entries} />
        )}
      </div>

      <FriendsSheet
        open={sheet.open}
        focusEmail={sheet.focusEmail}
        onClose={() => setSheet({ open: false, focusEmail: false })}
        friends={friends}
        loading={friendsLoading}
        error={friendError ? (friendError as Error).message : null}
        onAdd={handleAdd}
        onRemove={handleRemove}
      />
    </main>
  );
}

