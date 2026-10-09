#!/usr/bin/env python3
"""Prove a deployed storefront can take money while preserving analytics.

  verify.py <url> <slug> [--field name=value ...] [--file name=path ...] [--keep-events]

Checks, in order: page + terms load; a key is issued with free credits; one
real /api/run with the given form succeeds and debits; balance agrees;
/api/checkout returns a live Stripe URL (that session is EXPIRED immediately so
it can never be paid); claiming it is refused as unpaid; a bogus session is
refused. Events and IP counters are preserved by default. Only use
--reset-test-events on a disposable test deployment: it clears entire dicts.

Uses the restricted key from ~/pay-proxy/.env only to expire the test session.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import requests

ap = argparse.ArgumentParser()
ap.add_argument("url")
ap.add_argument("slug")
ap.add_argument("--field", action="append", default=[])
ap.add_argument("--file", action="append", default=[])
ap.add_argument("--keep-events", action="store_true", help="Compatibility flag; preservation is now the default")
ap.add_argument("--reset-test-events", action="store_true", help="Clear all events/IP counters on a disposable test deployment only")
a = ap.parse_args()
U = a.url.rstrip("/")
ok = True


def check(name, cond, detail=""):
    global ok
    ok &= bool(cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")


r = requests.get(U + "/", timeout=60)
check("page loads", r.status_code == 200 and "<html" in r.text.lower(), f"{r.status_code} {len(r.text)}B")
# standard since 2026-10-09: the page opens with a summary video (reported, not counted: it is cut after this passes)
m = re.search(r'<video[^>]+src="/static/summary\.mp4"', r.text)
sec = r.text.find("<section")
rv = requests.get(U + "/static/summary.mp4", timeout=30, stream=True); vid = rv.status_code == 200; rv.close()
print(f"{'PASS' if m and vid and (sec < 0 or m.start() < sec) else 'TODO'}  summary video at top  "
      f"{'served' if vid else 'not served yet: run scripts/summary_video.py, then redeploy'}")
leftover = re.findall(r"__[A-Z0-9_]+(?::[^_]*)?__", r.text)
check("no unfilled __PLACEHOLDERS__ on page", not leftover, ", ".join(sorted(set(leftover))[:6]))
r = requests.get(U + "/terms", timeout=30)
check("terms load", r.status_code == 200)
check("no unfilled placeholders in terms", not re.findall(r"__[A-Z0-9_]+", r.text))

j = requests.post(U + "/api/key", timeout=30).json()
key, free = j["key"], j["credits"]
check("key issued with free credits", free > 0, f"free={free}")

data = dict(f.split("=", 1) for f in a.field)
files = {k: open(os.path.expanduser(p), "rb") for k, p in (f.split("=", 1) for f in a.file)}
r = requests.post(U + "/api/run", data={"key": key, **data}, files=files or None, timeout=600)
charged = int(r.headers.get("X-Charged", 0))
check("one real run succeeds", r.status_code == 200, f"{r.status_code} charged={charged} "
      f"{r.headers.get('content-type')} {len(r.content)}B {r.elapsed.total_seconds():.1f}s")
if r.status_code != 200:
    print("   ", r.text[:300])
bal = requests.get(U + "/api/balance", params={"key": key}, timeout=30).json()["credits"]
check("balance debited by exactly the charge", bal == free - charged, f"{free} - {charged} = {bal}")

r = requests.post(U + "/api/checkout", json={"key": key, "pack": "starter"}, timeout=30)
url = r.json().get("url", "")
sid = (re.search(r"cs_(live|test)_[A-Za-z0-9]+", url) or [None])[0]
check("checkout returns a Stripe URL", url.startswith("https://checkout.stripe.com/") and sid,
      url[:45])
if sid:
    env = Path("~/pay-proxy/.env").expanduser().read_text()
    sk = re.search(r"^STRIPE_SECRET_KEY=(\S+)", env, re.M).group(1)
    e = requests.post(f"https://api.stripe.com/v1/checkout/sessions/{sid}/expire", auth=(sk, ""), timeout=30)
    check("test session expired (can never be paid)", e.json().get("status") == "expired")
    r = requests.get(U + "/api/claim", params={"session_id": sid}, timeout=30)
    check("unpaid session refused", r.status_code == 402, r.text[:80])
r = requests.get(U + "/api/claim", params={"session_id": "cs_live_bogus"}, timeout=30)
check("bogus session refused", r.status_code == 404, r.text[:80])

if a.reset_test_events and not a.keep_events:
    py = os.path.expanduser("~/.venv-modal/bin/python")
    subprocess.run([py, "-c", "import modal,sys\nfor n in sys.argv[1:]: modal.Dict.from_name(n).clear()",
                    f"{a.slug}-events", f"{a.slug}-ipday"], check=True)
    print("cleared test events + ip counters: STATS.md now counts only real visitors")
print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
