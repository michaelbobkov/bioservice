"""Требует запущенные Postgres и Redis (DATABASE_URL / REDIS_URL)."""
import httpx
import pytest_asyncio
from asgi_lifespan import LifespanManager  # noqa: F401  (см. requirements)

from app.main import app


@pytest_asyncio.fixture
async def client():
    async with LifespanManager(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            yield c


async def test_full_flow(client):
    r = await client.post("/api/links", json={"url": "https://example.com"})
    assert r.status_code == 201
    code = r.json()["code"]

    r = await client.get(f"/{code}", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"].startswith("https://example.com")

    s = (await client.get(f"/api/links/{code}/stats")).json()
    assert s["clicks"] == 1


async def test_404_and_health(client):
    assert (await client.get("/nope123")).status_code == 404
    assert (await client.get("/health")).status_code == 200
    assert b"http_requests_total" in (await client.get("/metrics")).content
