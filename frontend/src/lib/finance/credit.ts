/**
 * Credit maths — a faithful port of `backend/app/sections/cost_to_buy/service.py`.
 *
 * The backend is the source of truth; this file exists so the "adjust monthly
 * repayment" slider can recompute instantly on the phone. Keep the two in sync:
 *
 * - each cycle the payment is applied first, then interest is charged on what is
 *   left (APR/12) — so clearing the balance in full costs nothing;
 * - there is no grace period on a carried balance, so a new purchase accrues
 *   interest from its first full cycle;
 * - the loop is capped and a payment that cannot cover interest is rejected.
 */

export const MAX_CYCLES = 1200;

export interface Payoff {
  months: number;
  totalInterest: number;
  totalPaid: number;
}

export function monthlyRate(apr: number): number {
  return apr / 100 / 12;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}

/** Amortise `balance` at `apr` paying `payment` each month. */
export function amortise(balance: number, apr: number, payment: number): Payoff {
  if (balance <= 0) return { months: 0, totalInterest: 0, totalPaid: 0 };
  if (payment <= 0) return { months: MAX_CYCLES, totalInterest: 0, totalPaid: 0 };

  if (payment >= balance) {
    // Clearing the balance in full settles it that cycle: no further interest.
    return { months: 1, totalInterest: 0, totalPaid: round(balance) };
  }

  const rate = monthlyRate(apr);
  let outstanding = balance;
  let totalInterest = 0;
  let cycles = 0;

  while (outstanding > 0 && cycles < MAX_CYCLES) {
    cycles += 1;
    if (payment >= outstanding) {
      outstanding = 0;
      break;
    }
    // Interest is charged on what's left after the payment, so clearing the
    // balance in full costs nothing and the curve has no step changes.
    const remaining = outstanding - payment;
    const interest = remaining * rate;
    totalInterest += interest;
    outstanding = remaining + interest;
    if (outstanding < 0.005) outstanding = 0;
  }

  const interest = round(totalInterest);
  return {
    months: cycles,
    totalInterest: interest,
    totalPaid: round(balance + interest),
  };
}

/** True when `payment` covers the monthly interest, i.e. the debt can be cleared. */
export function paymentCoversInterest(balance: number, apr: number, payment: number): boolean {
  if (balance <= 0) return true;
  return payment > balance * monthlyRate(apr);
}

/**
 * The lowest payment worth offering: the monthly interest plus a small dent, and
 * never below £25. Below this the balance would never clear, so every slider in
 * the app bottoms out here.
 */
export function minimumPayment(balance: number, apr: number, floor = 25): number {
  if (balance <= 0) return 0;
  const interest = balance * monthlyRate(apr);
  return round(Math.max(floor, interest + 5));
}

/** Payment that clears `balance` in `months` cycles (mirrors suggest_payment). */
export function suggestPayment(balance: number, apr: number, months = 24): number {
  if (balance <= 0) return 0;
  const rate = monthlyRate(apr);
  const raw =
    rate === 0 ? balance / months : (balance * rate) / (1 - Math.pow(1 + rate, -months));
  return Math.ceil(raw * 100) / 100;
}

/** "1Y 5M" / "5M" / "Debt free" — the copy used on the dashboard tile. */
export function monthsToLabel(months: number): string {
  if (months <= 0) return "Debt free";
  const years = Math.floor(months / 12);
  const rest = months % 12;
  if (years === 0) return `${rest}M`;
  if (rest === 0) return `${years}Y`;
  return `${years}Y ${rest}M`;
}

export interface ProjectionPoint {
  month: number;
  balance: number;
}

/**
 * Remaining balance month by month, for the "balance until debt free" chart.
 * Starts at the purchase-inclusive balance so the curve tells the real story.
 */
export function balanceProjection(
  balance: number,
  apr: number,
  payment: number,
  maxMonths = 120,
): ProjectionPoint[] {
  const points: ProjectionPoint[] = [{ month: 0, balance: round(balance) }];
  if (balance <= 0 || payment <= 0) return points;

  const rate = monthlyRate(apr);
  let outstanding = balance;

  for (let month = 1; month <= Math.min(maxMonths, MAX_CYCLES); month += 1) {
    if (payment >= outstanding) {
      points.push({ month, balance: 0 });
      return points;
    }
    outstanding = (outstanding - payment) * (1 + rate);
    if (outstanding < 0.005) {
      points.push({ month, balance: 0 });
      return points;
    }
    points.push({ month, balance: round(outstanding) });
  }
  return points;
}
