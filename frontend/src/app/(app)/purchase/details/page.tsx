"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { ErrorNote } from "@/components/ui/primitives";
import { useCards } from "@/lib/state/cards";
import { usePurchaseDraft } from "@/lib/state/purchase-draft";

/** Details step: edit what the photo produced, or type it in from scratch. */
export default function PurchaseDetailsPage() {
  const router = useRouter();
  const { draft, startDraft, updateDraft } = usePurchaseDraft();
  const { selected: card } = useCards();

  const [name, setName] = useState(draft?.productName ?? "");
  const [price, setPrice] = useState(draft?.price ? String(draft.price) : "");
  const [error, setError] = useState<string | null>(null);

  const parsedPrice = Number.parseFloat(price);
  const invalid = !Number.isFinite(parsedPrice) || parsedPrice <= 0;

  function confirm(event: React.FormEvent) {
    event.preventDefault();
    if (invalid) {
      setError("Enter a price greater than zero.");
      return;
    }
    const payload = {
      productName: name.trim() || "This purchase",
      price: Math.round(parsedPrice * 100) / 100,
      source: draft?.source ?? ("manual" as const),
      imagePreview: draft?.imagePreview ?? null,
      extractionNote: draft?.extractionNote ?? null,
      // Pin the card the flow started on so the cost screen can't drift to another.
      cardId: draft?.cardId ?? card?.id ?? null,
    };
    if (draft) updateDraft(payload);
    else startDraft(payload);
    router.push("/purchase/plan");
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <h1 className="mt-5 text-[1.75rem] leading-tight font-semibold tracking-tight">
        Confirm Purchase Details
      </h1>

      {draft?.extractionNote ? (
        <p className="mt-2 rounded-2xl bg-surface px-4 py-2.5 text-sm text-ink-soft">
          {draft.extractionNote}
        </p>
      ) : null}

      <form onSubmit={confirm} className="mt-5 flex flex-1 flex-col">
        <label className="text-[1.05rem] font-medium" htmlFor="product-name">
          Name of product
        </label>
        <input
          id="product-name"
          className="field mt-2"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="H&M Grey Suit"
          autoComplete="off"
        />

        <label className="mt-5 text-[1.05rem] font-medium" htmlFor="product-price">
          Current Price
        </label>
        <div className="mt-2 flex items-center gap-1 rounded-2xl border border-ink-soft bg-elevated px-4 py-3">
          <span className="text-2xl text-muted">£</span>
          <input
            id="product-price"
            inputMode="decimal"
            className="w-full bg-transparent text-[1.9rem] font-semibold outline-none"
            value={price}
            onChange={(event) => setPrice(event.target.value.replace(/[^0-9.]/g, ""))}
            placeholder="22.34"
          />
        </div>

        {error ? (
          <div className="mt-3">
            <ErrorNote>{error}</ErrorNote>
          </div>
        ) : null}

        <div className="mt-auto pt-8">
          <Button type="submit" className="w-full" disabled={invalid}>
            Confirm
          </Button>
        </div>
      </form>
    </AppShell>
  );
}
