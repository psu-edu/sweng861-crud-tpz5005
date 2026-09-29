from prometheus_client import Counter, Histogram, make_asgi_app

# 1. Metric Definitions
# Request Latency
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "route"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]  # Latency buckets in seconds
)

# Request Counter
REQUEST_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests handled by method, route, and status code",
    ["method", "route", "status"]
)

# Domain Metric
ITEMS_CREATED_TOTAL = Counter(
    "osrs_items_created_total",
    "Total number of OSRS items created",
    ["created_by"]
)

# 2. Prometheus ASGI App Exporter
# This ASGI app will be mounted on /metrics in main.py
metrics_app = make_asgi_app()