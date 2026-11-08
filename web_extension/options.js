import {
  getConnection,
  saveConnection,
  getSelectedCardId,
  setSelectedCardId,
  saveResolvedCard,
  saveManualCard,
  getManualCard,
} from "./src/config.js";
import { getSession, signIn, signOut } from "./src/auth.js";
import { listCards, resolveCard } from "./src/api.js";

const $ = (id) => document.getElementById(id);
const gbp = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });

function showError(message) {
  $("error").textContent = message || "";
  $("error").hidden = !message;
}

function flash(id) {
  const el = $(id);
  el.hidden = false;
  setTimeout(() => {
    el.hidden = true;
  }, 1500);
}

async function loadConnection() {
  const conn = await getConnection();
  $("supabase-url").value = conn.supabaseUrl;
  $("supabase-anon").value = conn.supabaseAnonKey;
  $("backend-url").value = conn.backendBaseUrl;
}

$("save-connection").addEventListener("click", async () => {
  await saveConnection({
    supabaseUrl: $("supabase-url").value.trim(),
    supabaseAnonKey: $("supabase-anon").value.trim(),
    backendBaseUrl: $("backend-url").value.trim(),
  });
  flash("connection-saved");
});

function setSignedIn(session) {
  const status = $("account-status");
  if (session && session.user_id) {
    status.textContent = "Signed in as " + (session.email || session.user_id);
    $("signin-form").hidden = true;
    $("signout").hidden = false;
  } else {
    status.textContent = "Not signed in.";
    $("signin-form").hidden = false;
    $("signout").hidden = true;
  }
}

$("signin").addEventListener("click", async () => {
  showError("");
  const email = $("email").value.trim();
  const password = $("password").value;
  if (!email || !password) {
    showError("Enter your email and password.");
    return;
  }
  try {
    const session = await signIn(email, password);
    setSignedIn(session);
    $("password").value = "";
    await refreshCards();
  } catch (error) {
    showError(error.message);
  }
});

$("signout").addEventListener("click", async () => {
  await signOut();
  setSignedIn(null);
  $("card-select").innerHTML = '<option value="">Sign in first</option>';
  $("card-select").disabled = true;
  $("card-summary").hidden = true;
});

function populateSelect(cards) {
  const select = $("card-select");
  select.innerHTML = "";
  if (!cards.length) {
    select.innerHTML = '<option value="">No cards found</option>';
    select.disabled = true;
    return;
  }
  for (const card of cards) {
    const option = document.createElement("option");
    option.value = card.id;
    option.textContent =
      (card.nickname || card.issuer || "Card") +
      (card.last_four ? " \u2022\u2022\u2022\u2022 " + card.last_four : "");
    select.appendChild(option);
  }
  select.disabled = false;
}

function showSummary(card) {
  const payment = card.monthly_payment == null ? "not set" : gbp.format(card.monthly_payment);
  const apr = card.purchase_apr == null ? "\u2014" : card.purchase_apr + "%";
  $("card-summary").textContent =
    (card.nickname || "Card") +
    ": balance " +
    gbp.format(card.current_balance) +
    ", APR " +
    apr +
    ", monthly payment " +
    payment +
    ".";
  $("card-summary").hidden = false;
}

async function useCard(cardId) {
  const session = await getSession();
  if (!session || !session.user_id || !cardId) return;
  try {
    const card = await resolveCard(session.user_id, cardId);
    await saveResolvedCard(card);
    await setSelectedCardId(card.card_id);
    showSummary(card);
  } catch (error) {
    showError(error.message);
  }
}

async function refreshCards() {
  showError("");
  const session = await getSession();
  if (!session || !session.user_id) {
    $("card-select").innerHTML = '<option value="">Sign in first</option>';
    $("card-select").disabled = true;
    return;
  }
  try {
    const cards = await listCards(session.user_id);
    populateSelect(cards);
    if (cards && cards.length) {
      const savedId = await getSelectedCardId();
      const chosen = cards.some((card) => card.id === savedId) ? savedId : cards[0].id;
      $("card-select").value = chosen;
      await useCard(chosen);
    }
  } catch (error) {
    showError(error.message);
  }
}

$("refresh-cards").addEventListener("click", () => refreshCards());
$("card-select").addEventListener("change", () => useCard($("card-select").value));

$("save-manual").addEventListener("click", async () => {
  await saveManualCard({
    nickname: "Manual card",
    current_balance: Number($("m-balance").value) || 0,
    purchase_apr: Number($("m-apr").value) || 0,
    monthly_payment: Number($("m-payment").value) || 0,
  });
  flash("manual-saved");
});

async function init() {
  await loadConnection();
  const manual = await getManualCard();
  if (manual) {
    $("m-balance").value = String(manual.current_balance ?? "");
    $("m-apr").value = String(manual.purchase_apr ?? "");
    $("m-payment").value = String(manual.monthly_payment ?? "");
  }
  const session = await getSession();
  setSignedIn(session);
  if (session && session.user_id) await refreshCards();
}

init();
