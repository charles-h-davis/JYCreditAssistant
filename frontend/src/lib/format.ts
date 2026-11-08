import { CURRENCY, LOCALE } from "@/lib/config";

const money = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const moneyWhole = new Intl.NumberFormat(LOCALE, {
  style: "currency",
  currency: CURRENCY,
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

/** `£1,520.49` — the format used on tiles and transaction rows. */
export function formatMoney(value: number, options: { whole?: boolean } = {}): string {
  const safe = Number.isFinite(value) ? value : 0;
  return options.whole ? moneyWhole.format(safe) : money.format(safe);
}

/** `£1.5k` for tight chart axes. */
export function formatCompact(value: number): string {
  const safe = Number.isFinite(value) ? value : 0;
  const magnitude = Math.abs(safe);
  if (magnitude >= 1000) {
    const thousands = Math.round((safe / 1000) * 10) / 10;
    return `£${thousands % 1 === 0 ? thousands.toFixed(0) : thousands.toFixed(1)}k`;
  }
  return `£${Math.round(safe)}`;
}

/** `34.9%` */
export function formatPercent(value: number): string {
  return `${Math.round(value * 10) / 10}%`;
}

const ordinal = new Intl.PluralRules(LOCALE, { type: "ordinal" });
const ORDINAL_SUFFIX: Record<string, string> = { one: "st", two: "nd", few: "rd", other: "th" };

function dayWithSuffix(day: number): string {
  return `${day}${ORDINAL_SUFFIX[ordinal.select(day)]}`;
}

function parseDate(value: string): Date {
  // Dates come back as `YYYY-MM-DD` (no timezone) — anchor them at midday so a
  // browser timezone offset can never roll the day over.
  return new Date(`${value}T12:00:00`);
}

/** `7th Oct` */
export function formatShortDate(value: string | null): string {
  if (!value) return "";
  const date = parseDate(value);
  return `${dayWithSuffix(date.getDate())} ${date.toLocaleDateString(LOCALE, { month: "short" })}`;
}

/** `7th Oct 12:15` */
export function formatDateTime(value: string | null): string {
  if (!value) return "";
  const date = value.includes("T") ? new Date(value) : parseDate(value);
  const time = date.toLocaleTimeString(LOCALE, { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${dayWithSuffix(date.getDate())} ${date.toLocaleDateString(LOCALE, { month: "short" })} ${time}`;
}

/** `7th Oct` — used when a value has no time component (Plaid `authorized_date`). */
export function formatDayOrDateTime(value: string | null): string {
  if (!value) return "";
  return value.includes("T") ? formatDateTime(value) : formatShortDate(value);
}

/** `Monday 7th October 12:15` — matches the planned-purchase rows in the design. */
export function formatLongDateTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const weekday = date.toLocaleDateString(LOCALE, { weekday: "long" });
  const month = date.toLocaleDateString(LOCALE, { month: "long" });
  const time = date.toLocaleTimeString(LOCALE, { hour: "2-digit", minute: "2-digit", hour12: false });
  return `${weekday} ${dayWithSuffix(date.getDate())} ${month} ${time}`;
}

/** `October` */
export function formatMonth(value: string): string {
  return parseDate(`${value}-01`).toLocaleDateString(LOCALE, { month: "long" });
}

/** `just now`, `12m ago`, `3h ago`, `Yesterday`, `4d ago` — feed timestamps. */
export function formatRelativeTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  const elapsedSeconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (!Number.isFinite(elapsedSeconds)) return "";

  if (elapsedSeconds < 60) return "just now";

  const minutes = Math.round(elapsedSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.round(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;

  return formatShortDate(value.slice(0, 10));
}

/** Initials for the avatar: `Alex Morgan` -> `AM`. */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}
