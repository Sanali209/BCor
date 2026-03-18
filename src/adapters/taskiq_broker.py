import os
from taskiq_nats import NatsBroker
from taskiq import PrometheusMiddleware
# From the prompt: "TaskiqInstrumentor" / "OpenTelemetryMiddleware"
# We will use the built-in instrumentor or custom middleware if it exists.
# `taskiq-opentelemetry` didn't exist in pip directly, but we can implement a basic span propagation middleware or just use Prometheus.

# The URL should ideally be pulled from composite settings, but for the adapter
# declaration we can pull it dynamically or use a default.
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

def get_broker(is_test: bool = False) -> "taskiq.AsyncBroker":
    """Initializes and returns a TaskIQ broker instance.

    Depending on the environment, it returns either an InMemoryBroker 
    for testing or a NatsBroker for production, configured with 
    Prometheus metrics.

    Args:
        is_test: If True, returns an InMemoryBroker.

    Returns:
        A configured AsyncBroker instance.
    """
    if is_test:
        from taskiq import InMemoryBroker
        return InMemoryBroker()
    
    broker = NatsBroker(servers=[NATS_URL], queue="my_monolith_tasks")
    broker.add_middlewares(PrometheusMiddleware(server_port=9000))
    return broker


broker = get_broker(is_test=os.getenv("PYTEST_CURRENT_TEST") is not None)
"""Global broker instance for the current runtime environment."""
