/**
 * Supabase auth from the extension, using only the public anon key.
 *
 * We use the Auth REST endpoints directly (no SDK) so there are no bundled
 * dependencies and the session lives in `chrome.storage.local`:
 *   POST {url}/auth/v1/token?grant_type=password       -> sign in
 *   POST {url}/auth/v1/token?grant_type=refresh_token   -> refresh
 *   POST {url}/auth/v1/logout                           -> sign out
 *
 * We only need the user's UUID to talk to the backend (which trusts `user_id`).
 */

import { getConnection } from "./config.js";

const SESSION_KEY = "session";
const EXPIRY_MARGIN_MS = 60 * 1000;

function jsonHeaders(anonKey, extra = {}) {
  return { apikey: anonKey, "Content-Type": "application/json", ...extra };
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    return (
      body.error_description ||
      body.msg ||
      body.message ||
      (typeof body.error === "string" ? body.error : null) ||
      `Sign-in failed (${response.status}).`
    );
  } catch {
    return `Sign-in failed (${response.status}).`;
  }
}

function toSession(data) {
  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Date.now() + (Number(data.expires_in) || 3600) * 1000,
    user_id: data.user && data.user.id ? data.user.id : null,
    email: (data.user && data.user.email) || "",
  };
}

export async function signIn(email, password) {
  const conn = await getConnection();
  if (!conn.supabaseUrl || !conn.supabaseAnonKey) {
    throw new Error("Add your Supabase URL and anon key in Connection settings first.");
  }
  let response;
  try {
    response = await fetch(`${conn.supabaseUrl}/auth/v1/token?grant_type=password`, {
      method: "POST",
      headers: jsonHeaders(conn.supabaseAnonKey),
      body: JSON.stringify({ email: String(email).trim(), password }),
    });
  } catch {
    throw new Error("Couldn't reach Supabase. Check the URL and your connection.");
  }
  if (!response.ok) throw new Error(await errorMessage(response));
  const session = toSession(await response.json());
  await chrome.storage.local.set({ [SESSION_KEY]: session });
  return session;
}

async function refreshSession(session) {
  const conn = await getConnection();
  if (!conn.supabaseUrl || !conn.supabaseAnonKey || !session.refresh_token) {
    await chrome.storage.local.remove(SESSION_KEY);
    return null;
  }
  try {
    const response = await fetch(`${conn.supabaseUrl}/auth/v1/token?grant_type=refresh_token`, {
      method: "POST",
      headers: jsonHeaders(conn.supabaseAnonKey),
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    });
    if (!response.ok) throw new Error("refresh failed");
    const data = await response.json();
    const next = toSession(data);
    next.email = next.email || session.email;
    next.user_id = next.user_id || session.user_id;
    await chrome.storage.local.set({ [SESSION_KEY]: next });
    return next;
  } catch {
    await chrome.storage.local.remove(SESSION_KEY);
    return null;
  }
}

/** Return a usable session (auto-refreshing if it's about to expire), or null. */
export async function getSession() {
  const stored = await chrome.storage.local.get(SESSION_KEY);
  const session = stored[SESSION_KEY] || null;
  if (!session) return null;
  if (session.expires_at && session.expires_at - EXPIRY_MARGIN_MS > Date.now()) {
    return session;
  }
  return refreshSession(session);
}

export async function signOut() {
  const conn = await getConnection();
  const stored = await chrome.storage.local.get(SESSION_KEY);
  const session = stored[SESSION_KEY];
  if (session && conn.supabaseUrl && conn.supabaseAnonKey) {
    try {
      await fetch(`${conn.supabaseUrl}/auth/v1/logout`, {
        method: "POST",
        headers: { apikey: conn.supabaseAnonKey, Authorization: `Bearer ${session.access_token}` },
      });
    } catch {
      // Best-effort: clear locally regardless.
    }
  }
  await chrome.storage.local.remove(SESSION_KEY);
}
