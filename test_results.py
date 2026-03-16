import asyncio
from bubus import EventBus, BaseEvent

class E(BaseEvent):
    pass

async def main():
    bus = EventBus()
    @bus.on(E)
    def h(e):
        raise ValueError("X")

    res = await bus.dispatch(E())
    print("RES:", res)
    for r in res:
        print("result object:", type(r), dir(r))
        print("error:", r.error)

asyncio.run(main())
