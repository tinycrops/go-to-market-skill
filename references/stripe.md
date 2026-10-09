# Stripe: what the existing key can do, and the pattern that needs nothing more

Key: `STRIPE_SECRET_KEY` in
`~/pay-proxy/.env` on 7a72, an **rk_live restricted key** with only Checkout Sessions
read+write. Never print it; pass it via env or a Modal secret.

## What works with that key (verified 2026-10-08)
- `POST /v1/checkout/sessions` with **inline `price_data`**: any product name, any price,
  no Product/Price objects needed. So a new product needs no dashboard work.
- `GET /v1/checkout/sessions/{id}` and the list endpoint: retrieve status, metadata,
  customer_details. This is how sales get confirmed without a webhook.
- `POST /v1/checkout/sessions/{id}/expire`: kill a test session so it can never be paid.

## What it can NOT do (403 more_permissions_required)
- Account, Balance, Charges/Refunds, Prices, Products, Payment Links, Subscriptions.
  If a product needs one of these, tell Ath exactly which permission, for example
  "Charges and Refunds: Write", so he can grant it. He offered (2026-10-08) to issue keys.
  Typical asks:
  - refunds from code → *Charges and Refunds: Write*
  - subscriptions → *Subscriptions: Read* (gating) + *Prices: Write*, or a webhook secret
  - permanent shareable buy links → *Payment Links: Write* + *Prices: Write*

## The claim-on-redirect pattern (web.py implements it)
1. Browser holds a random access key (no accounts, no passwords).
2. `/api/checkout` creates a session with `client_reference_id=<key>`,
   `metadata[product]=<slug>`, `metadata[pack]=<pack>`,
   `success_url=<base>/?paid={CHECKOUT_SESSION_ID}`.
3. Stripe redirects back; the page calls `/api/claim?session_id=…`; the server GETs the
   session, requires `payment_status == "paid"` **and** `metadata.product == slug`
   (one account serves many products), and credits once, recorded in the claims Dict.
4. The same call is key recovery: the receipt's session id restores the owning key.

Why prepaid packs rather than a subscription: no webhook, no subscription read
permission, no dunning, and a $5 first purchase is a much smaller ask of a stranger.
A subscription to a trial product risks billing customers for a service that
later goes offline.

## Pricing
Measure the cost of one unit on Modal (GPU seconds × rate + cold-start idle;
L4 ≈ $0.80/h, scaledown 300 s means each cold wake costs ~$0.07 of idle). Keep the
cheapest pack ≥ 5× its unit cost, and make the first pack $5 or less.

## Testing without charging anyone
Never pay a live session to test. Create one, check it renders (URL starts
`https://checkout.stripe.com/`), check that claiming it unpaid returns 402, then expire it.
`scripts/verify.py` does exactly this.
