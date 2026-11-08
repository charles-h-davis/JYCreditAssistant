/**
 * Runtime configuration. Everything here is public (NEXT_PUBLIC_*), so the
 * service-role key must never appear in this file or anywhere in the bundle.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000/api/v1";

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

/** Credentials of the seeded demo account (see backend/scripts/seed_demo.py). */
export const DEMO_EMAIL = process.env.NEXT_PUBLIC_DEMO_EMAIL ?? "demo@demo.com";
export const DEMO_PASSWORD = process.env.NEXT_PUBLIC_DEMO_PASSWORD ?? "demo123!";

export const CURRENCY = "GBP";
export const LOCALE = "en-GB";
