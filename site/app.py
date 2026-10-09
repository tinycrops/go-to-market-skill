"""The go-to-market skill's website. Static, CPU only, costs nothing while idle.

    modal deploy site/app.py
"""
from pathlib import Path

import modal

HERE = Path(__file__).parent
image = (modal.Image.from_registry("python:3.11-slim-bookworm")
         .pip_install("fastapi[standard]==0.115.6")
         .add_local_file(HERE / "index.html", "/site/index.html")
         .add_local_file(HERE / "summary.mp4", "/site/summary.mp4")
         .add_local_file(HERE / "summary.jpg", "/site/summary.jpg"))
app = modal.App("go-to-market", image=image)


@app.function(max_containers=2)
@modal.asgi_app(label="go-to-market-site")
def site():
    from fastapi import FastAPI
    from fastapi.responses import FileResponse, HTMLResponse, Response

    page = Path("/site/index.html").read_text()
    web = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @web.get("/", response_class=HTMLResponse)
    def index():
        return HTMLResponse(page, headers={"Cache-Control": "public, max-age=300"})

    @web.get("/summary.mp4")
    def video():
        return FileResponse("/site/summary.mp4", media_type="video/mp4", headers={"Cache-Control": "public, max-age=3600"})

    @web.get("/summary.jpg")
    def poster():
        return FileResponse("/site/summary.jpg", media_type="image/jpeg", headers={"Cache-Control": "public, max-age=3600"})

    @web.get("/favicon.ico")
    def favicon():
        return Response(status_code=204)

    return web
