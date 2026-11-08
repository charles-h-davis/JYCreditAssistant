/**
 * Backend API client. Every call goes through the FastAPI app:
 *   POST /cost-to-buy/extract            (multipart image -> product + price)
 *   GET  /card-storage/cards?user_id=    (the user's cards)
 *   GET  /cost-to-buy/monthly-payment?   (stored monthly payment, 404 if unset)
 *
 * Fetches happen from the extension origin with `host_permissions`, so CORS is
 * bypassed and no backend CORS change is needed.
 */

import { getConnection } from "./config.js";

function errorMessage(body, status) {
  if (body && typeof body === "object") {
    if (body.error && body.error.message) return body.error.message;
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail[0] && body.detail[0].msg) {
      return body.detail[0].msg;
    }
  }
  return `Request failed (${status}).`;
}

async function baseUrl() {
  const conn = await getConnection();
  return conn.backendBaseUrl;
}

async function parseBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function call(path, options = {}) {
  const base = await baseUrl();
  let response;
  try {
    response = await fetch(`${base}${path}`, options);
  } catch {
    throw new Error("Can't reach the backend. Is it running on :8000?");
  }
  const body = await parseBody(response);
  if (!response.ok) throw new Error(errorMessage(body, response.status));
  return body;
}

/** Send a screenshot to the backend and get { product_name, price, currency, ... }. */
export async function extractImage(blob) {
  const form = new FormData();
  form.append("file", blob, "page.png");
  return call("/cost-to-buy/extract", { method: "POST", body: form });
}

export async function listCards(userId) {
  return call(`/card-storage/cards?user_id=${encodeURIComponent(userId)}`);
}

export async function getMonthlyPayment(userId, cardId) {
  const base = await baseUrl();
  const url =
    `${base}/cost-to-buy/monthly-payment?user_id=${encodeURIComponent(userId)}` +
    `&card_id=${encodeURIComponent(cardId)}`;
  let response;
  try {
    response = await fetch(url);
  } catch {
    throw new Error("Can't reach the backend. Is it running on :8000?");
  }
  if (response.status === 404) return null;
  const body = await parseBody(response);
  if (!response.ok) throw new Error(errorMessage(body, response.status));
  return body;
}

function toCard(row, monthlyPayment) {
  return {
    card_id: row.id,
    nickname: row.nickname || row.issuer || "Card",
    issuer: row.issuer || "",
    last_four: row.last_four || "",
    current_balance: Number(row.current_balance) || 0,
    purchase_apr: row.purchase_apr == null ? null : Number(row.purchase_apr),
    monthly_payment: monthlyPayment == null ? null : Number(monthlyPayment),
  };
}

/** Resolve a card (+ its stored monthly payment) for the calculator. */
export async function resolveCard(userId, cardId) {
  const cards = await listCards(userId);
  if (!Array.isArray(cards) || cards.length === 0) {
    throw new Error("No cards found for this account. Sync a card in the app first.");
  }
  const row = cards.find((entry) => entry.id === cardId) || cards[0];
  let monthlyPayment = null;
  try {
    const stored = await getMonthlyPayment(userId, row.id);
    monthlyPayment = stored ? stored.monthly_payment : null;
  } catch {
    monthlyPayment = null;
  }
  return toCard(row, monthlyPayment);
}

/**
 * Confirm a purchase: store it in the user's planned purchases. The backend also
 * upserts the card's current monthly payment to `monthly_payment`.
 */
export async function createPurchasePlan(payload) {
  return call("/cost-to-buy/purchase-plans", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
