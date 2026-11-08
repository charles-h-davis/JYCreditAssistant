import type { CategoryProgress, LessonProgress } from "@/lib/api/types";

/** Shared helpers for the learning screens. */

export function completedCount(category: CategoryProgress): number {
  return category.lessons.filter((lesson) => lesson.completed).length;
}

/** The first lesson the user has not finished, or null when the activity is done. */
export function nextLesson(category: CategoryProgress): LessonProgress | null {
  return category.lessons.find((lesson) => !lesson.completed) ?? null;
}
