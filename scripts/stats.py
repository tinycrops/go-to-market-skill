#!/home/ath/.venv-modal/bin/python
"""Visitors, runs, checkouts, sales and feedback for one product.

  stats.py [slug]        (the scaffolded copy has its slug baked in)

Reads the Modal Dict <slug>-events written by web.py and writes STATS.md next
to this file. Sales here are claims of paid sessions; scripts/stripe_audit.py
is the cross-check against Stripe itself.
"""
import collections
import datetime
import pathlib
import sys

import modal

SLUG = None
slug = sys.argv[1] if len(sys.argv) > 1 else SLUG
if not slug:
    raise SystemExit("usage: stats.py <slug>")
rows = sorted((v for _, v in modal.Dict.from_name(f"{slug}-events").items()), key=lambda r: r["t"])
c = collections.Counter(r["kind"] for r in rows)
cents = sum(r.get("cents") or 0 for r in rows if r["kind"] == "paid")
day = lambda r: datetime.datetime.fromtimestamp(r["t"]).strftime("%Y-%m-%d")
per = collections.defaultdict(collections.Counter)
for r in rows:
    per[day(r)][r["kind"]] += 1
runs = c["run"] + c["convert"]
out = [f"# {slug} stats ({datetime.datetime.now():%Y-%m-%d %H:%M})", "",
       f"- new visitors (access keys): {c['key']}", f"- runs: {runs}",
       f"- checkouts opened: {c['checkout']}", f"- **sales: {c['paid']} = ${cents/100:.2f}**",
       f"- errors: {sum(v for k, v in c.items() if k.endswith('error'))}",
       f"- feedback messages: {c['feedback']}", "",
       "| day | visitors | runs | checkouts | sales |", "|---|---|---|---|---|"]
out += [f"| {d} | {k['key']} | {k['run'] + k['convert']} | {k['checkout']} | {k['paid']} |"
        for d, k in sorted(per.items())]
fb = [r for r in rows if r["kind"] == "feedback"]
if fb:
    out += ["", "## Feedback"] + [f"- {day(r)}: {r['message']!r} (contact: {r.get('contact') or '-'})" for r in fb]
errs = [r for r in rows if r["kind"].endswith("error")][-5:]
if errs:
    out += ["", "## Last errors"] + [f"- {day(r)} {r['kind']}: {r.get('msg') or r.get('err')}" for r in errs]
text = "\n".join(out) + "\n"
(pathlib.Path(__file__).resolve().parent / "STATS.md").write_text(text)
print(text)
