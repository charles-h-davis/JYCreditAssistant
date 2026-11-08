/**
 * Runtime configuration. Everything here is public (NEXT_PUBLIC_*), so the
 * service-role key must never appear in this file or anywhere in the bundle.
 */

/** The uvicorn dev server, started from `backend/` (see backend/README.md). */
const DEV_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

/**
 * In production the API is same-origin: the root `vercel.json` rewrites
 * `/api/(.*)` to the internal `backend` service and FastAPI mounts every
 * section under `/api/v1`. A relative base URL keeps each preview and the
 * production domain talking to its own deployment, with no hardcoded host.
 */
const SAME_ORIGIN_API_BASE_URL = "/api/v1";

const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const defaultApiBaseUrl =
  process.env.NODE_ENV === "production" ? SAME_ORIGIN_API_BASE_URL : DEV_API_BASE_URL;

export const API_BASE_URL = (configuredApiBaseUrl || defaultApiBaseUrl).replace(/\/+$/, "");

export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

/** Credentials of the seeded demo account (see backend/scripts/seed_demo.py). */
export const DEMO_EMAIL = process.env.NEXT_PUBLIC_DEMO_EMAIL ?? "demo@demo.com";
export const DEMO_PASSWORD = process.env.NEXT_PUBLIC_DEMO_PASSWORD ?? "demo123!";

export const CURRENCY = "GBP";
export const LOCALE = "en-GB";
