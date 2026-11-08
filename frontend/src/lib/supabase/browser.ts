import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { SUPABASE_ANON_KEY, SUPABASE_URL } from "@/lib/config";

let browserClient: SupabaseClient | null = null;

/**
 * Anon-key Supabase client used only for auth (sign in / sign up / sign out and
 * reading the current user). The service-role key never reaches the browser.
 */
export function getSupabaseBrowserClient(): SupabaseClient | null {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return null;
  if (!browserClient) {
    browserClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: "creditmate-auth",
      },
    });
  }
  return browserClient;
}

export const isSupabaseConfigured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
