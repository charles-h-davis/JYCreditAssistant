import { ApiError, apiRequest, withUser } from "@/lib/api/client";
import type {
  AnswerCheck,
  AttemptResult,
  CardTransaction,
  ChatReply,
  CreditCard,
  DismissalCreate,
  ExtractResult,
  FeedEntry,
  FeedEntryCreate,
  Friend,
  FriendCreate,
  FriendsFeed,
  LessonDetail,
  MonthlyPayment,
  NotificationsFeed,
  PurchasePlan,
  PurchasePlanCreate,
  Recap,
  Roadmap,
} from "@/lib/api/types";

/* --- card storage ---------------------------------------------------------- */

export function listCards(userId: string): Promise<CreditCard[]> {
  return apiRequest<CreditCard[]>(withUser("/card-storage/cards", userId));
}

export function listCardTransactions(
  userId: string,
  cardId: string,
): Promise<CardTransaction[]> {
  return apiRequest<CardTransaction[]>(
    withUser(`/card-storage/cards/${cardId}/transactions`, userId),
  );
}

/* --- cost to buy ----------------------------------------------------------- */

export async function getMonthlyPayment(
  userId: string,
  cardId: string,
): Promise<MonthlyPayment | null> {
  try {
    return await apiRequest<MonthlyPayment>(
      withUser(`/cost-to-buy/monthly-payment?card_id=${encodeURIComponent(cardId)}`, userId),
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export function setMonthlyPayment(
  userId: string,
  cardId: string,
  monthlyPayment: number,
): Promise<MonthlyPayment> {
  return apiRequest<MonthlyPayment>("/cost-to-buy/monthly-payment", {
    method: "PUT",
    json: { user_id: userId, card_id: cardId, monthly_payment: monthlyPayment },
  });
}

export function listPurchasePlans(userId: string): Promise<PurchasePlan[]> {
  return apiRequest<PurchasePlan[]>(
    withUser("/cost-to-buy/purchase-plans", userId),
  );
}

export function createPurchasePlan(payload: PurchasePlanCreate): Promise<PurchasePlan> {
  return apiRequest<PurchasePlan>("/cost-to-buy/purchase-plans", {
    method: "POST",
    json: payload,
  });
}

export function deletePurchasePlan(userId: string, planId: string): Promise<void> {
  return apiRequest<void>(
    withUser(`/cost-to-buy/purchase-plans/${planId}`, userId),
    { method: "DELETE" },
  );
}

export function extractProduct(file: File): Promise<ExtractResult> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<ExtractResult>("/cost-to-buy/extract", { method: "POST", body });
}

/* --- credit learning ------------------------------------------------------- */

export function getRoadmap(userId: string): Promise<Roadmap> {
  return apiRequest<Roadmap>(withUser("/credit-learning/roadmap", userId));
}

export function getLesson(slug: string): Promise<LessonDetail> {
  return apiRequest<LessonDetail>(`/credit-learning/lessons/${slug}`);
}

/** Grade one option on tap, so the runner can give feedback immediately. */
export function checkAnswer(questionId: string, selectedIndex: number): Promise<AnswerCheck> {
  return apiRequest<AnswerCheck>(`/credit-learning/questions/${questionId}/answer`, {
    method: "POST",
    json: { selected_index: selectedIndex },
  });
}

export function submitLessonAttempt(
  slug: string,
  userId: string,
  answers: { question_id: string; selected_index: number }[],
): Promise<AttemptResult> {
  return apiRequest<AttemptResult>(`/credit-learning/lessons/${slug}/attempt`, {
    method: "POST",
    json: { user_id: userId, answers },
  });
}

export function getRecap(userId: string): Promise<Recap> {
  return apiRequest<Recap>(withUser("/credit-learning/recap", userId));
}

export function submitRecapAttempt(
  userId: string,
  answers: { question_id: string; selected_index: number }[],
): Promise<AttemptResult> {
  return apiRequest<AttemptResult>("/credit-learning/recap/attempt", {
    method: "POST",
    json: { user_id: userId, answers },
  });
}

/* --- AI assistant ---------------------------------------------------------- */

export function askAssistant(message: string): Promise<ChatReply> {
  return apiRequest<ChatReply>("/ai-assistant/chat", {
    method: "POST",
    json: { message },
  });
}

/* --- notifications --------------------------------------------------------- */

/** Planned purchases that look like they have already been bought. */
export function getNotifications(userId: string): Promise<NotificationsFeed> {
  return apiRequest<NotificationsFeed>(withUser("/notifications", userId));
}

/** Answer ✗: keep the planned purchase, stop notifying about this pair. */
export function dismissPurchaseMatch(payload: DismissalCreate): Promise<void> {
  return apiRequest<void>("/notifications/dismissals", {
    method: "POST",
    json: payload,
  });
}

/* --- friends --------------------------------------------------------------- */

export function listFriends(userId: string): Promise<Friend[]> {
  return apiRequest<Friend[]>(withUser("/friends", userId));
}

export function addFriend(payload: FriendCreate): Promise<Friend> {
  return apiRequest<Friend>("/friends", { method: "POST", json: payload });
}

export function removeFriend(userId: string, friendId: string): Promise<void> {
  return apiRequest<void>(withUser(`/friends/${friendId}`, userId), { method: "DELETE" });
}

/* --- friends feed ---------------------------------------------------------- */

/** Latest feed entries: hardcoded friend activity plus the user's own completions. */
export function getFriendsFeed(userId: string, limit?: number): Promise<FriendsFeed> {
  const size = limit === undefined ? "" : `&limit=${limit}`;
  return apiRequest<FriendsFeed>(`${withUser("/friends-feed/feed", userId)}${size}`);
}

/** Record a finished lesson or refresh round so it shows up in the feed. */
export function recordFeedEntry(payload: FeedEntryCreate): Promise<FeedEntry> {
  return apiRequest<FeedEntry>("/friends-feed/entries", {
    method: "POST",
    json: payload,
  });
}
