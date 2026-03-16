import os
from taskiq_nats import NatsBroker

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
