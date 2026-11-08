"use client";

import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  children: ReactNode;
};

/** Shared button — 52px tall, 16px radius, matches every CTA in the design refs. */
export function Button({
  variant = "primary",
  loading = false,
  className = "",
  children,
  disabled,
  ...rest
}: ButtonProps) {
  const variantClass =
    variant === "primary"
      ? "btn-primary"
      : variant === "secondary"
        ? "btn-secondary"
        : "btn-ghost";

  return (
    <button
      type="button"
      className={`btn ${variantClass} ${className} ${
        disabled || loading ? "opacity-60" : ""
      }`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? (
        <span
          aria-hidden
          className="size-4 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      ) : null}
      {children}
    </button>
  );
}
