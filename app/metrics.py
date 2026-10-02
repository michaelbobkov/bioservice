from prometheus_client import Counter, Histogram

REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["method", "route"])
REDIRECTS = Counter("redirects_total", "Successful redirects")
CACHE_HITS = Counter("cache_hits_total", "Redirect cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Redirect cache misses")
