"""Category 5 — Managing Repayments (3 lessons, 5 questions each)."""

from app.sections.credit_learning.content.models import Category, Lesson, Question

CATEGORY = Category(
    id="managing-repayments",
    title="Managing Repayments",
    position=5,
    lessons=(
        Lesson(
            slug="statement-cycles-and-due-dates",
            position=1,
            title="Statement cycles, closing day and due day",
            summary=(
                "Each card has a statement cycle: the closing day ends the statement and the "
                "statement day (the due day) is when payment is due. Spending just after the "
                "closing "
                "day usually lands on the next statement. Knowing both dates helps you time "
                "purchases and never miss a payment."
            ),
            questions=(
                Question(
                    1,
                    "What does the closing day mark?",
                    (
                        "The end of the statement cycle",
                        "The payment due date",
                        "The day your APR changes",
                        "The day your limit increases",
                    ),
                    0,
                    "The closing day finalises the statement for that cycle.",
                ),
                Question(
                    2,
                    "The statement day is when...",
                    (
                        "Your payment is due",
                        "You close the account",
                        "Interest starts on every purchase",
                        "Your limit is renewed",
                    ),
                    0,
                    "In this product's wording, statement day is the payment due date.",
                ),
                Question(
                    3,
                    "A purchase made just after the closing day usually...",
                    (
                        "Appears on the next statement",
                        "Is completely free",
                        "Is charged twice",
                        "Cancels the statement",
                    ),
                    0,
                    "New spending starts a fresh cycle after the statement closes.",
                ),
                Question(
                    4,
                    "Why track closing and due dates?",
                    (
                        "To pay on time and plan spending",
                        "To raise your credit limit",
                        "To lower your APR automatically",
                        "To avoid statements",
                    ),
                    0,
                    "Timing payments and purchases around both dates avoids fees and interest.",
                ),
                Question(
                    5,
                    "Missing the due date usually causes...",
                    (
                        "Late fees, interest and possibly a report mark",
                        "Nothing at all",
                        "A refund",
                        "A higher credit score",
                    ),
                    0,
                    "Late payments are costly and can hurt your credit report.",
                ),
            ),
        ),
        Lesson(
            slug="minimum-versus-full-payments",
            position=2,
            title="Minimum versus full payments",
            summary=(
                "The minimum payment is the smallest amount that keeps the account "
                "in good standing, "
                "and it is designed to keep you borrowing. Paying the full statement "
                "balance avoids "
                "interest on purchases in most cases. If you cannot pay in full, paying a fixed "
                "amount above the minimum shortens the debt."
            ),
            questions=(
                Question(
                    1,
                    "What does paying the full statement balance usually do?",
                    (
                        "Avoids interest on purchases",
                        "Raises your APR",
                        "Lowers your credit limit",
                        "Extends the due date",
                    ),
                    0,
                    "Clearing the statement balance means no interest on those purchases.",
                ),
                Question(
                    2,
                    "The minimum payment is...",
                    (
                        "The smallest amount that keeps the account in good standing",
                        "The full balance",
                        "A reward for loyalty",
                        "The APR",
                    ),
                    0,
                    "Paying at least the minimum avoids late/default status.",
                ),
                Question(
                    3,
                    "Why can minimum payments be expensive?",
                    (
                        "They stretch repayment and maximise interest",
                        "They are always zero",
                        "They clear the balance fast",
                        "They avoid all fees",
                    ),
                    0,
                    "Low payments keep a balance alive for a long time.",
                ),
                Question(
                    4,
                    "If you cannot pay in full, what is better than the minimum?",
                    (
                        "A fixed amount above the minimum",
                        "Paying after the due date",
                        "Skipping payments",
                        "Doing nothing",
                    ),
                    0,
                    "Any extra above the minimum attacks the principal sooner.",
                ),
                Question(
                    5,
                    "What happens if you pay less than the minimum?",
                    (
                        "Fees, interest and possible late marks",
                        "Nothing",
                        "A discount",
                        "A higher credit score",
                    ),
                    0,
                    "Underpaying risks late fees and report entries.",
                ),
            ),
        ),
        Lesson(
            slug="payoff-strategies-and-late-fees",
            position=3,
            title="Payoff strategies and avoiding late fees",
            summary=(
                "Snowball targets the smallest balance first for quick wins; avalanche targets the "
                "highest APR first to save the most interest. Both beat drifting on "
                "minimums. Set up "
                "a direct debit for at least the minimum, and act fast if a payment is "
                "at risk: late "
                "fees and report marks cost more than the payment itself."
            ),
            questions=(
                Question(
                    1,
                    "Which strategy targets the highest APR first?",
                    (
                        "Avalanche",
                        "Snowball",
                        "Minimum-only",
                        "Balance transfer",
                    ),
                    0,
                    "Avalanche focuses extra payments on the most expensive debt.",
                ),
                Question(
                    2,
                    "Which strategy gives quick motivational wins?",
                    (
                        "Snowball",
                        "Avalanche",
                        "Minimum-only",
                        "Cash advance",
                    ),
                    0,
                    "Snowball clears the smallest balance first for momentum.",
                ),
                Question(
                    3,
                    "What is the best protection against late fees?",
                    (
                        "A direct debit for at least the minimum",
                        "Ignoring reminders",
                        "Using more credit",
                        "Closing the account",
                    ),
                    0,
                    "Automating at least the minimum prevents accidental misses.",
                ),
                Question(
                    4,
                    "Which usually costs the most over time?",
                    (
                        "Paying only the minimum",
                        "Avalanche",
                        "Paying in full",
                        "Snowball",
                    ),
                    0,
                    "Minimum-only repayment maximises interest paid.",
                ),
                Question(
                    5,
                    "Late payments can...",
                    (
                        "Trigger fees, interest and a report mark",
                        "Improve your credit score",
                        "Waive interest",
                        "Raise your credit limit",
                    ),
                    0,
                    "Lateness is costly and visible to future lenders.",
                ),
            ),
        ),
    ),
)
