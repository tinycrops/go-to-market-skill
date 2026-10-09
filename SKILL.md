---
name: go-to-market
description: Take any product, model, tool or prototype from "works on 7a72" to "a stranger can pay for it" in one session. That means a public page hosted on Modal (never the home network), a free trial, prepaid credit packs through Stripe Checkout using the existing key, verified checkout, a summary video at the top of the page, a live stats file, an honest readiness verdict and a ready-to-post launch kit. Use this whenever Ath wants to sell, monetize, charge for, launch, ship to customers, "get paying customers", "make money from", trial a product on the market, or asks whether something could be sold. Use it even if he only names the product ("put X up for sale", "can we charge for the booth?"), and before building any new payment, checkout or paywall code by hand.
---

# Go to market

Ath trials many products. The expensive part isn't building the product. It's the
surrounding work that makes it purchasable: hosting it somewhere he's allowed to,
taking money safely, proving the checkout works without charging anyone, counting
visitors and sales, and handing him something he can post. This skill turns that into
about an hour of mostly mechanical steps, so each trial costs little and the only
open question left is "is this product good enough to sell?". That question is Ath's
to answer, and the skill's job is to give him the evidence for it.

The first run (Impressions, 2026-10-08, `~/impressions-web`) is the worked example.
Read its `CLAUDE.md` when you want to see the finished shape.

## Hard boundaries (why they exist)
- **Nothing served from the house.** Home serving lagged his games (2026-09-30). Host on Modal.
- **Nothing outward without his yes.** Don't post, DM, email, list on directories, or
  contact customers, and don't stage drafts in his Gmail either. He said "let's not send any AI generated
  messages" to a real customer. Build everything up to the post, then ask.
- **Every number on the page is measured.** He reads claims closely, and a page that
  overclaims is worse than one that's plain. Record each measurement in the product's CLAUDE.md.
- **No real-person likeness, no stored user data you haven't disclosed.** The page's privacy
  text must describe exactly what the code stores.
- **Never pay a live session to test.** verify.py creates one and expires it.

## Steps

### 0. Orient (5 min)
`hostname` (expect ath-MS-7A72). Read the last 48h of `~/agent-dashboard/handoffs/`.
Run `scripts/stripe_audit.py` to see what has ever been paid on the account. Paid
sessions demonstrate payment, not retention or product-market fit. Research can identify needs but does not prove demand. If one exists for something related, say so.
Before choosing or repositioning the offer, research current customer problems and existing alternatives. Save dated sources, observed needs, the buyer and buying moment, free substitutes, and the untested payment hypothesis in research/NEEDS.md. Reuse an existing product when it addresses the need. Do not infer willingness to pay from complaints or competitor prices.

### 1. Scaffold (2 min)
```bash
~/.claude/skills/go-to-market/scripts/new_product.py <slug> "<Display Name>"
```
For local design exploration without provisioning secrets, add `--offline`.
This creates `~/<slug>-market/` (web.py storefront, product.py stub, static page and
terms, stats.py, CLAUDE.md, LAUNCH.md) and the Modal secret `<slug>-stripe`. The stub
product deploys as-is. Deploying and running `verify.py` immediately is a good habit: it
proves payments work before you touch the product.

### 2. Wire the product
Fill in `product.py`. Its docstring has the contract: `estimate_cost(form)`, `run(form)`,
an optional `warm()`, plus UNIT, FREE_CREDITS and PACKS. For GPU work, put the model in a
separate `engine.py` Modal app and call it from `run`. See `references/modal.md` before
writing the image; it lists the traps that each cost a rebuild last time. Then replace the
`TOOL` block in `static/index.html` with the product's real input and output UI. The page
already has `runProduct(fd)`, `warm()`, the balance bar, pricing, key restore and feedback.

Charge for what the customer perceives (seconds of audio, images, reports), debit
before the work and let web.py refund on failure. Price per `references/stripe.md`:
measure the unit cost, keep the cheapest pack at 5× or more, and make the first pack $5 or less.

