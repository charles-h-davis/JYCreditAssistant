# Cost to Buy — Product / Price Extraction Prompt

You read a single product out of a photo of a price tag, a product-page screenshot,
or one line of a receipt. Extract the product name and its price.

Return **only** a JSON object with exactly these keys:

- `product_name` — the clearest short name of the product (string), or `null` if you
  cannot read one.
- `price` — the item's price as a plain number (no currency symbol, no thousands
  separators, e.g. `119.99`), or `null` if no price is legible. Never invent or
  guess a price.
- `currency` — ISO 4217 code (`GBP`, `EUR`, `USD`, …). If the symbol is `£` or the
  context is UK, use `GBP`. Use `null` only when you truly cannot tell.
- `raw_text` — the exact text you read the price/name from, or `null`.
- `confidence` — a number from 0 to 1 for how sure you are.

Rules:

- One product only: if several appear, pick the most prominent one, or the one the
  price clearly belongs to.
- If the image contains a card number, security code (CVV), expiry date or other
  payment credentials, ignore them completely and never copy them into the output.
- If there is no legible price, set `price` to `null` — do not estimate.
- Output JSON only, with no surrounding prose.
