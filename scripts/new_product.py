#!/usr/bin/env python3
"""Scaffold a sellable product: storefront + metering + Stripe + stats.

  new_product.py <slug> "<Display Name>" [--dir ~/<slug>-market]

Creates the directory from assets/template, fills __SLUG__/__NAME__, writes
stats.py, CLAUDE.md and LAUNCH.md stubs, and creates the Modal secret
<slug>-stripe from ~/pay-proxy/.env (STRIPE_SECRET_KEY) if it doesn't exist.
Deploy afterwards with:  ~/.venv-modal/bin/modal deploy web.py
"""
import argparse
import html
import os
import re
import shutil
import subprocess
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
MODAL = os.path.expanduser("~/.venv-modal/bin/modal")
ENV = Path("~/pay-proxy/.env").expanduser()

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("name")
ap.add_argument("--dir")
ap.add_argument("--offline", action="store_true", help="Scaffold locally without inspecting credentials or creating Modal secrets")
a = ap.parse_args()
if not re.fullmatch(r"[a-z][a-z0-9-]{1,30}", a.slug):
    raise SystemExit("slug: lowercase letters, digits, dashes (it becomes Modal app/dict names)")
dest = Path(a.dir or f"~/{a.slug}-market").expanduser()
if dest.exists():
    raise SystemExit(f"{dest} already exists; not overwriting")

shutil.copytree(SKILL / "assets" / "template", dest)
for p in dest.rglob("*"):
    if p.is_file() and p.suffix in (".py", ".html", ".md"):
        p.write_text(p.read_text().replace("__SLUG__", a.slug).replace("__NAME__", html.escape(a.name) if p.suffix == ".html" else a.name))

stats = (SKILL / "scripts" / "stats.py").read_text().replace('SLUG = None', f'SLUG = "{a.slug}"')
(dest / "stats.py").write_text(stats)
(dest / "stats.py").chmod(0o755)

(dest / "CLAUDE.md").write_text(f"""# {a.name}

Live: (fill in after `modal deploy web.py`), hosted on Modal (workspace medott29). Nothing is served from the house.
Scaffolded by the go-to-market skill. Product logic: product.py. Storefront: web.py (rarely edit).
Stripe secret: Modal secret `{a.slug}-stripe` (restricted key, Checkout Sessions read+write).
State: Modal Dicts `{a.slug}-accounts`, `-claims`, `-ipday`, `-events`. Stats: ./stats.py → STATS.md.

## Measured (every number on the page must appear here with how it was measured)
- (none yet)

## Promises the page makes (keep them true in code)
- (privacy / refunds / what is stored)
""")
(dest / "LAUNCH.md").write_text(f"""# {a.name}: launch kit (NOT posted; posting needs Ath's go-ahead)

Demo video: (path, length < 45 s for X, sha256 prefix, Replay Tube link)
Link: (url)

## X (@tinycrops)
(hook line that states the claim; the demo; the link; "free to try, no signup")

## Communities (read each sub's self-promo rules first)
""")
(dest / "DESIGN.md").write_text("# Design brief\n\nAudience and buying moment:\nPrimary task:\nEvidence and limits:\nArt direction (typography, palette, composition):\nPhone behavior:\nLoading, failure and success states:\n\nRead the go-to-market references/website-design.md before editing the page.\n")
(dest / ".gitignore").write_text("__pycache__/\nSTATS.md\nsmoke/\ndemo/frames/\n")
subprocess.run(["git", "init", "-q"], cwd=dest)

if not a.offline:
    # Modal secret: copy the existing restricted key without ever printing it.
    have = subprocess.run([MODAL, "secret", "list", "--json"], capture_output=True, text=True).stdout
    if f'"{a.slug}-stripe"' not in have:
        key = next((l.split("=", 1)[1].strip() for l in ENV.read_text().splitlines()
                    if l.startswith("STRIPE_SECRET_KEY=")), "")
        if not key:
            print(f"!! no STRIPE_SECRET_KEY in {ENV}; create the secret by hand:"
                  f" modal secret create {a.slug}-stripe STRIPE_SECRET_KEY=...")
        else:
            subprocess.run([MODAL, "secret", "create", f"{a.slug}-stripe", f"STRIPE_SECRET_KEY={key}"],
                           check=True, capture_output=True)
            print(f"created Modal secret {a.slug}-stripe")
print(f"scaffolded {dest}\nnext: edit product.py + static/index.html TOOL block, then"
      f"\n  cd {dest} && {MODAL} deploy web.py")