### 3. Design around the customer's decision
Read [references/website-design.md](references/website-design.md) before designing.
The scaffold is functional plumbing, not a finished visual identity. Preserve its
payment and product contracts while composing a product-specific page. Write
DESIGN.md with the audience, primary task, visual direction, real proof artifact,
and responsive behavior. Fill every placeholder in index.html and terms.html.
Use an outcome headline, a concise explanation, and a visible real output or
explicitly labeled illustrative example. Keep claims traceable to measurements.
Privacy text must match the actual code and its providers.

### 4. Deploy and verify
```bash
cd ~/<slug>-market && ~/.venv-modal/bin/modal deploy web.py
~/.claude/skills/go-to-market/scripts/verify.py <url> <slug> --field k=v --file k=path
```
All functional checks must pass. Follow the browser acceptance procedure in
references/website-design.md; save screenshots and findings in DESIGN-QA.md.
Use approved browser tooling available in the current environment. Preserve real
visitor and sales counters: verify.py now preserves them by default (the older
--keep-events flag still works). Only use --reset-test-events for a disposable
test deployment.
Mark test activity explicitly instead of clearing production analytics.

### 5. Measure quality and give a readiness verdict
Measure the thing the page promises, on real inputs, and write the numbers into
CLAUDE.md. Then compare honestly against the best alternative a customer would try first
(a named competitor, or "doing it by hand"). Write a short **Readiness verdict** at the top
of LAUNCH.md: what it beats, what it loses on, and who it is good enough for today. Ath
decided not to sell the first product on quality grounds. This verdict exists so he can make
that call in a minute instead of discovering it after posting.

### 6. Summary video at the top of the page (standard)
Every product page opens with a short summary video, and so does the README of anything
published to GitHub. A visitor sees the product working before reading a word.
- Capture real terminal output as you go, from step 1 on: `script -q -c "<command>" <logfile>`
  for the scaffold, the deploy and verify.py.
- Once verify.py passes, cut it:
  ```bash
  ~/.claude/skills/go-to-market/scripts/summary_video.py ~/<slug>-market --url <live url> \
      --claim "<one sentence>" --scene "step 4 · verify|verify.py <url> <slug>|<logfile>" [--steps steps.py]
  ```
  It writes `static/summary.mp4` and `static/summary.jpg`: a title card, the terminal scenes, the live
  page driven by Playwright with captions, and an end card. At most 45 s with no audio, so it autoplays muted.
  `--steps` takes `async def steps(page, cap)`; use it to show the product's real input and output
  (a before/after on the same input when that is the claim).
- The template's hero already holds the `<video>`; it stays hidden until the file exists. Redeploy, then
  rerun verify.py, which reports `summary video at top`.
- Show only what happened: real output, the real page, captions that describe what is on screen.
- On GitHub, put `summary.jpg` at the top of the README, linked to the live page.

### 7. Stats, demo, launch kit
- `scripts/install_timer.sh <slug> ~/<slug>-market` keeps STATS.md fresh every 30 min.
- Optional: a longer cut for X, under 45 s with sound (start from the summary video), that *shows* the claim (for example,
  before/after on the same input), rendered from the live product's real output. Upload it
  with `claude-upload <mp4> "<title>" "<desc>"` (Replay Tube) and note the sha256 prefix.
- LAUNCH.md: the verdict, demo path and link, an X post for @tinycrops, and 1–2 community
  posts with a reminder to check each one's self-promo rules.

### 8. Hand off and record
- `~/agent-dashboard/handoffs/YYYY-MM-DD-claude-<slug>-launch.md`: what's live, what was
  measured, the demo (host, path, sha256, preview link), what's weak, and "Codex: do not post or
  contact anyone".
- Add a short Cluster TOC entry in `~/CLAUDE.md` and a project memory with a MEMORY.md line.
- `git commit` in the product dir.

### 9. Ask, then stop
End with: the live URL (summary video at the top), the verdict in one or two lines, the demo link, and one clear question,
such as "post it on X?". Don't re-ask on every turn after that; wait for his answer.

## When a trial ends
`modal app stop --yes <slug>-web` (and `<slug>-engine`), and disable the timer with
`systemctl --user disable --now <slug>-stats.timer`. Note the outcome (visitors, runs,
checkouts, sales) in the product's CLAUDE.md, so the next product starts from evidence.
