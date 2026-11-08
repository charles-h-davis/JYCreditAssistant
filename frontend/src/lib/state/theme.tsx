"use client";

import {
  createContext,
  useCallback,
  useContext,
  useSyncExternalStore,
  type ReactNode,
} from "react";

/** The base colour scheme: cool light, dark, or dark-ink-on-cream. */
export type ThemeMode = "light" | "dark" | "cream";
/** A lighter-touch accent that layers on top of the base scheme. */
export type ThemeAccent = "indigo" | "ocean" | "rose" | "amber";

export const THEME_MODES: { value: ThemeMode; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "cream", label: "Cream" },
];

export const THEME_ACCENTS: { value: ThemeAccent; label: string; swatch: string }[] = [
  { value: "indigo", label: "Indigo", swatch: "var(--color-accent)" },
  { value: "ocean", label: "Ocean", swatch: "#0f7c8c" },
  { value: "rose", label: "Rose", swatch: "#b83f7a" },
  { value: "amber", label: "Amber", swatch: "#b26a12" },
];

export const MODE_KEY = "creditmate-theme";
export const ACCENT_KEY = "creditmate-accent";
export const DEFAULT_MODE: ThemeMode = "light";
export const DEFAULT_ACCENT: ThemeAccent = "indigo";

/** The colour a mobile browser paints its own chrome with, per scheme. */
export const CHROME_COLOUR: Record<ThemeMode, string> = {
  light: "#f5f8fc",
  dark: "#0b1220",
  cream: "#f7f0e3",
};

export function isMode(value: unknown): value is ThemeMode {
  return THEME_MODES.some((mode) => mode.value === value);
}

export function isAccent(value: unknown): value is ThemeAccent {
  return THEME_ACCENTS.some((accent) => accent.value === value);
}

interface Scheme {
  mode: ThemeMode;
  accent: ThemeAccent;
}

/** Write the scheme onto <html> so the CSS token blocks pick it up. */
function apply({ mode, accent }: Scheme) {
  const root = document.documentElement;
  root.dataset.theme = mode;
  root.dataset.accent = accent;
  root.style.colorScheme = mode === "dark" ? "dark" : "light";
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", CHROME_COLOUR[mode]);
}

function persist({ mode, accent }: Scheme) {
  try {
    window.localStorage.setItem(MODE_KEY, mode);
    window.localStorage.setItem(ACCENT_KEY, accent);
  } catch {
    // Private mode / storage disabled — the choice just won't survive a reload.
  }
}

/** What the inline script in the root layout already put on <html>. */
function readFromDom(): Scheme {
  const root = document.documentElement;
  let storedMode: string | null = null;
  let storedAccent: string | null = null;
  try {
    storedMode = window.localStorage.getItem(MODE_KEY);
    storedAccent = window.localStorage.getItem(ACCENT_KEY);
  } catch {
    // Storage blocked: fall back to whatever the pre-paint script applied.
  }
  return {
    mode: isMode(storedMode)
      ? storedMode
      : isMode(root.dataset.theme)
        ? root.dataset.theme
        : DEFAULT_MODE,
    accent: isAccent(storedAccent)
      ? storedAccent
      : isAccent(root.dataset.accent)
        ? root.dataset.accent
        : DEFAULT_ACCENT,
  };
}

/*
 * The scheme lives on <html> and in localStorage, i.e. outside React. Treat it as
 * an external store: the snapshot is cached so React sees a stable value, and the
 * server snapshot is the default so prerendered HTML stays deterministic. React
 * re-reads after hydration, which picks up the pre-paint choice with no flash and
 * no state-in-effect.
 */
let snapshot: Scheme | null = null;
const listeners = new Set<() => void>();

function getSnapshot(): Scheme {
  snapshot ??= readFromDom();
  return snapshot;
}

function getServerSnapshot(): Scheme {
  return { mode: DEFAULT_MODE, accent: DEFAULT_ACCENT };
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function writeScheme(next: Scheme) {
  snapshot = next;
  apply(next);
  persist(next);
  for (const listener of listeners) listener();
}

interface ThemeValue {
  mode: ThemeMode;
  accent: ThemeAccent;
  setMode: (mode: ThemeMode) => void;
  setAccent: (accent: ThemeAccent) => void;
}

const ThemeContext = createContext<ThemeValue | null>(null);

/**
 * Holds the colour scheme chosen on the Your Account screen. The scheme is on
 * <html> (`data-theme`, `data-accent`), so every token-based class in the app
 * changes at once, and it is mirrored into localStorage for the next visit.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const { mode, accent } = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );

  const setMode = useCallback((next: ThemeMode) => {
    writeScheme({ ...getSnapshot(), mode: next });
  }, []);

  const setAccent = useCallback((next: ThemeAccent) => {
    writeScheme({ ...getSnapshot(), accent: next });
  }, []);

  return (
    <ThemeContext.Provider value={{ mode, accent, setMode, setAccent }}>
      {children}
    </ThemeContext.Provider>
  );
}

/** The current colour scheme and its setters. */
export function useTheme(): ThemeValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme must be used inside a ThemeProvider");
  return value;
}
