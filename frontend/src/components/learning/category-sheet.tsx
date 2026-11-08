"use client";

import Link from "next/link";
import type { CategoryProgress } from "@/lib/api/types";
import { completedCount, nextLesson } from "@/lib/learning";

/**
 * Pop-up behind each activity ring: starts the next unfinished lesson, or lists
 * all three for a retake once the activity is complete.
 */
export function CategorySheet({
  category,
  onChanged,
}: {
  category: CategoryProgress;
  onChanged: () => void;
}) {
  const done = completedCount(category);
  const next = nextLesson(category);

  if (next) {
    return (
      <>
        <p className="text-xs font-medium tracking-wide text-muted uppercase">
          Lesson {next.position} of {category.lessons.length}
        </p>
        <h2 className="mt-1 text-xl font-semibold tracking-tight">{category.title}</h2>
        <p className="mt-1 text-sm text-ink-soft">{next.summary}</p>
        <Link
          href={`/learning/lesson/${next.slug}`}
          onClick={onChanged}
          className="btn btn-primary mt-5 w-full"
        >
          Start lesson
        </Link>
        <p className="mt-3 text-center text-xs text-muted">
          {done} of {category.lessons.length} complete in this activity
        </p>
      </>
    );
  }

  return (
    <>
      <p className="text-xs font-medium tracking-wide text-muted uppercase">Completed</p>
      <h2 className="mt-1 text-xl font-semibold tracking-tight">{category.title}</h2>
      <p className="mt-1 text-sm text-ink-soft">
        All {category.lessons.length} lessons done. Pick one to run again — retakes keep
        your best score.
      </p>
      <div className="mt-4 space-y-2">
        {category.lessons.map((lesson) => (
          <Link
            key={lesson.id}
            href={`/learning/lesson/${lesson.slug}`}
            onClick={onChanged}
            className="flex items-center justify-between gap-3 rounded-2xl bg-surface px-4 py-3"
          >
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium">{lesson.title}</span>
              <span className="block text-xs text-muted">
                Best {lesson.best_score ?? 0}/{lesson.question_count} · {lesson.attempts}{" "}
                attempt{lesson.attempts === 1 ? "" : "s"}
              </span>
            </span>
            <span className="shrink-0 text-sm text-ink-soft">Redo</span>
          </Link>
        ))}
      </div>
    </>
  );
}
