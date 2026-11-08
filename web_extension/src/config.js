/**
 * Connection + card configuration stored in `chrome.storage.local`.
 *
 * Primary card source is the backend (Supabase sign-in -> cards -> monthly
 * payment). A manual card is kept as a fallback so the calculator still works if
 * the backend is unreachable.
 */

const KEYS = {
  connection: "connection",
  selectedCardId: "selectedCardId",
  resolvedCard: "resolvedCard",
  manualCard: "manualCard",
};

export const DEFAULT_BACKEND = "http://127.0.0.1:8000/api/v1";

/** @returns {Promise<{supabaseUrl: string, supabaseAnonKey: string, backendBaseUrl: string}>} */
export async function getConnection() {
  const stored = await chrome.storage.local.get(KEYS.connection);
  const conn = stored[KEYS.connection] || {};
  return {
    supabaseUrl: String(conn.supabaseUrl || "").replace(/\/+$/, ""),
    supabaseAnonKey: String(conn.supabaseAnonKey || ""),
    backendBaseUrl: String(conn.backendBaseUrl || DEFAULT_BACKEND).replace(/\/+$/, ""),
  };
}

export async function saveConnection(conn) {
  await chrome.storage.local.set({ [KEYS.connection]: conn });
}

export async function getSelectedCardId() {
  const stored = await chrome.storage.local.get(KEYS.selectedCardId);
  return stored[KEYS.selectedCardId] || null;
}

export async function setSelectedCardId(cardId) {
  await chrome.storage.local.set({ [KEYS.selectedCardId]: cardId || null });
}

export async function saveResolvedCard(card) {
  await chrome.storage.local.set({ [KEYS.resolvedCard]: card || null });
}

export async function getResolvedCard() {
  const stored = await chrome.storage.local.get(KEYS.resolvedCard);
  return stored[KEYS.resolvedCard] || null;
}

export async function saveManualCard(card) {
  await chrome.storage.local.set({ [KEYS.manualCard]: card || null });
}

export async function getManualCard() {
  const stored = await chrome.storage.local.get(KEYS.manualCard);
  return stored[KEYS.manualCard] || null;
}

/** Card used by the popup: resolved (backend) first, manual fallback second. */
export async function getCard() {
  return (await getResolvedCard()) || (await getManualCard()) || null;
}
