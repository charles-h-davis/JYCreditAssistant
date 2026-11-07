"""Category 4 — Comparing Credit Options (3 lessons, 5 questions each)."""

from app.sections.credit_learning.content.models import Category, Lesson, Question

CATEGORY = Category(
    id="comparing-credit-options",
    title="Comparing Credit Options",
    position=4,
    lessons=(
        Lesson(
            slug="apr-fees-and-total-cost",
            position=1,
            title="APR, fees and total cost",
            summary=(
                "Two offers with the same headline rate can cost very different amounts once fees "
                "are added. Compare APR, annual or arrangement fees, and the total you will repay "
                "over the term. The cheapest-looking monthly payment can hide "
                "a longer, pricier deal."
            ),
            questions=(
                Question(
                    1,
                    "A 0% card with a 3% transfer fee versus one with no fee: what should you "
                    "compare?",
                    (
                        "APR, fees and total cost",
                        "Only the transfer fee",
                        "Only the headline rate",
                        "Only the monthly payment",
                    ),
                    0,
                    "Total cost captures rate, fees and term together.",
                ),
                Question(
                    2,
                    "Which can make an offer more expensive despite a low rate?",
                    (
                        "Annual and arrangement fees",
                        "Paying on time",
                        "Clearing the balance",
                        "Using a comparison site",
                    ),
                    0,
                    "Fees are added cost that a headline rate can hide.",
                ),
                Question(
                    3,
                    "Same APR but a longer term means...",
                    (
                        "More total interest",
                        "Less total interest",
                        "The same interest",
                        "No interest at all",
                    ),
                    0,
                    "Interest accrues for longer, so the total goes up.",
                ),
                Question(
                    4,
                    "What is the best single comparison number?",
                    (
                        "Total cost over the term",
                        "The monthly payment alone",
                        "The credit limit",
                        "The colour of the card",
                    ),
                    0,
                    "Total cost is what you actually pay.",
                ),
                Question(
                    5,
                    "A small monthly payment can hide...",
                    (
                        "A longer, more expensive deal",
                        "A cheaper deal",
                        "A higher limit",
                        "A better credit score",
                    ),
                    0,
                    "Low payments often mean longer terms and more interest.",
                ),
            ),
        ),
        Lesson(
            slug="intro-offers-and-balance-transfers",
            position=2,
            title="0% intro offers and balance transfers",
            summary=(
                "0% purchase and balance-transfer offers can save real money, if you clear the "
                "balance before the promotion ends. After the intro period the standard APR "
                "usually applies to whatever is left. Watch transfer fees and any rule that new "
                "spending is "
                "charged at the normal rate."
            ),
            questions=(
                Question(
                    1,
                    "What happens when a 0% intro period ends?",
                    (
                        "The 0% rate ends and the standard APR applies",
                        "The card is cancelled",
                        "Your limit disappears",
                        "Your score drops to zero",
                    ),
                    0,
                    "Promotional rates are temporary; the standard APR takes over.",
                ),
                Question(
                    2,
                    "What usually makes a balance transfer worthwhile?",
                    (
                        "Clearing the balance before the promotion ends",
                        "Spending more during the offer",
                        "Paying late",
                        "Taking a cash advance",
                    ),
                    0,
                    "The saving only lands if the balance is gone before the 0% period ends.",
                ),
                Question(
                    3,
                    "A typical balance-transfer fee is...",
                    (
                        "A percentage of the amount transferred",
                        "Always zero",
                        "A fixed $1 fee",
                        "Your APR",
                    ),
                    0,
                    "Transfer fees are usually a few percent of the moved balance.",
                ),
                Question(
                    4,
                    "What is a common trap with promotional cards?",
                    (
                        "New spending or a leftover balance charged at the standard APR",
                        "Free money forever",
                        "No statements during the offer",
                        "Automatic repayment",
                    ),
                    0,
                    "Mixed spending and leftover balances can trigger the normal rate.",
                ),
                Question(
                    5,
                    "Which statement is true?",
                    (
                        "Intro offers are only cheap if you stick to the plan",
                        "0% lasts forever",
                        "Fees never apply",
                        "Transfers improve your score instantly",
                    ),
                    0,
                    "Discipline and timing determine whether the offer saves money.",
                ),
            ),
        ),
        Lesson(
            slug="secured-and-credit-building",
            position=3,
            title="Secured cards and credit-building options",
            summary=(
                "If your score is thin or poor, secured cards and specialist "
                "credit-builder products "
                "can help. They usually come with smaller limits and higher APRs, so pay in full "
                "where you can. A few months of on-time payments can unlock better deals."
            ),
            questions=(
                Question(
                    1,
                    "What is a secured card?",
                    (
                        "A card backed by a cash deposit",
                        "A card with no spending limit",
                        "A store loyalty card",
                        "A type of personal loan",
                    ),
                    0,
                    "The deposit reduces the lender's risk and usually sets the limit.",
                ),
                Question(
                    2,
                    "Why use a credit-builder product?",
                    (
                        "To build payment history when options are limited",
                        "To borrow large sums cheaply",
                        "To avoid statements",
                        "To skip interest forever",
                    ),
                    0,
                    "It is a stepping stone to better credit, not cheap large borrowing.",
                ),
                Question(
                    3,
                    "Secured cards usually have...",
                    (
                        "Smaller limits and higher APRs",
                        "Huge limits and 0% APR",
                        "No fees at all",
                        "No reporting to credit bureaus",
                    ),
                    0,
                    "Risk-based pricing means modest limits and higher rates.",
                ),
                Question(
                    4,
                    "What is the best way to use a secured card?",
                    (
                        "Small spending, paid in full and on time",
                        "Maxing it out immediately",
                        "Missing the odd payment",
                        "Never using it",
                    ),
                    0,
                    "Low usage with on-time full payments builds history safely.",
                ),
                Question(
                    5,
                    "What improves access to better deals over time?",
                    (
                        "Consistent on-time payments",
                        "Applying for lots of new credit",
                        "Missing payments",
                        "Keeping high balances",
                    ),
                    0,
                    "A clean repayment record is the strongest signal to lenders.",
                ),
            ),
        ),
    ),
)
