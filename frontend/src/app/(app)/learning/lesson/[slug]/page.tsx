"use client";

import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { LessonRunner } from "@/components/learning/lesson-runner";
import { LoadingSplash } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/primitives";
import { getLesson, recordFeedEntry, submitLessonAttempt } from "@/lib/api/endpoints";
import { useSession } from "@/lib/state/session";

/** Full-screen lesson runner: summary -> five questions -> graded result. */
export default function LessonPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const { userId } = useSession();
  const slug = params.slug;

  const { data, error, isLoading } = useSWR(slug ? `lesson:${slug}` : null, () =>
    getLesson(slug),
  );

  if (isLoading) return <LoadingSplash label="Loading lesson" />;

  if (error || !data || !userId) {
    return (
      <main className="app-column grid min-h-dvh place-items-center bg-page px-6">
        <EmptyState
          title="Lesson unavailable"
          body={error?.message ?? "That lesson could not be loaded."}
          action={
            <button
              type="button"
              onClick={() => router.push("/learning")}
              className="btn btn-primary mt-3 px-6"
            >
              Back to learning
            </button>
          }
        />
      </main>
    );
  }

  return (
    <LessonRunner
      eyebrow={`${data.category_title} · Lesson ${data.position}`}
      title={data.title}
      summary={data.summary}
      questions={data.questions}
      onExit={() => router.push("/learning")}
      onSubmit={async (answers) => {
        const result = await submitLessonAttempt(slug, userId, answers);
        try {
          // Finish the loop: the feed keeps a permanent row for this lesson.
          await recordFeedEntry({
            user_id: userId,
            kind: "lesson",
            lesson_title: data.title,
            score: result.score,
            total: result.total,
          });
        } catch {
          // The feed is a nicety — never hide the graded result because of it.
        }
        return result;
      }}
    />
  );
}
