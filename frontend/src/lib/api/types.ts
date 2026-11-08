/**
 * Types mirroring the FastAPI response models in `backend/app/sections/<section>/schemas.py`.
 * Money is always GBP; APRs are percentages (`24.99` means 24.99%).
 */

export interface CreditCard {
  id: string;
  user_id: string;
  nickname: string;
  issuer: string;
  last_four: string;
  credit_limit: number | null;
  current_balance: number;
  available_balance: number | null;
  purchase_apr: number | null;
  closing_day: number | null;
  statement_day: number | null;
  is_secured: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface CardTransaction {
  id: string;
  user_id: string;
  card_id: string;
  plaid_transaction_id: string;
  description: string | null;
  merchant_name: string | null;
  amount: number;
  category: string | null;
  authorized_date: string | null;
  posted_date: string | null;
  pending: boolean;
  iso_currency_code: string | null;
}

export interface MonthlyPayment {
  user_id: string;
  card_id: string;
  monthly_payment: number;
  updated_at: string | null;
}

export interface PurchasePlan {
  id: string;
  user_id: string;
  card_id: string;
  product_name: string | null;
  purchase_amount: number;
  currency: string;
  monthly_payment: number;
  months_to_payoff: number | null;
  total_interest: number | null;
  created_at: string | null;
}

export interface PurchasePlanCreate {
  user_id: string;
  card_id: string;
  product_name?: string | null;
  purchase_amount: number;
  monthly_payment: number;
  months_to_payoff?: number | null;
  total_interest?: number | null;
}

export interface ExtractResult {
  product_name: string | null;
  price: number | null;
  currency: string | null;
  raw_text: string | null;
  confidence: number | null;
  model: string | null;
}

export interface LessonProgress {
  id: string;
  slug: string;
  category_id: string;
  position: number;
  title: string;
  summary: string;
  question_count: number;
  completed: boolean;
  attempts: number;
  best_score: number | null;
  last_completed_at: string | null;
}

export interface CategoryProgress {
  id: string;
  title: string;
  position: number;
  lessons: LessonProgress[];
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
  active_today: boolean;
}

export interface Roadmap {
  streak: Streak;
  categories: CategoryProgress[];
}

export interface Question {
  id: string;
  lesson_id: string;
  lesson_slug: string;
  lesson_title: string;
  position: number;
  prompt: string;
  options: string[];
}

export interface LessonDetail {
  id: string;
  slug: string;
  category_id: string;
  category_title: string;
  position: number;
  title: string;
  summary: string;
  questions: Question[];
}

export interface AnswerResult {
  question_id: string;
  selected_index: number;
  correct_index: number;
  correct: boolean;
  explanation: string | null;
}

/** Instant verdict for one tap, from `POST /credit-learning/questions/{id}/answer`. */
export interface AnswerCheck {
  question_id: string;
  selected_index: number;
  correct_index: number;
  correct: boolean;
  explanation: string | null;
}

export interface AttemptResult {
  kind: "lesson" | "recap";
  lesson_id: string | null;
  score: number;
  total: number;
  answers: AnswerResult[];
  streak: Streak;
}

export interface Recap {
  questions: Question[];
}

export interface ChatReply {
  reply: string;
  in_scope: boolean;
  refused: boolean;
  model: string | null;
}

/* --- friends --------------------------------------------------------------- */

/** One friend on the user's list (`GET /friends`). A contact, not an account. */
export interface Friend {
  id: string;
  user_id: string;
  friend_name: string;
  friend_email: string;
  created_at: string | null;
}

/** Body of `POST /friends` — `name` is optional, the API derives it from the email. */
export interface FriendCreate {
  user_id: string;
  email: string;
  name?: string;
}

/* --- friends feed ---------------------------------------------------------- */

export type FeedKind = "lesson" | "recap" | "streak";

/** One row of the friends feed (`GET /friends-feed/feed`). */
export interface FeedEntry {
  id: string;
  actor: string;
  kind: FeedKind;
  action: string;
  detail: string | null;
  occurred_at: string;
  is_self: boolean;
}

export interface FriendsFeed {
  entries: FeedEntry[];
}

/** Body of `POST /friends-feed/entries`, sent once an attempt has been graded. */
export interface FeedEntryCreate {
  user_id: string;
  kind: "lesson" | "recap";
  lesson_title?: string | null;
  score: number;
  total: number;
}
