# go-to-market

A Claude Code skill that takes a product, model, tool or prototype from "works on my machine" to
"a stranger can pay for it" in one session:

- a public page hosted on [Modal](https://modal.com), never on a home network
- a free trial and prepaid credit packs through Stripe Checkout
- a checkout that is verified without charging anyone
- a live stats file, a draft demo video, a readiness verdict and a launch kit

Nothing gets posted or sent to anyone without the operator's go-ahead.

Website: https://medott29--go-to-market-site.modal.run

## Install

```sh
git clone https://github.com/tinycrops/go-to-market-skill ~/.claude/skills/go-to-market
```

Claude Code picks the skill up from `SKILL.md`. Ask it to "put X up for sale" or "can we charge for X?".

## What you need

- A Modal account and the `modal` CLI. The scripts expect it at `~/.venv-modal/bin/modal`.
- A Stripe **restricted** key with only *Checkout Sessions: read + write*, in `~/pay-proxy/.env` as
  `STRIPE_SECRET_KEY=...`. That is enough for inline-priced checkout, claiming paid sessions and
  expiring test sessions. See `references/stripe.md`.
- Python 3.10+ with `requests`.

Paths and machine names in `SKILL.md` (7a72, `~/agent-dashboard`) come from the author's setup.
Change them to match yours.

## Layout

| Path | What it is |
| --- | --- |
| `SKILL.md` | The procedure Claude follows, steps 0–8 |
| `references/` | Modal traps, the Stripe pattern, the website design and acceptance procedure |
| `scripts/new_product.py` | Scaffolds `~/<slug>-market/` and creates the Modal secret |
| `scripts/verify.py` | Proves a deployed storefront can take money, then expires the test session |
| `scripts/stripe_audit.py` | Summarises every Checkout Session the account has seen |
| `scripts/stats.py`, `install_timer.sh` | Visitors, runs, checkouts and sales into `STATS.md` every 30 min |
| `assets/template/` | The storefront: FastAPI on Modal, credit metering, Stripe claim-on-redirect |
| `site/` | The skill's own website, deployed with `modal deploy site/app.py` |
