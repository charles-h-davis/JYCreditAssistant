"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ErrorNote } from "@/components/ui/primitives";
import { checkAnswer } from "@/lib/api/endpoints";
import type { AnswerCheck, AttemptResult, Question } from "@/lib/api/types";

type Phase = "summary" | "questions" | "result";

/**
 * The lesson flow from the design refs: summary first, then the five questions,
 * then the graded result. Shared by lessons and the recap round.
 */
export function LessonRunner({
  eyebrow,
  title,
  summary,
  questions,
  submitLabel = "Start questions",
  onSubmit,
  onExit,
}: {
  eyebrow: string;
  title: string;
  summary: string;
  questions: Question[];
  submitLabel?: string;
  onSubmit: (
    answers: { question_id: string; selected_index: number }[],
  ) => Promise<AttemptResult>;
  onExit: () => void;
}) {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("summary");
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [feedback, setFeedback] = useState<Record<string, AnswerCheck>>({});
  const [checking, setChecking] = useState<string | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const current = questions[index];
  const answered = Object.keys(answers).length;

  /** Record the pick, then ask the API for an instant verdict. */
  async function choose(question: Question, optionIndex: number) {
    if (feedback[question.id] || checking !== null) return;
    setAnswers((previous) => ({ ...previous, [question.id]: optionIndex }));
    setChecking(question.id);
    try {
      const verdict = await checkAnswer(question.id, optionIndex);
      setFeedback((previous) => ({ ...previous, [question.id]: verdict }));
    } catch {
      // Feedback is a nicety: if it fails the final submission still grades.
    } finally {
      setChecking(null);
    }
  }

  async function submit() {
    setPending(true);
    setError(null);
    try {
      const payload = questions.map((question) => ({
        question_id: question.id,
        selected_index: answers[question.id] ?? 0,
      }));
      const graded = await onSubmit(payload);
      setResult(graded);
      setPhase("result");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Couldn't grade that attempt.");
    } finally {
      setPending(false);
    }
  }

  function next() {
    if (index < questions.length - 1) setIndex(index + 1);
    else void submit();
  }

  return (
    <main className="app-column flex min-h-dvh flex-col bg-page px-5 pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onExit}
          aria-label="Exit lesson"
          className="grid size-11 place-items-center rounded-full bg-surface-strong text-ink transition active:scale-95"
        >
          <X size={20} strokeWidth={2.2} aria-hidden />
        </button>
        <p className="text-xs text-muted">
          {phase === "questions"
            ? `${index + 1} of ${questions.length}`
            : phase === "summary"
              ? "Lesson summary"
              : "Result"}
        </p>
      </div>

      {phase === "questions" ? (
        <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-surface-strong">
          <div
            className="h-full rounded-full bg-ink transition-all duration-300"
            style={{ width: `${(answered / questions.length) * 100}%` }}
          />
        </div>
      ) : null}

      {phase === "summary" ? (
        <div className="mt-5 flex flex-1 flex-col">
          <p className="text-xs font-medium tracking-wide text-muted uppercase">{eyebrow}</p>
          <h1 className="mt-1 text-[1.9rem] leading-tight font-semibold tracking-tight">
            {title}
          </h1>
          <div className="surface mt-4 p-4">
            <p className="text-[0.95rem] leading-relaxed text-ink-soft">{summary}</p>
          </div>
          <p className="mt-3 text-sm text-muted">
            {questions.length} questions · any score completes the lesson · retakes are
            unlimited.
          </p>
          <div className="mt-auto pt-6">
            <Button className="w-full" onClick={() => setPhase("questions")}>
              {submitLabel}
            </Button>
          </div>
        </div>
      ) : null}

      {phase === "questions" && current ? (
        <div className="mt-4 flex flex-1 flex-col">
          <h1 className="text-[1.6rem] leading-tight font-semibold tracking-tight">
            {title}
          </h1>
          <div className="surface mt-4 p-5">
            <p className="text-center text-lg leading-snug font-medium">{current.prompt}</p>
          </div>

          <div className="mt-4 space-y-2.5">
            {current.options.map((option, optionIndex) => {
              const verdict = feedback[current.id];
              const selected = answers[current.id] === optionIndex;
              const showCorrect = verdict ? optionIndex === verdict.correct_index : false;
              const showWrong = Boolean(verdict && selected && !verdict.correct);

              const tone = showCorrect
                ? "bg-positive text-white"
                : showWrong
                  ? "bg-danger text-white"
                  : selected
                    ? "bg-ink text-white"
                    : "bg-surface text-ink";

              return (
                <button
                  key={`${current.id}-${optionIndex}`}
                  type="button"
                  onClick={() => void choose(current, optionIndex)}
                  aria-pressed={selected}
                  disabled={Boolean(verdict) || checking === current.id}
                  className={`flex w-full items-center justify-center gap-2 rounded-2xl px-4 py-3.5 text-center text-[0.95rem] font-medium transition ${tone}`}
                >
                  {option}
                  {showCorrect ? <Check size={16} aria-hidden /> : null}
                  {showWrong ? <X size={16} aria-hidden /> : null}
                </button>
              );
            })}
          </div>

          {feedback[current.id] ? (
            <div
              className={`mt-3 rounded-2xl px-4 py-3 ${
                feedback[current.id].correct ? "bg-positive/10" : "bg-[#fdecea]"
              }`}
            >
              <p
                className={`text-sm font-semibold ${
                  feedback[current.id].correct ? "text-positive" : "text-danger"
                }`}
              >
                {feedback[current.id].correct ? "Correct" : "Not quite"}
              </p>
              {feedback[current.id].explanation ? (
                <p className="mt-1 text-sm text-ink-soft">
                  {feedback[current.id].explanation}
                </p>
              ) : null}
            </div>
          ) : null}

          {error ? (
            <div className="mt-3">
              <ErrorNote>{error}</ErrorNote>
            </div>
          ) : null}

          <div className="mt-auto pt-6">
            <Button
              className="w-full"
              onClick={next}
              loading={pending}
              disabled={answers[current.id] === undefined}
            >
              {index === questions.length - 1 ? "Finish" : "Next question"}
            </Button>
          </div>
        </div>
      ) : null}

      {phase === "result" && result ? (
        <div className="mt-5 flex flex-1 flex-col">
          <p className="text-xs font-medium tracking-wide text-muted uppercase">
            {result.kind === "recap" ? "Refresh round" : "Lesson complete"}
          </p>
          <h1 className="mt-1 text-[1.9rem] leading-tight font-semibold tracking-tight">
            {result.score} of {result.total} correct
          </h1>
          <p className="mt-1 text-sm text-muted">
            Streak {result.streak.current_streak} day
            {result.streak.current_streak === 1 ? "" : "s"} · best{" "}
            {result.streak.longest_streak}
          </p>

          <ul className="mt-4 space-y-2">
            {result.answers.map((answer, answerIndex) => {
              const question = questions.find((item) => item.id === answer.question_id);
              return (
                <li key={answer.question_id} className="rounded-2xl bg-surface p-3.5">
                  <div className="flex items-start gap-2">
                    <span
                      className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full text-[11px] font-semibold ${
                        answer.correct ? "bg-positive text-white" : "bg-danger text-white"
                      }`}
                      aria-hidden
                    >
                      {answer.correct ? <Check size={12} /> : <X size={12} />}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium">
                        {answerIndex + 1}. {question?.prompt ?? "Question"}
                      </p>
                      <p className="mt-0.5 text-xs text-ink-soft">
                        Correct: {question?.options[answer.correct_index] ?? "—"}
                      </p>
                      {answer.explanation ? (
                        <p className="mt-1 text-xs text-muted">{answer.explanation}</p>
                      ) : null}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>

          <div className="mt-auto pt-6">
            <Button
              className="w-full"
              onClick={() => {
                router.push("/learning");
                router.refresh();
              }}
            >
              Back to learning
            </Button>
          </div>
        </div>
      ) : null}
    </main>
  );
}
