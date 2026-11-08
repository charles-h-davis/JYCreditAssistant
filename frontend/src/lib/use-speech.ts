"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Read text aloud with the browser's built-in speech synthesis — no dependency,
 * no API key, no network round-trip.
 *
 * One button drives it: `toggle` starts, pauses and resumes. State is tracked
 * optimistically (some browsers don't fire `onpause`) and mirrored from the
 * utterance events so it always settles on the truth.
 */

export type SpeechState = "idle" | "speaking" | "paused";

function synthesis(): SpeechSynthesis | null {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return null;
  return window.speechSynthesis;
}

/** Prefer a UK English voice (the app is en-GB), else any English, else the default. */
function pickVoice(): SpeechSynthesisVoice | null {
  const engine = synthesis();
  if (!engine) return null;
  const voices = engine.getVoices();
  if (voices.length === 0) return null;
  const tag = (voice: SpeechSynthesisVoice) => voice.lang.replace("_", "-").toLowerCase();
  return (
    voices.find((voice) => tag(voice) === "en-gb") ??
    voices.find((voice) => tag(voice).startsWith("en")) ??
    null
  );
}

export function useSpeech() {
  const [state, setState] = useState<SpeechState>("idle");
  const [available] = useState(() => synthesis() !== null);
  const current = useRef<SpeechSynthesisUtterance | null>(null);

  const stop = useCallback(() => {
    const engine = synthesis();
    if (!engine) return;
    engine.cancel();
    current.current = null;
    setState("idle");
  }, []);

  const speak = useCallback((text: string) => {
    const engine = synthesis();
    const trimmed = text.trim();
    if (!engine || !trimmed) return;

    // Always cancel first: Chrome otherwise leaves a half-spoken queue behind.
    engine.cancel();

    const utterance = new SpeechSynthesisUtterance(trimmed);
    utterance.lang = "en-GB";
    utterance.rate = 1;
    const voice = pickVoice();
    if (voice) utterance.voice = voice;
    utterance.onstart = () => setState("speaking");
    utterance.onend = () => {
      current.current = null;
      setState("idle");
    };
    utterance.onerror = () => {
      current.current = null;
      setState("idle");
    };
    utterance.onpause = () => setState("paused");
    utterance.onresume = () => setState("speaking");

    current.current = utterance;
    engine.speak(utterance);
  }, []);

  const pause = useCallback(() => {
    const engine = synthesis();
    if (!engine) return;
    engine.pause();
    setState("paused");
  }, []);

  const resume = useCallback(() => {
    const engine = synthesis();
    if (!engine) return;
    engine.resume();
    setState("speaking");
  }, []);

  /** Start, pause or resume — whatever the button should do next. */
  const toggle = useCallback(
    (text: string) => {
      if (state === "speaking") {
        pause();
        return;
      }
      if (state === "paused") {
        resume();
        return;
      }
      speak(text);
    },
    [state, pause, resume, speak],
  );

  // Leaving the screen mid-sentence must not keep talking.
  useEffect(() => {
    return () => {
      synthesis()?.cancel();
    };
  }, []);

  return { available, state, speak, pause, resume, stop, toggle };
}
