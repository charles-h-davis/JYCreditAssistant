import {
  amortise,
  monthsToLabel,
  minimumPayment,
  paymentCoversInterest,
  suggestPayment,
} from "./src/finance.js";
import { getCard, getSelectedCardId, saveResolvedCard } from "./src/config.js";
import { createPurchasePlan, extractImage, resolveCard } from "./src/api.js";
import { getSession } from "./src/auth.js";
import { captureVisibleTab } from "./src/capture.js";

const $ = (id) => document.getElementById(id);
const gbp = new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" });
const gbp0 = new Intl.NumberFormat("en-GB", {
  style: "currency",
  currency: "GBP",
  maximumFractionDigits: 0,
});

let card = null;
let product = null;
let session = null;
let sliderState = { value: 0, months: 0, extraMonths: 0, extraInterest: 0, payable: false };

function show(el, visible) {
  if (el) el.hidden = !visible;
}

function status(message) {
  $("status").textContent = message || "";
  show($("status"), Boolean(message));
}

function cardLabel(c) {
  if (!c) return "";
  const last4 = c.last_four ? "\u2022\u2022\u2022\u2022 " + c.last_four : "";
  return (c.nickname || "Card") + (last4 ? " " + last4 : "");
}

async function loadCard(activeSession) {
  if (activeSession && activeSession.user_id) {
    try {
      const fresh = await resolveCard(
        activeSession.user_id,
        await getSelectedCardId(),
      );
      await saveResolvedCard(fresh);
      return fresh;
    } catch {
      // Fall back to the cached/manual card below.
    }
  }
  return await getCard();
}

function renderProduct(data) {
  if (data && data.product_name) {
    $("product-name").textContent = data.product_name;
    show($("product-name"), true);
  }
  if (data && data.price != null) {
    $("price").textContent = gbp.format(data.price);
    $("source").textContent = "gemini";
    show($("price-row"), true);
    if (data.currency && data.currency !== "GBP") {
      $("currency-note").textContent =
        "Read as " + data.currency + "; the maths treats the amount as GBP.";
      show($("currency-note"), true);
    }
  }
  if (data && (data.product_name || data.price != null)) show($("product"), true);
}

function updateSaveUi() {
  const button = $("save-plan");
  const hint = $("save-hint");
  const signedIn = Boolean(session && session.user_id);
  const ready = Boolean(signedIn && card && product && sliderState.payable);
  button.disabled = !ready;

  if (ready) {
    hint.textContent =
      "Saving also sets " +
      cardLabel(card) +
      "'s monthly repayment to " +
      gbp0.format(sliderState.value) +
      ".";
    show(hint, true);
  } else if (!signedIn) {
    hint.textContent = "Sign in (Card settings) to save to planned purchases.";
    show(hint, true);
  } else if (!card) {
    hint.textContent = "Choose a card in settings to save.";
    show(hint, true);
  } else {
    show(hint, false);
  }
}

function setupSlider() {
  const balance = Number(card.current_balance) || 0;
  const apr = Number(card.purchase_apr) || 0;
  const total = balance + product.price;

  const min = minimumPayment(total, apr);
  const max = Math.max(Math.ceil(total * 100) / 100, min + 1);
  const guess =
    card.monthly_payment && card.monthly_payment > 0
      ? card.monthly_payment
      : suggestPayment(total, apr);
  const start = Math.min(Math.max(guess, min), max);

  const slider = $("slider");
  slider.min = String(min);
  slider.max = String(max);
  slider.step = "5";
  slider.value = String(start);
  $("min-label").textContent = gbp0.format(min);
  $("max-label").textContent = gbp0.format(max);

  show($("calc"), true);
  compute(start);
}

