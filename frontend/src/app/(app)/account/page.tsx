"use client";

import { useState } from "react";
import { Check, LogOut, Palette, Pencil } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { CardPanel } from "@/components/account/card-panel";
import { Button } from "@/components/ui/button";
import { ErrorNote, Segmented, Skeleton } from "@/components/ui/primitives";
import { initials } from "@/lib/format";
import { useCards } from "@/lib/state/cards";
import { useSession } from "@/lib/state/session";
import { THEME_ACCENTS, THEME_MODES, useTheme } from "@/lib/state/theme";

export default function AccountPage() {
  const { displayName, email, signOut, updateDisplayName } = useSession();
  const { cards, isLoading } = useCards();
  const { mode, accent, setMode, setAccent } = useTheme();
  const [editingName, setEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState(displayName);
  const [nameError, setNameError] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  async function saveName() {
    setNameError(null);
    try {
      await updateDisplayName(nameDraft);
      setEditingName(false);
    } catch (caught) {
      setNameError(caught instanceof Error ? caught.message : "Couldn't save that name.");
    }
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <h1 className="mt-5 text-[2rem] leading-tight font-semibold tracking-tight">
        Your Account
      </h1>

      <section className="surface mt-4 flex items-center gap-3 p-4">
        <span className="grid size-12 shrink-0 place-items-center rounded-full bg-strong text-sm font-semibold text-white">
          {initials(displayName)}
        </span>
        <div className="min-w-0 flex-1">
          {editingName ? (
            <div className="flex items-center gap-2">
              <input
                className="field py-1.5"
                value={nameDraft}
                onChange={(event) => setNameDraft(event.target.value)}
                aria-label="Display name"
                autoFocus
              />
              <button
                type="button"
                onClick={saveName}
                className="shrink-0 text-sm font-medium text-accent"
              >
                Save
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => {
                setNameDraft(displayName);
                setEditingName(true);
              }}
              className="flex items-center gap-1.5"
            >
              <span className="truncate text-lg font-semibold">{displayName}</span>
              <Pencil size={14} className="text-muted" aria-hidden />
              <span className="sr-only">Edit display name</span>
            </button>
          )}
          <p className="truncate text-sm text-muted">{email || "Demo account"}</p>
        </div>
      </section>

      {nameError ? (
        <div className="mt-3">
          <ErrorNote>{nameError}</ErrorNote>
        </div>
      ) : null}

      <h2 className="mt-6 flex items-center gap-2 text-sm font-semibold tracking-wide text-muted uppercase">
        <Palette size={15} strokeWidth={2} aria-hidden />
        Appearance
      </h2>

      <section className="surface mt-2 p-4">
        <p className="text-sm font-medium text-ink">Colour scheme</p>
        <div className="mt-2">
          <Segmented options={THEME_MODES} value={mode} onChange={setMode} />
        </div>

        <p className="mt-4 text-sm font-medium text-ink">Accent</p>
        <div className="mt-2 flex items-center gap-3" role="radiogroup" aria-label="Accent colour">
          {THEME_ACCENTS.map((option) => {
            const active = accent === option.value;
            return (
              <button
                key={option.value}
                type="button"
                role="radio"
                aria-checked={active}
                aria-label={option.label}
                title={option.label}
                onClick={() => setAccent(option.value)}
                className={`grid size-10 place-items-center rounded-full transition active:scale-95 ${
                  active ? "ring-2 ring-ink ring-offset-2 ring-offset-surface" : ""
                }`}
                style={{ backgroundColor: option.swatch }}
              >
                {active ? (
                  <Check size={15} strokeWidth={3} className="text-white" aria-hidden />
                ) : null}
              </button>
            );
          })}
        </div>
        <p className="mt-3 text-xs text-muted">Saved on this device.</p>
      </section>

      <h2 className="mt-6 text-sm font-semibold tracking-wide text-muted uppercase">
        Card details
      </h2>

      <div className="mt-2 space-y-3">
        {isLoading ? (
          <>
            <Skeleton className="h-40 w-full" />
            <Skeleton className="h-40 w-full" />
          </>
        ) : cards.length === 0 ? (
          <p className="text-sm text-muted">No cards stored for this account yet.</p>
        ) : (
          cards.map((card) => <CardPanel key={card.id} card={card} />)
        )}
      </div>

      <div className="mt-6">
        <Button
          variant="secondary"
          className="w-full"
          loading={signingOut}
          onClick={async () => {
            setSigningOut(true);
            await signOut();
          }}
        >
          <LogOut size={18} aria-hidden />
          Log out
        </Button>
      </div>
    </AppShell>
  );
}
