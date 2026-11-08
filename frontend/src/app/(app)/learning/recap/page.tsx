"use client";

import { useRouter } from "next/navigation";
import useSWR from "swr";
import { LessonRunner } from "@/components/learning/lesson-runner";
import { LoadingSplash } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/primitives";
import { getRecap, recordFeedEntry, submitRecapAttempt } from "@/lib/api/endpoints";
import { useSession } from "@/lib/state/session";

/**
 * The "refresh lesson": five random questions drawn from lessons the user has
 * already completed. Counts towards the streak like a normal lesson.
 */
export default function RecapPage() {
  const router = useRouter();
  const { userId } = useSession();

  const { data, error, isLoading } = useSWR(userId ? `recap:${userId}` : null, () =>
    getRecap(userId as string),
  );

  if (isLoading) return <LoadingSplash label="Building your refresh round" />;

  if (error || !data || data.questions.length === 0 || !userId) {
    return (
      <main className="app-column grid min-h-dvh place-items-center bg-page px-6">
        <EmptyState
          title="Nothing to refresh yet"
          body={
            error?.status === 409
              ? "Complete a lesson first — the refresh pulls questions from lessons you've finished."
              : (error?.message ?? "No completed lessons to draw questions from.")
          }
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
      eyebrow="Refresh lesson"
      title="Mixed recap"
      summary="Five questions pulled from lessons you've already completed. Answering any of them keeps your streak alive."
      submitLabel="Start recap"
      questions={data.questions}
      onExit={() => router.push("/learning")}
      onSubmit={async (answers) => {
        const result = await submitRecapAttempt(userId, answers);
        try {
          // Refresh rounds show up in the feed alongside finished lessons.
          await recordFeedEntry({
            user_id: userId,
            kind: "recap",
            score: result.score,
            total: result.total,
          });
        } catch {
          // Best effort — the graded result always wins.
        }
        return result;
      }}
    />
  );
}
