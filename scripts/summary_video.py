#!/usr/bin/env python3
"""Cut the summary video that sits at the top of every product page.

  summary_video.py <product-dir> --url <live url> --claim "<one sentence>"
      [--scene "label|command|logfile" ...] [--steps steps.py] [--end "<closing line>"]

Everything in the video is real: terminal scenes replay output you captured with
  script -q -c "<command>" <logfile>
and the browser scene drives the live page. Write <product-dir>/static/summary.mp4
(H.264, no audio, at most 45 s) and summary.jpg (poster), then redeploy.

--steps names a Python file with `async def steps(page, cap)`: drive the page
with Playwright and call `await cap("text")` to caption what is on screen.
Without it the default scrolls to #try and #pricing. Captions describe what the
viewer sees; never caption a number the run didn't produce.

Needs Python Playwright, /usr/bin/google-chrome, ffmpeg, and Playwright's own
ffmpeg for page recording (`python -m playwright install ffmpeg`, once).
"""
import argparse
import asyncio
import html
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

FPS, W, H, MAX_S = 30, 1280, 720, 45

ap = argparse.ArgumentParser()
ap.add_argument("product_dir")
ap.add_argument("--url", required=True)
ap.add_argument("--claim", required=True, help="one sentence under the title card")
ap.add_argument("--title", help="defaults to NAME in product.py")
ap.add_argument("--scene", action="append", default=[], help='"label|command|logfile", in order')
ap.add_argument("--steps", help="python file defining async steps(page, cap)")
ap.add_argument("--end", default="", help="closing card text, e.g. the link")
ap.add_argument("--chrome", default="/usr/bin/google-chrome")
a = ap.parse_args()

prod = Path(a.product_dir).expanduser().resolve()
title = a.title or (re.search(r'^NAME\s*=\s*"(.*)"', (prod / "product.py").read_text(), re.M) or [None, prod.name])[1]
ANSI = re.compile(r"\x1b\[[?0-9;]*[A-Za-z]|\r")


def log_text(p):
    lines = [l for l in ANSI.sub("", Path(p).expanduser().read_text()).splitlines() if not l.startswith("Script ")]
    return "\n".join(lines).strip()


