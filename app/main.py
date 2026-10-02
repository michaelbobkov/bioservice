import asyncio
import os
import secrets
import string
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import AnyHttpUrl, BaseModel

from . import cache, config, db, metrics

ALPHABET = string.ascii_letters + string.digits
_leak: list[bytes] = []


def make_code(n: int = 7) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    cache.init()
    yield
    await cache.close()
    await db.close()


app = FastAPI(title="URL shortener", lifespan=lifespan)


@app.middleware("http")
async def track(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = route.path if route else "unmatched"
        metrics.REQUESTS.labels(request.method, path, str(status)).inc()
        metrics.LATENCY.labels(request.method, path).observe(time.perf_counter() - start)


class LinkIn(BaseModel):
    url: AnyHttpUrl


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.post("/api/links", status_code=201)
async def create_link(body: LinkIn):
    url = str(body.url)
    for _ in range(5):
        code = make_code()
        row = await db.pool.fetchrow(
            "INSERT INTO links (code, url) VALUES ($1, $2) ON CONFLICT DO NOTHING RETURNING code",
            code, url,
        )
        if row:
            return {"code": code, "short_url": f"{config.BASE_URL}/{code}"}
    raise HTTPException(500, "could not allocate code")


@app.get("/api/links/{code}/stats")
async def stats(code: str):
    row = await db.pool.fetchrow("SELECT code, url, clicks, created_at FROM links WHERE code=$1", code)
    if not row:
        raise HTTPException(404, "not found")
    return dict(row)


@app.get("/health/live")
async def live():
    return {"status": "ok"}


@app.get("/health")
async def ready():
    try:
        await db.pool.fetchval("SELECT 1")
    except Exception:
        raise HTTPException(503, "database unavailable")
    return {"status": "ready"}


@app.get("/metrics")
async def prom():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if config.ENABLE_CHAOS:

    @app.get("/crash")
    async def crash():
        os._exit(1)

    @app.get("/slow")
    async def slow(ms: int = 2000):
        await asyncio.sleep(ms / 1000)
        return {"slept_ms": ms}

    @app.get("/error")
    async def error():
        raise HTTPException(500, "chaos error")

    @app.get("/leak")
    async def leak(mb: int = 10):
        _leak.append(b"x" * mb * 1024 * 1024)
        return {"leaked_mb": sum(len(b) for b in _leak) // (1024 * 1024)}


@app.get("/{code}")
async def redirect(code: str):
    url = await cache.get(code)
    if url:
        metrics.CACHE_HITS.inc()
    else:
        metrics.CACHE_MISSES.inc()
        url = await db.pool.fetchval("SELECT url FROM links WHERE code=$1", code)
        if not url:
            raise HTTPException(404, "not found")
        await cache.set(code, url)
    await db.pool.execute("UPDATE links SET clicks = clicks + 1 WHERE code=$1", code)
    metrics.REDIRECTS.inc()
    return RedirectResponse(url, status_code=307)
