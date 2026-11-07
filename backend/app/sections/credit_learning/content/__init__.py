"""The credit-learning roadmap: five categories, three lessons each.

Order matters: categories and lessons are presented in the order defined here
(`position` is 1-based). Each lesson has a summary plus five questions.
"""

from app.sections.credit_learning.content.budgeting_and_affordability import (
    CATEGORY as BUDGETING_AND_AFFORDABILITY,
)
from app.sections.credit_learning.content.comparing_credit_options import (
    CATEGORY as COMPARING_CREDIT_OPTIONS,
)
from app.sections.credit_learning.content.credit_basics import CATEGORY as CREDIT_BASICS
from app.sections.credit_learning.content.financial_arithmetic import (
    CATEGORY as FINANCIAL_ARITHMETIC,
)
from app.sections.credit_learning.content.managing_repayments import (
    CATEGORY as MANAGING_REPAYMENTS,
)
from app.sections.credit_learning.content.models import Category, Lesson, Question

CATEGORIES: tuple[Category, ...] = (
    CREDIT_BASICS,
    FINANCIAL_ARITHMETIC,
    BUDGETING_AND_AFFORDABILITY,
    COMPARING_CREDIT_OPTIONS,
    MANAGING_REPAYMENTS,
)

__all__ = ["CATEGORIES", "Category", "Lesson", "Question"]
