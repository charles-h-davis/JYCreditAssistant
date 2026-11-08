"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { UserPlus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNote, Sheet, Skeleton } from "@/components/ui/primitives";
import type { Friend } from "@/lib/api/types";
import { initials } from "@/lib/format";

/**
 * Bottom sheet behind the Friends / Add friend buttons on the feed: the user's
 * friend list plus an add-by-email row. The feed page owns the query, this only
 * renders it and reports the two actions.
 */
export function FriendsSheet({
  open,
  focusEmail = false,
  onClose,
  friends,
  loading,
  error,
  onAdd,
  onRemove,
}: {
  open: boolean;
  focusEmail?: boolean;
  onClose: () => void;
  friends: Friend[];
  loading: boolean;
  error: string | null;
  onAdd: (email: string) => Promise<void>;
  onRemove: (friendId: string) => Promise<void>;
}) {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Opened from "Add friend": put the cursor straight in the email field.
  useEffect(() => {
    if (open && focusEmail) inputRef.current?.focus();
  }, [open, focusEmail]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = email.trim();
    if (!value || busy) return;
    setBusy(true);
    setFormError(null);
    try {
      await onAdd(value);
      setEmail("");
    } catch (caught) {
      setFormError(caught instanceof Error ? caught.message : "Couldn't add that friend.");
    } finally {
      setBusy(false);
    }
  }

  async function remove(friendId: string) {
    if (removing) return;
    setRemoving(friendId);
    setFormError(null);
    try {
      await onRemove(friendId);
    } catch (caught) {
      setFormError(caught instanceof Error ? caught.message : "Couldn't remove that friend.");
    } finally {
      setRemoving(null);
    }
  }

  return (
    <Sheet open={open} onClose={onClose} title="Friends">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-xl font-semibold tracking-tight">Friends</h2>
        <p className="text-xs text-muted">
          {friends.length} {friends.length === 1 ? "person" : "people"}
        </p>
      </div>

      <div className="mt-3 max-h-[52vh] overflow-y-auto">
        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : error ? (
          <ErrorNote>{error}</ErrorNote>
        ) : friends.length === 0 ? (
          <EmptyState
            title="No friends yet"
            body="Add someone by email below and their activity shows up in your feed."
          />
        ) : (
          <ul className="space-y-2">
            {friends.map((friend) => (
              <li
                key={friend.id}
                className="flex items-center gap-3 rounded-2xl bg-surface px-3.5 py-3"
              >
                <span
                  aria-hidden
                  className="grid size-10 shrink-0 place-items-center rounded-full bg-surface-strong text-[0.8rem] font-semibold text-ink-soft"
                >
                  {initials(friend.friend_name)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{friend.friend_name}</p>
                  <p className="truncate text-xs text-muted">{friend.friend_email}</p>
                </div>
                <button
                  type="button"
                  onClick={() => void remove(friend.id)}
                  disabled={removing === friend.id}
                  aria-label={`Remove ${friend.friend_name}`}
                  className="grid size-9 shrink-0 place-items-center rounded-full text-ink-soft transition active:scale-95 disabled:opacity-50"
                >
                  <X size={16} strokeWidth={2.2} aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form onSubmit={submit} className="mt-4 border-t border-surface-strong pt-4">
        <label htmlFor="friend-email" className="text-xs text-muted">
          Add a friend by email
        </label>
        <div className="mt-1.5 flex gap-2">
          <input
            id="friend-email"
            ref={inputRef}
            type="email"
            inputMode="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="friend@example.com"
            className="min-w-0 flex-1 rounded-2xl bg-surface px-4 py-3 text-sm outline-none placeholder:text-muted focus-visible:ring-2 focus-visible:ring-accent"
          />
          <Button type="submit" loading={busy} disabled={!email.trim()}>
            <UserPlus size={16} strokeWidth={2} aria-hidden />
            Add
          </Button>
        </div>
        {formError ? (
          <div className="mt-2">
            <ErrorNote>{formError}</ErrorNote>
          </div>
        ) : null}
      </form>
    </Sheet>
  );
}
