"""HTTP routes for the Credit Learning section (mounted at /api/v1/credit-learning).

There is no JWT auth dependency yet, so user-scoped endpoints take an explicit
``user_id`` and the router injects the service-role Supabase client; every
repository query filters on that id.

``TODO(credit_learning)``: replace the `user_id` parameters with the Supabase JWT
subject and `get_supabase_admin` with `get_supabase` once auth exists.
"""

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.core.database import get_supabase_admin
from app.sections.credit_learning import service
from app.sections.credit_learning.schemas import (
    AnswerCheck,
    AnswerCheckRequest,
    AttemptResult,
    LessonAttemptRequest,
    LessonDetail,
    LessonSummary,
    ProgressResponse,
    RecapAttemptRequest,
    RecapResponse,
    RoadmapResponse,
)

router = APIRouter(prefix="/credit-learning", tags=["Credit Learning"])


@router.get("/ping", summary="Health check for the Credit Learning section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "credit-learning", "status": "ok"}


@router.get(
    "/roadmap",
    response_model=RoadmapResponse,
    summary="Learning roadmap with the user's progress and streak",
    responses={422: {"description": "Missing or empty user_id."}},
)
def get_roadmap(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the progress (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> RoadmapResponse:
    """Return the five categories, their lessons, completion state and the streak."""
    return service.get_roadmap(client, user_id=user_id)


@router.get(
    "/lessons",
    response_model=list[LessonSummary],
    summary="List the lesson catalogue",
)
def list_lessons(
    client: Client = Depends(get_supabase_admin),
) -> list[LessonSummary]:
    """Return every published lesson with its category and question count."""
    return service.list_lessons(client)


@router.get(
    "/lessons/{slug}",
    response_model=LessonDetail,
    summary="Fetch a lesson's summary and questions",
    responses={404: {"description": "No lesson with that slug."}},
)
def get_lesson(
    slug: str,
    client: Client = Depends(get_supabase_admin),
) -> LessonDetail:
    """Return one lesson with its five questions. Correct answers are withheld."""
    return service.get_lesson(client, slug=slug)


@router.post(
    "/questions/{question_id}/answer",
    response_model=AnswerCheck,
    summary="Check one answer for instant feedback",
    responses={404: {"description": "No question with that id."}},
)
def check_answer(
    question_id: str,
    payload: AnswerCheckRequest,
    client: Client = Depends(get_supabase_admin),
) -> AnswerCheck:
    """Grade a single answer so the lesson runner can react on tap.

    The correct option and explanation are only returned once the learner has
    committed to an answer — lesson payloads still withhold them.
    """
    return service.check_answer(
        client, question_id=question_id, selected_index=payload.selected_index
    )


@router.post(
    "/lessons/{slug}/attempt",
    response_model=AttemptResult,
    summary="Submit a lesson attempt (any score completes it)",
    responses={
        404: {"description": "No lesson with that slug."},
        409: {"description": "The lesson has no questions."},
        422: {"description": "Answers do not match the lesson's questions."},
    },
)
def submit_lesson_attempt(
    slug: str,
    payload: LessonAttemptRequest,
    client: Client = Depends(get_supabase_admin),
) -> AttemptResult:
    """Grade the answers, mark the lesson completed and count today for the streak.

    Retakes are unlimited: each submission bumps the attempt count, keeps the
    best score and — if it happens on a new consecutive day — extends the streak.
    """
    return service.submit_lesson_attempt(client, slug=slug, request=payload)


@router.get(
    "/progress",
    response_model=ProgressResponse,
    summary="Completed lessons and the current streak",
    responses={422: {"description": "Missing or empty user_id."}},
)
def get_progress(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the progress (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> ProgressResponse:
    """Return every completed lesson with attempt stats plus the streak."""
    return service.get_progress(client, user_id=user_id)


@router.get(
    "/recap",
    response_model=RecapResponse,
    summary="Five random questions from the user's completed lessons",
    responses={
        409: {"description": "The user has not completed a lesson yet."},
        422: {"description": "Missing or empty user_id."},
    },
)
def get_recap(
    user_id: str = Query(
        ...,
        min_length=1,
        description="Supabase auth user id that owns the progress (temporary until JWT auth).",
    ),
    client: Client = Depends(get_supabase_admin),
) -> RecapResponse:
    """Serve recap questions drawn from lessons the user has completed at least once."""
    return service.get_recap(client, user_id=user_id)


@router.post(
    "/recap/attempt",
    response_model=AttemptResult,
    summary="Submit a recap attempt (counts towards the streak)",
    responses={
        409: {"description": "The user has not completed a lesson yet."},
        422: {"description": "Answers do not match the recap question set."},
    },
)
def submit_recap_attempt(
    payload: RecapAttemptRequest,
    client: Client = Depends(get_supabase_admin),
) -> AttemptResult:
    """Grade a recap round and count today towards the streak."""
    return service.submit_recap_attempt(client, request=payload)
