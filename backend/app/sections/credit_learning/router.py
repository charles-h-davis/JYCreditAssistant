"""HTTP routes for the Credit Learning section (mounted at /api/v1/credit-learning)."""

from fastapi import APIRouter, HTTPException, status

from app.sections.credit_learning.schemas import LessonDetail, LessonSummary

router = APIRouter(prefix="/credit-learning", tags=["Credit Learning"])

NOT_IMPLEMENTED = {
    status.HTTP_501_NOT_IMPLEMENTED: {"description": "Not implemented yet (scaffold stub)."}
}


@router.get("/ping", summary="Health check for the Credit Learning section")
def ping() -> dict[str, str]:
    """Prove the router is mounted. Asserted by the section smoke test."""
    return {"section": "credit-learning", "status": "ok"}


@router.get(
    "/lessons",
    response_model=list[LessonSummary],
    summary="List available credit lessons",
    responses=NOT_IMPLEMENTED,
)
def list_lessons() -> list[LessonSummary]:
    """Return the lesson catalogue, newest first.

    TODO(credit_learning owner): delegate to `service.list_lessons`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="credit_learning.list_lessons is not implemented yet.",
    )


@router.get(
    "/lessons/{slug}",
    response_model=LessonDetail,
    summary="Fetch a single lesson by slug",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No lesson with that slug."},
        **NOT_IMPLEMENTED,
    },
)
def get_lesson(slug: str) -> LessonDetail:
    """Return one lesson including its body copy.

    TODO(credit_learning owner): delegate to `service.get_lesson(slug)`.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"credit_learning.get_lesson('{slug}') is not implemented yet.",
    )