function compute(value) {
  const price = product.price;
  const balance = Number(card.current_balance) || 0;
  const apr = Number(card.purchase_apr) || 0;
  const total = balance + price;

  const payable = paymentCoversInterest(total, apr, value);
  const baseline = amortise(balance, apr, value);
  const withItem = amortise(total, apr, value);
  const extraInterest = Math.max(withItem.totalInterest - baseline.totalInterest, 0);
  const realCost = price + extraInterest;
  const extraMonths = Math.max(withItem.months - baseline.months, 0);

  sliderState = {
    value,
    months: withItem.months,
    extraMonths,
    extraInterest: Math.round(extraInterest * 100) / 100,
    payable,
  };

  $("cost-today").textContent = gbp.format(price);
  $("apr").textContent = apr + "%";
  $("monthly").textContent = gbp0.format(value);
  $("real-cost").textContent = gbp.format(realCost);
  $("debt-free").textContent =
    monthsToLabel(withItem.months) + (extraMonths ? " (+" + extraMonths + "m)" : "");
  $("extra-interest").textContent =
    "Includes " + gbp.format(extraInterest) + " of extra interest on this card.";
  show($("not-payable"), !payable);
  updateSaveUi();
}

function setPlanStatus(message, isError) {
  const box = $("plan-status");
  box.textContent = message || "";
  box.classList.toggle("error-text", Boolean(isError));
  show(box, Boolean(message));
}

function showConfirmation() {
  $("confirm-name").textContent =
    product && product.product_name ? product.product_name : "This item";
  $("confirm-price").textContent = gbp.format(product.price);
  $("confirm-real-cost").textContent = gbp.format(product.price + sliderState.extraInterest);
  $("confirm-extra").textContent = gbp.format(sliderState.extraInterest);
  $("confirm-monthly").textContent = gbp0.format(sliderState.value) + "/month";
  $("confirm-debt-free").textContent =
    monthsToLabel(sliderState.months) +
    (sliderState.extraMonths ? " (+" + sliderState.extraMonths + "m)" : "");
  $("confirm-card").textContent = cardLabel(card);
  show($("confirmation"), true);
}

async function savePlan() {
  if (!session || !session.user_id || !card || !product || !sliderState.payable) return;

  $("save-plan").disabled = true;
  setPlanStatus("", false);

  try {
    await createPurchasePlan({
      user_id: session.user_id,
      card_id: card.card_id,
      product_name: product.product_name ?? null,
      purchase_amount: product.price,
      currency: "GBP",
      monthly_payment: sliderState.value,
      months_to_payoff: sliderState.months,
      total_interest: sliderState.extraInterest,
    });
    // The backend also stored this as the card's current monthly payment.
    card.monthly_payment = sliderState.value;
    showConfirmation();
  } catch (error) {
    setPlanStatus(
      error && error.message ? error.message : "Couldn't add that purchase.",
      true,
    );
  } finally {
    updateSaveUi();
  }
}

async function run() {
  status("");
  show($("calc"), false);
  show($("product"), false);
  show($("product-name"), false);
  show($("price-row"), false);
  show($("currency-note"), false);
  show($("not-payable"), false);
  show($("card-label"), false);
  show($("save-hint"), false);
  setPlanStatus("", false);
  $("save-plan").disabled = true;
  $("price").textContent = "";
  $("source").textContent = "";
  product = null;
  sliderState = { value: 0, months: 0, extraMonths: 0, extraInterest: 0, payable: false };
  show($("confirmation"), false);

  session = await getSession();
  card = await loadCard(session);
  if (card) {
    $("card-label").textContent = "Card: " + cardLabel(card);
    show($("card-label"), true);
  }

  let data = null;
  try {
    const blob = await captureVisibleTab();
    data = await extractImage(blob);
  } catch (error) {
    status(error && error.message ? error.message : "Couldn't read this page.");
    updateSaveUi();
    return;
  }

  renderProduct(data);

  if (!data || data.price == null) {
    status("Couldn't read a price. Scroll so the price is visible, then press Re-read.");
    updateSaveUi();
    return;
  }
  if (!card) {
    status("Sign in and choose a card in settings to see the cost.");
    updateSaveUi();
    return;
  }

  product = data;
  status("");
  setupSlider();
}

function init() {
  $("options").addEventListener("click", () => chrome.runtime.openOptionsPage());
  $("reread").addEventListener("click", () => run());
  $("save-plan").addEventListener("click", () => savePlan());
  $("confirm-close").addEventListener("click", () => window.close());
  $("slider").addEventListener("input", (event) => compute(Number(event.target.value)));
  run();
}

init();



