# Modal hosting: why it's the default, and the traps already paid for

**Why Modal:** since 2026-09-30 nothing on the home network serves the internet (Ath:
public serving lagged his games). Modal gives a public HTTPS URL
(`https://medott29--<app>-<fn>.modal.run`), GPUs on demand, and costs nothing while idle.
CLI: `~/.venv-modal/bin/modal` (v1.5.5, profile `medott29`) on 7a72.

## Shape
- `<slug>-web` (web.py): CPU FastAPI under `@modal.asgi_app()`, holds the Stripe secret,
  serves the page, meters credits. HTTPS, so mic/camera (`getUserMedia`) work in the browser.
- `<slug>-engine` (optional, separate file): `@app.cls(gpu="L4", scaledown_window=300,
  max_containers=4)` with `@modal.enter()` loading the model. product.py calls it:
  `await modal.Cls.from_name("<slug>-engine","Engine")().fn.remote.aio(...)`.
  Separate apps mean the storefront redeploys in about 40 s without rebuilding a GPU image.
- State: `modal.Dict.from_name(..., create_if_missing=True)`. That's fine for keys and credits
  at launch scale; read-modify-write isn't atomic, so don't build high-contention logic on it.

## Traps hit on 2026-10-08 (each cost a rebuild)
1. `modal.Image.debian_slim()` on this workspace builds **bullseye** and apt 404s on
   debian-security. Use `modal.Image.from_registry("python:3.11-slim-bookworm")` and
   `run_commands("apt-get update && apt-get install -y …")`.
2. Old ML deps pin **protobuf <3.20** (descript-audiotools), which breaks the Modal client
   inside the container (`VolumeFsVersion has no ValueType`). Add a later
   `.run_commands("pip install 'protobuf>=4.25,<6'")` step after the deps.
3. Moving a CPU-snapshotted model onto the GPU by hand is fragile. Load straight onto
   the GPU in `@modal.enter()` and accept the cold start, or use Modal's GPU snapshot only
   if the library supports it cleanly.
4. **Cold start ≈ 60–70 s** for a GPU model. Hide it: the page calls `/api/warm` on the
   visitor's first interaction (typing, record button, file picked), and `product.warm()`
   does `engine.warm.spawn.aio()`. Keeping `min_containers=1` costs ≈ $19/day on an L4,
   which isn't worth it before there are sales.
5. A per-IP free-trial cap of 3 starved real phones (CGNAT). It's 20 now.
6. Bake model weights into the image with `.run_function(prefetch)` so a cold start
   downloads nothing.

## Useful commands
- deploy: `modal deploy web.py` (prints the URL)
- logs: `modal app logs <slug>-web`
- take it down: `modal app stop --yes <slug>-web` (`--yes` is required in a non-interactive shell) (the URL then 404s; Dicts and secret remain)
- secrets: `modal secret list`; never echo values
