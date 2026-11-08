"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { SendHorizontal } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { TopBar } from "@/components/layout/top-bar";
import { ErrorNote } from "@/components/ui/primitives";
import { ApiError } from "@/lib/api/client";
import { askAssistant } from "@/lib/api/endpoints";

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  refused?: boolean;
}

const GREETING: Message = {
  id: "greeting",
  role: "assistant",
  text: "Hi, I'm here to answer any questions you might have related to credit or money!",
};

function newId(): string {
  return Math.random().toString(36).slice(2);
}

/** "Ask Me Anything" — a Gemini-backed chat, scoped to credit and money. */
export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;

    setInput("");
    setError(null);
    setLastQuestion(trimmed);
    setMessages((current) => [
      ...current,
      { id: newId(), role: "user", text: trimmed },
    ]);
    setBusy(true);
    try {
      const reply = await askAssistant(trimmed);
      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          text: reply.reply,
          refused: reply.refused || !reply.in_scope,
        },
      ]);
    } catch (caught) {
      const status = caught instanceof ApiError ? caught.status : 0;
      setError(
        status === 502 || status === 503
          ? "The AI service is busy right now. Give it a moment and try again."
          : status === 0
            ? "Can't reach the API. Is the backend running on port 8000?"
            : caught instanceof Error
              ? caught.message
              : "The assistant couldn't answer that.",
      );
    } finally {
      setBusy(false);
    }
  }

  function send(event: React.FormEvent) {
    event.preventDefault();
    void ask(input);
  }

  function retry() {
    if (!lastQuestion) return;
    // Drop the unanswered question first so the retry doesn't duplicate it.
    setMessages((current) =>
      current.at(-1)?.role === "user" ? current.slice(0, -1) : current,
    );
    void ask(lastQuestion);
  }

  return (
    <AppShell>
      <TopBar showCamera={false} />
      <h1 className="mt-5 text-[2rem] leading-tight font-semibold tracking-tight">
        Ask Me Anything
      </h1>

      <div className="mt-4 flex h-[calc(100dvh-13.5rem)] flex-col">
        <div
          ref={scroller}
          className="surface flex-1 overflow-y-auto p-3"
          aria-live="polite"
        >
          <ul className="space-y-2">
            {messages.map((message) => (
              <li
                key={message.id}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-[0.95rem] leading-relaxed ${
                    message.role === "user"
                      ? "bg-ink text-white"
                      : message.refused
                        ? "bg-surface-strong/70 text-muted italic"
                        : "bg-surface-strong/70 text-ink"
                  }`}
                >
                  {message.role === "assistant" ? (
                    <div className="[&_a]:underline [&_code]:rounded [&_code]:bg-white/60 [&_code]:px-1 [&_li]:ml-4 [&_li]:list-disc [&_p]:m-0 [&_p+p]:mt-2 [&_strong]:font-semibold">
                      <ReactMarkdown>{message.text}</ReactMarkdown>
                    </div>
                  ) : (
                    message.text
                  )}
                </div>
              </li>
            ))}
          </ul>

          {busy ? (
            <div className="mt-2 flex justify-start">
              <div className="flex items-center gap-1.5 rounded-2xl bg-surface-strong/70 px-3.5 py-3">
                {[0, 1, 2].map((dot) => (
                  <span
                    key={dot}
                    className="size-1.5 animate-bounce rounded-full bg-muted"
                    style={{ animationDelay: `${dot * 120}ms` }}
                  />
                ))}
                <span className="sr-only">Assistant is typing</span>
              </div>
            </div>
          ) : null}
        </div>

        {error ? (
          <div className="mt-2">
            <ErrorNote
              action={
                lastQuestion ? (
                  <button
                    type="button"
                    onClick={retry}
                    disabled={busy}
                    className="text-sm font-medium underline underline-offset-2 disabled:opacity-50"
                  >
                    Try again
                  </button>
                ) : null
              }
            >
              {error}
            </ErrorNote>
          </div>
        ) : null}

        <form onSubmit={send} className="mt-3 flex items-center gap-2">
          <input
            className="field"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type question here..."
            aria-label="Your question"
            maxLength={2000}
          />
          <button
            type="submit"
            disabled={busy || input.trim().length === 0}
            aria-label="Send question"
            className="grid size-12 shrink-0 place-items-center rounded-2xl bg-ink text-white transition active:scale-95 disabled:opacity-40"
          >
            <SendHorizontal size={19} strokeWidth={2} aria-hidden />
          </button>
        </form>
      </div>
    </AppShell>
  );
}
