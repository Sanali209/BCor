import os

from taskiq import PrometheusMiddleware
from taskiq_nats import NatsBroker

# From the prompt: "TaskiqInstrumentor" / "OpenTelemetryMiddleware"
# We will use the built-in instrumentor or custom middleware if it exists.
# `taskiq-opentelemetry` didn't exist in pip directly, but we can implement a basic span propagation middleware or just use Prometheus.


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
    force_real = os.getenv("TASKIQ_FORCE_REAL_BROKER") == "1"
    if is_test and not force_real:
        from taskiq import InMemoryBroker

        return InMemoryBroker()

    from taskiq_nats import NatsBroker
    from taskiq_redis import RedisAsyncResultBackend
    from taskiq_dashboard import DashboardMiddleware
    from src.adapters.taskiq_local_monitor import LocalMonitorMiddleware
    
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6380/1")
    
    result_backend = RedisAsyncResultBackend(redis_url=redis_url)
    broker = NatsBroker(servers=[nats_url], queue="bcor_assets").with_result_backend(result_backend)
    
    # Dashboard Middleware (Only if requested - prevents ConnectError on localhost:8000)
    if os.getenv("TASKIQ_DASHBOARD") == "1":
        broker.add_middlewares(
            PrometheusMiddleware(server_port=9000),
            DashboardMiddleware(
                url="http://127.0.0.1:8000",
                api_token="bcor-secret-token",
                broker_name="bcor_assets_worker",
            ),
        )
    else:
        broker.add_middlewares(PrometheusMiddleware(server_port=9000))
    
    # Local GUI Monitoring Middleware
    if os.getenv("BCOR_GUI_MONITOR") == "1":
        broker.add_middlewares(LocalMonitorMiddleware())
        
    return broker


broker = get_broker(is_test=os.getenv("PYTEST_CURRENT_TEST") is not None)
"""Global broker instance for the current runtime environment."""
