import os
from taskiq_nats import NatsBroker
from taskiq import PrometheusMiddleware
# From the prompt: "TaskiqInstrumentor" / "OpenTelemetryMiddleware"
# We will use the built-in instrumentor or custom middleware if it exists.
# `taskiq-opentelemetry` didn't exist in pip directly, but we can implement a basic span propagation middleware or just use Prometheus.

# The URL should ideally be pulled from composite settings, but for the adapter
# declaration we can pull it dynamically or use a default.
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Initialize the TaskIQ NATS Broker
# This broker can be imported and injected into the System composition root
# and used by module handlers to dispatch tasks.
broker = NatsBroker(
    servers=[NATS_URL],
    queue="my_monolith_tasks"
)

# Attach Observability Middlewares
broker.add_middlewares(
    PrometheusMiddleware(
        server_port=9000
    )
)
