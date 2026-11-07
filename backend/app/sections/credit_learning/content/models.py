"""Typed shape of the credit-learning roadmap content.

The roadmap is stored in the database at runtime; these dataclasses are the
source that `seed.py` loads into Supabase (and that the tests validate).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    """One multiple-choice question inside a lesson."""

    position: int
    prompt: str
    options: tuple[str, str, str, str]
    correct_index: int
    explanation: str


@dataclass(frozen=True)
class Lesson:
    """One learning task: a summary plus exactly five questions."""

    slug: str
    position: int
    title: str
    summary: str
    questions: tuple[Question, ...]


@dataclass(frozen=True)
class Category:
    """One roadmap category with exactly three lessons."""

    id: str
    title: str
    position: int
    lessons: tuple[Lesson, ...]
