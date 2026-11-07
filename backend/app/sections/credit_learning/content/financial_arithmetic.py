"""Category 2 — Financial Arithmetic (3 lessons, 5 questions each)."""

from app.sections.credit_learning.content.models import Category, Lesson, Question

CATEGORY = Category(
    id="financial-arithmetic",
    title="Financial Arithmetic",
    position=2,
    lessons=(
        Lesson(
            slug="interest-and-apr",
            position=1,
            title="Interest and APR",
            summary=(
                "Interest is the price of borrowing, charged as a percentage over time. "
                "APR (annual "
                "percentage rate) bundles the interest rate with typical fees so you can compare "
                "offers like-for-like. A lower APR usually means cheaper borrowing, as long as you "
                "compare the same kind of product."
            ),
            questions=(
                Question(
                    1,
                    "What is interest?",
                    (
                        "A fee for borrowing, charged as a percentage over time",
                        "A tax on savings",
                        "A discount for early repayment",
                        "A reward for loyalty",
                    ),
                    0,
                    "Interest is the lender's charge for letting you use their money.",
                ),
                Question(
                    2,
                    "What does APR stand for?",
                    (
                        "Annual Percentage Rate",
                        "Average Payment Ratio",
                        "Applied Purchase Rate",
                        "Annual Principal Refund",
                    ),
                    0,
                    "APR is the annual percentage rate: interest plus typical fees, per year.",
                ),
                Question(
                    3,
                    "Two cards, same balance: A is 19.9% APR, B is 29.9% APR. Which costs more if "
                    "you carry the balance?",
                    (
                        "Card A",
                        "Card B",
                        "Both cost the same",
                        "It depends on the shop",
                    ),
                    1,
                    "A higher APR means more interest on the same balance.",
                ),
                Question(
                    4,
                    "Why is APR useful?",
                    (
                        "It lets you compare borrowing costs like-for-like",
                        "It tells you the minimum payment",
                        "It replaces your credit score",
                        "It sets your credit limit",
                    ),
                    0,
                    "APR standardises cost so offers can be compared fairly.",
                ),
                Question(
                    5,
                    "APR includes...",
                    (
                        "Interest plus typical fees",
                        "Only fees",
                        "Only interest",
                        "Nothing at all",
                    ),
                    0,
                    "APR bundles the rate with fees to reflect the true annual cost.",
                ),
            ),
        ),
        Lesson(
            slug="compound-interest-and-minimums",
            position=2,
            title="Compound interest and minimum payments",
            summary=(
                "If you do not clear a balance, interest is added and then itself earns interest. "
                "That is compounding, and the longer you leave it the faster the debt grows. "
                "Paying only the minimum keeps the balance alive for years; paying more each "
                "month shortens "
                "the debt and cuts total interest sharply."
            ),
            questions=(
                Question(
                    1,
                    "What is compounding on a credit card?",
                    (
                        "Interest charged on interest",
                        "A discount for loyalty",
                        "A fixed monthly fee",
                        "The annual fee",
                    ),
                    0,
                    "Unpaid interest joins the balance and starts earning interest too.",
                ),
                Question(
                    2,
                    "What does paying only the minimum do?",
                    (
                        "Clears the balance quickly",
                        "Keeps the balance and interest going for longer",
                        "Stops all interest",
                        "Increases your credit limit",
                    ),
                    1,
                    "Minimums are set low, so the balance lingers and accrues interest.",
                ),
                Question(
                    3,
                    (
                        "You owe $1,000 at about 24% APR and pay only the minimum. "
                        "What usually happens?"
                    ),
                    (
                        "Paid off within months",
                        "Can take years and cost far more than the original balance",
                        "Interest is waived",
                        "The balance doubles overnight",
                    ),
                    1,
                    "Minimum-only repayments stretch for years and multiply the interest paid.",
                ),
                Question(
                    4,
                    "Which change saves the most interest?",
                    (
                        "Paying more than the minimum each month",
                        "Paying later each month",
                        "Using the card more",
                        "Ignoring statements",
                    ),
                    0,
                    "Extra payments go straight at principal, shrinking future interest.",
                ),
                Question(
                    5,
                    "Why does time matter with compounding?",
                    (
                        "The longer you carry a balance, the more interest builds",
                        "Interest resets every month",
                        "Time has no effect on cost",
                        "Lenders refund interest after a year",
                    ),
                    0,
                    "Compounding snowballs: more time means more interest on interest.",
                ),
            ),
        ),
        Lesson(
            slug="amortisation-and-total-cost",
            position=3,
            title="Amortisation and total cost",
            summary=(
                "Amortisation is how each repayment splits between interest and principal. "
                "Early on, "
                "more of each payment covers interest; later, more reduces the balance. Total cost "
                "— principal plus interest plus fees — is the number that tells you whether a deal "
                "is actually cheap."
            ),
            questions=(
                Question(
                    1,
                    "What is amortisation?",
                    (
                        "Splitting payments between interest and principal over time",
                        "A type of insurance",
                        "A discount scheme",
                        "A credit score",
                    ),
                    0,
                    "Amortisation describes how each payment is divided over the life of the debt.",
                ),
                Question(
                    2,
                    "On a typical loan, early payments are mostly...",
                    (
                        "Interest",
                        "Principal",
                        "Fees",
                        "Refunds",
                    ),
                    0,
                    "Interest is calculated on a larger balance early, so it takes a bigger share.",
                ),
                Question(
                    3,
                    "What does total cost of credit mean?",
                    (
                        "The price tag only",
                        "Everything you repay: principal, interest and fees",
                        "The APR alone",
                        "The monthly payment",
                    ),
                    1,
                    "Total cost adds up every dollar you hand over for the borrowing.",
                ),
                Question(
                    4,
                    "Two loans, same amount and term: 10% APR versus 15% APR. Which has the higher "
                    "total cost?",
                    (
                        "The 10% loan",
                        "The 15% loan",
                        "They cost the same",
                        "You cannot tell",
                    ),
                    1,
                    "A higher rate on the same structure costs more overall.",
                ),
                Question(
                    5,
                    "Why compare total cost rather than just the monthly payment?",
                    (
                        "A smaller payment can mean a longer term and more interest overall",
                        "Monthly payments never matter",
                        "Total cost includes your salary",
                        "Lenders require it by law",
                    ),
                    0,
                    "Low monthly payments can hide a longer, pricier repayment schedule.",
                ),
            ),
        ),
    ),
)