scenes = []
for s in a.scene:
    label, cmd, logf = s.split("|", 2)
    scenes.append({"label": label, "cmd": cmd, "out": log_text(logf)})

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>html,body{margin:0;background:#000;color:#d9d9d9;width:%(W)dpx;height:%(H)dpx;overflow:hidden}
.wrap{position:absolute;inset:0;padding:56px 72px;display:grid;grid-template-rows:auto 1fr;gap:26px}
.eye{font:600 15px/1 "JetBrains Mono",monospace;letter-spacing:.16em;text-transform:uppercase;color:#8b90a0}
.term{position:relative;border:1px solid #2a2f3d;background:#07080b;padding:26px 30px;font:19px/1.6 "JetBrains Mono",monospace;white-space:pre;overflow:hidden}
.term::after{content:"";position:absolute;top:10px;right:10px;width:9px;height:9px;background:#5affaa;box-shadow:0 0 10px #5affaa}
.p{color:#8b90a0}.ok{color:#5affaa}.bad{color:#f03088}.y{color:#ffe14d}.l{color:#7f9cff}
.card{position:absolute;inset:0;display:grid;place-content:center;gap:22px;padding:0 120px}
h1{font:700 76px/1 "Chakra Petch",sans-serif;margin:0}.card p{font:22px/1.5 "JetBrains Mono",monospace;color:#8b90a0;margin:0;max-width:1000px}
.caret{display:inline-block;width:11px;height:22px;background:#64f0f8;vertical-align:-4px}</style></head>
<body><div id="root"></div><script>
const D=%(data)s, esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
const fmt=s=>s.replace(/^PASS/gm,'<span class="ok">PASS</span>').replace(/^FAIL/gm,'<span class="bad">FAIL</span>')
  .replace(/ALL PASS/,'<span class="y">ALL PASS</span>').replace(/(https:\\/\\/[^\\s<]+)/g,'<span class="l">$1</span>');
const card=(e,h,p)=>`<div class="card"><div class="eye">${e}</div><h1>${h}</h1><p>${p}</p></div>`;
window.render=(kind,i,t)=>{let h='';
  if(kind==='title')h=card('go-to-market',esc(D.title),esc(D.claim));
  else if(kind==='end')h=card('',esc(D.title),esc(D.end));
  else{const s=D.scenes[i],cps=Math.max(38,s.cmd.length/2.2),n=Math.floor(t*cps),done=n>=s.cmd.length;
    let b=`<span class="p">$ </span>${esc(s.cmd.slice(0,n))}`+(done?'':'<span class="caret"></span>');
    const tl=t-s.cmd.length/cps-.35,ls=s.out.split('\\n'),per=Math.min(.4,4.5/Math.max(1,ls.length));
    if(done&&tl>0)b+='\\n'+fmt(esc(ls.slice(0,Math.floor(tl/per)+1).join('\\n')));
    h=`<div class="wrap"><div class="eye">${esc(s.label)}</div><div class="term">${b}</div></div>`;}
  document.getElementById('root').innerHTML=h;};
</script></body></html>"""


def scene_len(s):
    cps = max(38, len(s["cmd"]) / 2.2)
    n = len(s["out"].splitlines())
    return len(s["cmd"]) / cps + .35 + min(.4, 4.5 / max(1, n)) * n + 1.8


async def default_steps(page, cap):
    await cap("the live page")
    await page.wait_for_timeout(2500)
    for sel, text in (("#try", "try it free"), ("#pricing", "prepaid packs through Stripe Checkout")):
        if await page.query_selector(sel):
            await cap(text)
            await page.evaluate(f"document.querySelector('{sel}').scrollIntoView({{behavior:'smooth',block:'center'}})")
            await page.wait_for_timeout(3000)


async def main(tmp):
    from playwright.async_api import async_playwright
    steps = default_steps
    if a.steps:
        spec = importlib.util.spec_from_file_location("steps", a.steps)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); steps = mod.steps
    page_html = tmp / "scene.html"
    page_html.write_text(PAGE % {"W": W, "H": H, "data": json.dumps(
        {"title": title, "claim": a.claim, "end": a.end or a.url, "scenes": scenes})})
    parts = []

    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=a.chrome)

        async def cards(name, kind, i, dur):
            d = tmp / name; d.mkdir()
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.goto(page_html.as_uri()); await pg.wait_for_timeout(1200)
            for f in range(int(dur * FPS)):
                await pg.evaluate("([k,i,t])=>render(k,i,t)", [kind, i, f / FPS])
                await pg.screenshot(path=str(d / f"{f:05d}.png"))
            await pg.close()
            out = tmp / f"{name}.mp4"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(d / "%05d.png"),
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out)], check=True)
            parts.append(out)

        await cards("a_title", "title", 0, 3.2)
        for i, s in enumerate(scenes):
            await cards(f"b_scene{i}", "scene", i, scene_len(s))

        ctx = await b.new_context(viewport={"width": W, "height": H}, record_video_dir=str(tmp / "vid"),
                                  record_video_size={"width": W, "height": H})
        pg = await ctx.new_page()
        await pg.goto(a.url, wait_until="networkidle"); await pg.wait_for_timeout(800)

        async def cap(text):
            await pg.evaluate("t=>{let c=document.getElementById('__cap');if(!c){c=document.createElement('div');c.id='__cap';"
                              "c.style.cssText='position:fixed;left:24px;bottom:24px;z-index:2147483647;font:600 15px/1.3 monospace;"
                              "letter-spacing:.12em;text-transform:uppercase;background:#000;color:#64f0f8;border:1px solid #64f0f8;"
                              "padding:10px 14px';document.body.appendChild(c)}c.textContent=t}", text)
        await steps(pg, cap)
        v = pg.video; await ctx.close()
        live = tmp / "c_live.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "0.8", "-i", await v.path(), "-vf",
                        f"fps={FPS},scale={W}:{H}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(live)], check=True)
        parts.append(live)
        await cards("d_end", "end", 0, 3.5)
        await b.close()

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{x}'\n" for x in parts))
    mp4, jpg = prod / "static" / "summary.mp4", prod / "static" / "summary.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "slow", "-movflags", "+faststart", "-an", str(mp4)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(min(dur - .5, 3.2 + .5 * sum(map(scene_len, scenes)))),
                    "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(jpg)], check=True)
    print(f"{mp4}  {dur:.1f} s  {mp4.stat().st_size / 1e6:.1f} MB\n{jpg}")
    if dur > MAX_S:
        raise SystemExit(f"!! {dur:.1f} s is over {MAX_S} s: shorten the steps or drop a scene")
    print("next: redeploy, then check the page shows it (verify.py reports 'summary video at top')")


tmp = Path(tempfile.mkdtemp(prefix="summary-video-"))
try:
    asyncio.run(main(tmp))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
