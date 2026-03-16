import asyncio
from bubus import EventBus, BaseEvent

class E(BaseEvent):
    pass

async def main():
    bus = EventBus()
    def h(e):
        raise ValueError("X")
    bus.on(E, h)
    res = await bus.dispatch(E())

    print("res dict?", dir(res))
    print("res is ", type(res))
    print("res.event_results=", res.event_results)

    for k, v in res.event_results.items():
        print("v=", type(v), dir(v))
        print("v.error=", getattr(v, "error", None))

    bus._is_running = False

asyncio.run(main())
