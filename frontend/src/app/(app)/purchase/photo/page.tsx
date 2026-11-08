"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Camera, ImagePlus, X } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { ErrorNote } from "@/components/ui/primitives";
import { extractProduct } from "@/lib/api/endpoints";
import { useCards } from "@/lib/state/cards";
import { usePurchaseDraft } from "@/lib/state/purchase-draft";

/**
 * Photo step: snap a price tag or attach a screenshot, then let Gemini read the
 * product name and price. Both inputs are separate so iOS offers the camera for
 * one and the photo library for the other.
 */
export default function PurchasePhotoPage() {
  const router = useRouter();
  const { startDraft } = usePurchaseDraft();
  const { selected: card } = useCards();
  const cameraInput = useRef<HTMLInputElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function onPick(picked: File | null) {
    if (!picked) return;
    setError(null);
    setFile(picked);
    setPreview(URL.createObjectURL(picked));
  }

  async function analyse() {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const result = await extractProduct(file);
      startDraft({
        productName: result.product_name ?? "",
        price: result.price ?? 0,
        source: "photo",
        imagePreview: preview,
        extractionNote:
          result.product_name || result.price
            ? "Filled in from your photo — check the details before continuing."
            : "We couldn't read that photo. Enter the details by hand.",
        cardId: card?.id ?? null,
      });
      router.push("/purchase/details");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Couldn't read that photo. Enter the details manually instead.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <div className="mt-5 flex items-start justify-between gap-3">
        <h1 className="text-[1.9rem] leading-tight font-semibold tracking-tight">
          Check a purchase
        </h1>
        <button
          type="button"
          onClick={() => router.push("/purchase")}
          aria-label="Close"
          className="grid size-10 shrink-0 place-items-center rounded-full bg-surface-strong"
        >
          <X size={18} strokeWidth={2.2} aria-hidden />
        </button>
      </div>
      <p className="mt-1 text-sm text-ink-soft">
        Take a photo of a price tag or attach a screenshot
      </p>

      <button
        type="button"
        onClick={() => cameraInput.current?.click()}
        className="surface-strong relative mt-4 grid h-[22rem] w-full place-items-center overflow-hidden"
      >
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={preview} alt="Chosen price tag" className="h-full w-full object-cover" />
        ) : (
          <span className="flex flex-col items-center gap-3 text-ink-soft">
            <Camera size={40} strokeWidth={1.5} aria-hidden />
            <span className="text-sm">Tap to use the camera</span>
          </span>
        )}
        <span className="absolute bottom-5 left-1/2 grid size-12 -translate-x-1/2 place-items-center rounded-full bg-white shadow-soft">
          <span className="size-7 rounded-full bg-surface-strong" />
          <span className="sr-only">Take photo</span>
        </span>
      </button>

      <div className="mt-3 flex items-center justify-center gap-4">
        <button
          type="button"
          onClick={() => fileInput.current?.click()}
          className="flex items-center gap-1.5 text-sm text-ink-soft"
        >
          <ImagePlus size={16} aria-hidden />
          Attach a screenshot
        </button>
      </div>

      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={(event) => onPick(event.target.files?.[0] ?? null)}
      />
      <input
        ref={fileInput}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/heic,image/heif"
        className="sr-only"
        onChange={(event) => onPick(event.target.files?.[0] ?? null)}
      />

      {error ? (
        <div className="mt-4">
          <ErrorNote>{error}</ErrorNote>
        </div>
      ) : null}

      <div className="mt-5 space-y-3">
        <Button
          className="w-full"
          onClick={analyse}
          loading={busy}
          disabled={!file}
        >
          {file ? "Read the price" : "Choose a photo first"}
        </Button>
        <Button
          variant="secondary"
          className="w-full"
          onClick={() => router.push("/purchase/details")}
        >
          Enter details manually
        </Button>
      </div>
    </AppShell>
  );
}
