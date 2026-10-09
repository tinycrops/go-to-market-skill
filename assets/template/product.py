"""The only file a new product has to fill in. web.py imports it.

Contract:
  NAME, UNIT, FREE_CREDITS, PACKS, PIP          constants
  async estimate_cost(form) -> int              credits this request will use;
                                                raise HTTPException(400, msg) on bad input
  async run(form) -> (bytes, media_type)        do the work; raise on failure
                                                (web.py refunds automatically)
  async warm()                                  optional: start a cold GPU early
  SECRETS = ["<slug>-openai", ...]              optional: extra Modal secrets for the web app
  MODULES = ["report", ...]                     optional: extra local .py modules to ship
  PUBLIC_CONFIG                                 optional dict merged into /api/config

`form` is a starlette FormData: form.get("field") for text, an UploadFile for
files (await f.read()). Heavy work belongs in a separate Modal app (GPU), called
like:  modal.Cls.from_name("<slug>-engine", "Engine")().method.remote.aio(...)

The stub below is a working placeholder (1 credit per run, echoes text back) so
the storefront can be deployed and verified before the real product exists.
"""
import json

NAME = "__NAME__"
UNIT = "credits"            # what the customer is buying: "minutes", "images", "reports"...
FREE_CREDITS = 3            # enough to feel the product, not enough to live on it
PIP = []                    # extra pip packages the web container needs

# Price from unit cost: measure what one credit costs you on Modal, then keep
# the cheapest pack at >= 5x that. Small first pack = low-friction first sale.
PACKS = {
    "starter": {"label": "20 credits", "cents": 500, "credits": 20},
    "studio": {"label": "100 credits", "cents": 1500, "credits": 100},
    "pro": {"label": "400 credits", "cents": 3900, "credits": 400},
}


async def estimate_cost(form) -> int:
    from fastapi import HTTPException
    text = str(form.get("text", "")).strip()
    if not text:
        raise HTTPException(400, "type something first")
    return 1


async def run(form):
    text = str(form.get("text", ""))
    return json.dumps({"result": text[::-1]}).encode(), "application/json"
