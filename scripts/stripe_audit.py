#!/usr/bin/env python3
"""What has Stripe actually seen? Run this before deciding what to build.

  stripe_audit.py [--limit 300] [--show-names]

Summarises Checkout Sessions on the account behind ~/pay-proxy/.env: per
product (metadata.product, or amount for older links), how many were opened,
how many paid, and when. Paid sessions are the only hard evidence of
willingness to pay; agents that skip this step miss real sales. Names/emails stay masked unless
--show-names; never contact a customer from this output, give Ath the facts.
"""
import argparse
import collections
import datetime
import re
from pathlib import Path

import requests

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=300)
ap.add_argument("--show-names", action="store_true")
a = ap.parse_args()
sk = re.search(r"^STRIPE_SECRET_KEY=(\S+)", Path("~/pay-proxy/.env").expanduser().read_text(), re.M).group(1)

rows, after = [], None
while len(rows) < a.limit:
    p = {"limit": 100, **({"starting_after": after} if after else {})}
    d = requests.get("https://api.stripe.com/v1/checkout/sessions", params=p, auth=(sk, ""), timeout=30).json()
    if "error" in d:
        raise SystemExit(d["error"]["message"])
    rows += d["data"]
    if not d["has_more"]:
        break
    after = d["data"][-1]["id"]

g = collections.defaultdict(lambda: {"opened": 0, "paid": 0, "first": None, "last": None})
paid = []
for s in rows:
    label = (s.get("metadata") or {}).get("product") or \
        f"{s['mode']} ${(s['amount_total'] or 0)/100:.2f}" + (" (payment link)" if s.get("payment_link") else "")
    day = datetime.date.fromtimestamp(s["created"]).isoformat()
    x = g[label]
    x["opened"] += 1
    x["first"] = min(filter(None, [x["first"], day]))
    x["last"] = max(filter(None, [x["last"], day]))
    if s["payment_status"] == "paid":
        x["paid"] += 1
        cd = s.get("customer_details") or {}
        who = cd.get("name") or "?"
        if not a.show_names:
            who = who[:1] + "***"
        paid.append((day, label, s["amount_total"], who, s.get("subscription") and "subscription" or ""))

print(f"{len(rows)} checkout sessions scanned\n")
print(f"{'product':38} {'opened':>6} {'paid':>5}  first → last")
for k, v in sorted(g.items(), key=lambda kv: -kv[1]["paid"]):
    print(f"{k[:38]:38} {v['opened']:>6} {v['paid']:>5}  {v['first']} → {v['last']}")
print("\nPAID:" if paid else "\nno paid sessions")
for p in paid:
    print(f"  {p[0]}  {p[1]}  ${p[2]/100:.2f}  {p[3]} {p[4]}")
