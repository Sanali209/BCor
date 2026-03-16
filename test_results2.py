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

    # Let's inspect EventResult
    for r in res:
        print("Exception property:", getattr(r, 'exception', None))
        print("Error property:", getattr(r, 'error', None))
        print("Result:", r)

asyncio.run(main())
