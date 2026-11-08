"use client";

import { motion } from "motion/react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { PanInfoLike } from "@/lib/pan-info";

/* --- buttons --------------------------------------------------------------- */

type IconButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  children: ReactNode;
  tone?: "soft" | "ink";
};

/** Round 44px control used in the top bar and card switcher (design refs: 1, 3). */
export function IconButton({
  label,
  children,
  tone = "soft",
  className = "",
  ...rest
}: IconButtonProps) {
  const toneClass =
    tone === "ink" ? "bg-ink text-white" : "bg-surface-strong text-ink";
  return (
    <button
      type="button"
      aria-label={label}
      className={`grid size-11 shrink-0 place-items-center rounded-full transition active:scale-95 ${toneClass} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

/* --- tiles ----------------------------------------------------------------- */

export function StatTile({
  label,
  value,
  hint,
  trailing,
  className = "",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  trailing?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`surface flex-1 p-4 ${className}`}>
      <p className="text-[0.95rem] leading-tight text-ink-soft">{label}</p>
      <div className="mt-1 flex items-end justify-between gap-2">
        <p className="text-2xl leading-tight font-semibold tracking-tight text-ink">
          {value}
        </p>
        {trailing}
      </div>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </div>
  );
}

/* --- states ---------------------------------------------------------------- */

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-surface-strong/70 ${className}`} />;
}

export function ErrorNote({
  children,
  action,
}: {
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 rounded-2xl bg-[#fdecea] px-4 py-3 text-sm text-danger">
      <span className="mt-0.5 shrink-0" aria-hidden>
        !
      </span>
      <div className="flex-1">
        <p>{children}</p>
        {action ? <div className="mt-2">{action}</div> : null}
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  body,
  action,
}: {
  title: string;
  body?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-3xl bg-surface/60 px-6 py-10 text-center">
      <p className="font-medium text-ink">{title}</p>
      {body ? <p className="text-sm text-muted">{body}</p> : null}
      {action}
    </div>
  );
}

/* --- bottom sheet ---------------------------------------------------------- */

export function Sheet({
  open,
  onClose,
  children,
  title,
}: {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <motion.button
        type="button"
        aria-label="Close"
        onClick={onClose}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.18 }}
        className="absolute inset-0 bg-ink/25 backdrop-blur-[2px]"
      />
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 380, damping: 34 }}
        drag="y"
        dragConstraints={{ top: 0, bottom: 0 }}
        dragElastic={{ top: 0, bottom: 0.4 }}
        onDragEnd={(_event: unknown, info: PanInfoLike) => {
          if (info.offset.y > 110 || info.velocity.y > 600) onClose();
        }}
        className="relative z-10 w-full max-w-[430px] rounded-t-[26px] bg-white px-5 pt-3 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-lift"
      >
        <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-surface-strong" />
        {children}
      </motion.div>
    </div>
  );
}

/* --- segmented control ----------------------------------------------------- */

export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="flex rounded-2xl bg-surface p-1" role="tablist">
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(option.value)}
            className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition ${
              active ? "bg-white text-ink shadow-soft" : "text-muted"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
