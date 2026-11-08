/**
 * Credit maths — a direct port of `frontend/src/lib/finance/credit.ts`, which is
 * itself the client-side mirror of `backend/app/sections/cost_to_buy/service.py`.
 *
 * Model (payment-first): each cycle the payment is applied first, then interest is
 * charged on the balance that is left (APR/12). Clearing the balance in full
 * therefore costs nothing, and raising the payment can only ever lower the total
 * interest. Keep the three copies in sync — see the README's golden test vector.
 */

export const MAX_CYCLES = 1200;

/** @typedef {{ months: number, totalInterest: number, totalPaid: number }} Payoff */

/** @param {number} apr */
export function monthlyRate(apr) {
  return apr / 100 / 12;
}

/** @param {number} value */
function round(value) {
  return Math.round(value * 100) / 100;
}

/**
 * Amortise `balance` at `apr` paying `payment` each month.
 * @param {number} balance
 * @param {number} apr
 * @param {number} payment
 * @returns {Payoff}
 */
export function amortise(balance, apr, payment) {
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

/**
 * True when `payment` covers the monthly interest, i.e. the debt can be cleared.
 * @param {number} balance
 * @param {number} apr
 * @param {number} payment
 */
export function paymentCoversInterest(balance, apr, payment) {
  if (balance <= 0) return true;
  return payment > balance * monthlyRate(apr);
}

/**
 * The lowest payment worth offering: monthly interest plus a small dent, never
 * below `floor`. Below this the balance would never clear.
 * @param {number} balance
 * @param {number} apr
 * @param {number} [floor]
 */
export function minimumPayment(balance, apr, floor = 25) {
  if (balance <= 0) return 0;
  const interest = balance * monthlyRate(apr);
  return round(Math.max(floor, interest + 5));
}

/**
 * Payment that clears `balance` in `months` cycles (mirrors suggest_payment).
 * @param {number} balance
 * @param {number} apr
 * @param {number} [months]
 */
export function suggestPayment(balance, apr, months = 24) {
  if (balance <= 0) return 0;
  const rate = monthlyRate(apr);
  const raw =
    rate === 0 ? balance / months : (balance * rate) / (1 - Math.pow(1 + rate, -months));
  return Math.ceil(raw * 100) / 100;
}

/**
 * "1Y 5M" / "5M" / "Debt free" — the copy used on the dashboard tile.
 * @param {number} months
 */
export function monthsToLabel(months) {
  if (months <= 0) return "Debt free";
  const years = Math.floor(months / 12);
  const rest = months % 12;
  if (years === 0) return `${rest}M`;
  if (rest === 0) return `${years}Y`;
  return `${years}Y ${rest}M`;
}
