import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shortener:shortener@localhost:5432/shortener")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
ENABLE_CHAOS = os.getenv("ENABLE_CHAOS", "false").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
