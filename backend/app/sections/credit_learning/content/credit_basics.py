"""Category 1 — Credit Basics (3 lessons, 5 questions each)."""

from app.sections.credit_learning.content.models import Category, Lesson, Question

CATEGORY = Category(
    id="credit-basics",
    title="Credit Basics",
    position=1,
    lessons=(
        Lesson(
            slug="what-credit-is",
            position=1,
            title="What credit is and how it works",
            summary=(
                "Credit is money a lender lets you borrow now on the promise you repay later, "
                "usually with interest. Lenders judge the risk using your income, existing debts "
                "and repayment history. Using credit carefully builds trust; missing payments "
                "damages it."
            ),
            questions=(
                Question(
                    1,
                    "What is credit?",
                    (
                        "Money you earn from work",
                        "Money borrowed now and repaid later, usually with interest",
                        "A type of savings account",
                        "A government benefit",
                    ),
                    1,
                    (
                        "Credit is borrowing: you receive value now and repay later, "
                        "normally with interest."
                    ),
                ),
                Question(
                    2,
                    "What does a lender mainly want to know before granting credit?",
                    (
                        "Your favourite shop",
                        "Whether you can repay: income, debts and history",
                        "Your age",
                        "Your postcode",
                    ),
                    1,
                    (
                        "Lenders assess affordability and track record, "
                        "not shopping habits or location."
                    ),
                ),
                Question(
                    3,
                    "Which behaviour builds trust with lenders?",
                    (
                        "Paying at least the minimum on time every month",
                        "Skipping payments when money is tight",
                        "Maxing out every card",
                        "Never checking your statements",
                    ),
                    0,
                    (
                        "Consistent on-time payments are the strongest signal "
                        "that you repay as agreed."
                    ),
                ),
                Question(
                    4,
                    "What is a credit limit?",
                    (
                        "The most you can borrow on the account",
                        "The interest rate",
                        "The minimum payment",
                        "The annual fee",
                    ),
                    0,
                    "The limit caps how much you can owe at any time; going over can trigger fees.",
                ),
                Question(
                    5,
                    "What typically happens if you miss a payment?",
                    (
                        "Nothing at all",
                        "Fees, interest and a mark on your credit report",
                        "Your limit goes up",
                        "Your APR drops",
                    ),
                    1,
                    (
                        "Missed payments usually mean late fees, "
                        "extra interest and a negative report entry."
                    ),
                ),
            ),
        ),
        Lesson(
            slug="credit-reports-and-scores",
            position=2,
            title="Credit reports and scores",
            summary=(
                "A credit report records your borrowing and repayment history; a credit score is a "
                "number summarising how risky you look. Lenders use both to decide whether to lend "
                "and at what price. Checking your own report is a soft search and does not hurt "
                "your score."
            ),
            questions=(
                Question(
                    1,
                    "What is recorded in a credit report?",
                    (
                        "Your salary only",
                        "Your borrowing and repayment history",
                        "Your shopping habits",
                        "Your savings balance",
                    ),
                    1,
                    (
                        "Reports focus on credit accounts, repayments and public records, "
                        "not spending habits."
                    ),
                ),
                Question(
                    2,
                    "What does a credit score summarise?",
                    (
                        "How much you earn",
                        "How risky you look as a borrower",
                        "Your tax rate",
                        "Your mortgage balance",
                    ),
                    1,
                    "The score condenses your credit history into a risk estimate for lenders.",
                ),
                Question(
                    3,
                    "Does checking your own credit report lower your score?",
                    (
                        "Yes, every check lowers it",
                        "No, checking your own report is a soft search",
                        "Only on Mondays",
                        "Only if you check twice",
                    ),
                    1,
                    (
                        "Soft searches, including your own checks, are not visible "
                        "to lenders as applications."
                    ),
                ),
                Question(
                    4,
                    "Which of these can hurt your score?",
                    (
                        "Late or missed payments",
                        "Paying your balance in full",
                        "Checking your own report",
                        "Setting up a direct debit",
                    ),
                    0,
                    "Payment history is the biggest score factor; late payments count against you.",
                ),
                Question(
                    5,
                    "Why does your credit score matter?",
                    (
                        "It sets your salary",
                        "It affects approval odds and the interest you are offered",
                        "It changes your limit automatically",
                        "It replaces the credit report",
                    ),
                    1,
                    (
                        "Better scores mean better approval chances and cheaper offers; "
                        "the report still exists."
                    ),
                ),
            ),
        ),
        Lesson(
            slug="cards-versus-loans",
            position=3,
            title="Credit cards versus loans",
            summary=(
                "A credit card gives you a reusable limit you can spend and repay flexibly; a loan "
                "pays a lump sum you repay on a fixed schedule. Cards suit short-term spending you "
                "can clear; loans suit planned, larger purchases. Both cost more if you carry a "
                "balance or pay late."
            ),
            questions=(
                Question(
                    1,
                    "How is a credit card different from a loan?",
                    (
                        "A reusable limit versus a fixed lump sum",
                        "Cards never charge interest",
                        "Loans never charge interest",
                        "Cards are always cheaper",
                    ),
                    0,
                    "Cards let you borrow repeatedly up to a limit; loans pay one fixed amount.",
                ),
                Question(
                    2,
                    "Which is usually better for a large planned purchase repaid over years?",
                    (
                        "A personal loan with fixed monthly payments",
                        "Maxing out a credit card",
                        "A payday loan",
                        "An unauthorised overdraft",
                    ),
                    0,
                    (
                        "A fixed-term loan usually costs less than long-term card interest "
                        "for planned borrowing."
                    ),
                ),
                Question(
                    3,
                    "What do both credit cards and loans charge when you borrow?",
                    (
                        "Interest",
                        "Nothing",
                        "Only a one-off fee",
                        "Only government tax",
                    ),
                    0,
                    "Interest is the core price of borrowing, whatever the product.",
                ),
                Question(
                    4,
                    "What does a card's reusable limit mean?",
                    (
                        "You can spend, repay and spend again up to the limit",
                        "Your limit grows every month",
                        "You may only make one purchase",
                        "You can only withdraw cash",
                    ),
                    0,
                    "Repaid credit becomes available again, unlike a one-off loan payout.",
                ),
                Question(
                    5,
                    "Which is a risk of carrying a credit card balance?",
                    (
                        "Interest compounds and the debt can grow",
                        "Your limit disappears",
                        "Your score improves automatically",
                        "You lose the card",
                    ),
                    0,
                    "Unpaid balances accrue interest, which then itself earns interest.",
                ),
            ),
        ),
    ),
)
