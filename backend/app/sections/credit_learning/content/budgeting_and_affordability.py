"""Category 3 — Budgeting and Affordability (3 lessons, 5 questions each)."""

from app.sections.credit_learning.content.models import Category, Lesson, Question

CATEGORY = Category(
    id="budgeting-and-affordability",
    title="Budgeting and Affordability",
    position=3,
    lessons=(
        Lesson(
            slug="income-expenses-and-cash-flow",
            position=1,
            title="Income, expenses and cash flow",
            summary=(
                "Cash flow is money in versus money out. Start with your take-home income, list "
                "fixed and variable expenses, and see what is left. A simple monthly budget shows "
                "whether a new credit payment fits before you sign up for it."
            ),
            questions=(
                Question(
                    1,
                    "What is cash flow?",
                    (
                        "Money coming in versus money going out",
                        "Your credit score",
                        "Your APR",
                        "Your savings rate",
                    ),
                    0,
                    "Cash flow tracks income against spending over a period.",
                ),
                Question(
                    2,
                    "Which of these is a fixed expense?",
                    (
                        "Rent",
                        "Groceries",
                        "Cinema tickets",
                        "Birthday gifts",
                    ),
                    0,
                    "Fixed expenses stay broadly the same each month.",
                ),
                Question(
                    3,
                    "Why budget before taking on credit?",
                    (
                        "To check a new payment actually fits",
                        "To raise your credit limit",
                        "To lower your APR automatically",
                        "To avoid statements",
                    ),
                    0,
                    "A budget shows whether the monthly payment is affordable before you commit.",
                ),
                Question(
                    4,
                    "Take-home pay is $2,400 and expenses are $2,150. What is left?",
                    (
                        "$250",
                        "$150",
                        "$350",
                        "$0",
                    ),
                    0,
                    "2400 - 2150 = 250.",
                ),
                Question(
                    5,
                    "Which of these is a variable expense?",
                    (
                        "Utility bills that change with usage",
                        "Rent",
                        "A fixed loan payment",
                        "An insurance premium",
                    ),
                    0,
                    "Variable expenses move with usage or choices, like energy bills.",
                ),
            ),
        ),
        Lesson(
            slug="needs-wants-and-emergency-buffer",
            position=2,
            title="Needs, wants and an emergency buffer",
            summary=(
                "Needs keep you housed, fed and working; wants are optional. "
                "Cover needs first, then "
                "build a small emergency buffer so an unexpected bill does not land on a credit "
                "card. Even a few hundred dollars of buffer prevents expensive debt spirals."
            ),
            questions=(
                Question(
                    1,
                    "Which of these is a need?",
                    (
                        "Rent",
                        "A streaming subscription",
                        "New trainers",
                        "A concert ticket",
                    ),
                    0,
                    "Housing is a core need; the others are optional wants.",
                ),
                Question(
                    2,
                    "Why keep an emergency buffer?",
                    (
                        "So surprise bills do not become card debt",
                        "To raise your credit limit",
                        "To improve your APR",
                        "To avoid budgeting",
                    ),
                    0,
                    "A buffer absorbs shocks without new borrowing.",
                ),
                Question(
                    3,
                    "Which of these is a want?",
                    (
                        "Takeaway coffee",
                        "Electricity",
                        "Bus fare to work",
                        "Basic groceries",
                    ),
                    0,
                    "A takeaway coffee is optional spending, unlike utilities or commuting.",
                ),
                Question(
                    4,
                    "After covering needs, what is a sensible next step?",
                    (
                        "Build a small emergency fund",
                        "Max out a card",
                        "Take a payday loan",
                        "Skip saving entirely",
                    ),
                    0,
                    "A small fund prevents future high-cost borrowing.",
                ),
                Question(
                    5,
                    "How does a buffer help your credit health?",
                    (
                        "Fewer panic borrowings and missed payments",
                        "It raises your score instantly",
                        "It removes interest",
                        "It increases your limit",
                    ),
                    0,
                    "Less emergency borrowing means fewer missed or late payments.",
                ),
            ),
        ),
        Lesson(
            slug="debt-to-income-and-affordability",
            position=3,
            title="Debt-to-income and affordability checks",
            summary=(
                "Lenders compare what you owe with what you earn: a debt-to-income (DTI) ratio. "
                "Lower DTI means more room for a new payment and better approval odds. A safe rule "
                "of thumb is keeping total debt payments to a modest share of your take-home pay."
            ),
            questions=(
                Question(
                    1,
                    "What is debt-to-income?",
                    (
                        "Debt payments compared with income",
                        "Debt compared with your credit limit",
                        "Income compared with savings",
                        "APR compared with fees",
                    ),
                    0,
                    "DTI expresses monthly debt payments as a share of income.",
                ),
                Question(
                    2,
                    "Which action lowers your DTI?",
                    (
                        "Paying down debt or increasing income",
                        "Taking another loan",
                        "Maxing out cards",
                        "Missing payments",
                    ),
                    0,
                    "Less debt or more income shrinks the ratio.",
                ),
                Question(
                    3,
                    "Income is $3,000 a month and debt payments are $600. What is the DTI?",
                    (
                        "20%",
                        "15%",
                        "30%",
                        "60%",
                    ),
                    0,
                    "600 / 3000 = 20%.",
                ),
                Question(
                    4,
                    "Why do lenders check DTI?",
                    (
                        "To judge whether you can afford more borrowing",
                        "To set the APR exactly",
                        "To decide your job",
                        "To calculate tax",
                    ),
                    0,
                    "DTI is a quick affordability check.",
                ),
                Question(
                    5,
                    "Which is a sensible affordability rule?",
                    (
                        "Keep total debt payments a modest share of take-home pay",
                        "Borrow up to every limit",
                        "Rely on future raises",
                        "Ignore monthly payments",
                    ),
                    0,
                    "Keeping debt payments modest leaves room for surprises.",
                ),
            ),
        ),
    ),
)
