import asyncio
from typing import Annotated, NewType
from dataclasses import dataclass, field
from src.modules.agm.metadata import Stored, Live, Rel
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.fluent import QueryBuilder
from dishka import make_async_container, Provider, Scope, provide

LiveStatusFetcher = NewType("LiveStatusFetcher", str)


@dataclass
class TargetNode:
    id: str


@dataclass
class AetherisBaseNode:
    id: str
    text_content: str
    embedding: Annotated[list[float], Stored(source_field="text_content")] = field(
        default_factory=list
    )
    current_status: Annotated[str, Live(handler=LiveStatusFetcher)] = "offline"
    friends: Annotated[list[TargetNode], Rel(type="KNOWS", direction="OUTGOING")] = (
        field(default_factory=list)
    )


class LiveDataProvider(Provider):
    scope = Scope.APP

    @provide
    async def fetch_status(self) -> LiveStatusFetcher:
        await asyncio.sleep(0.01)
        return LiveStatusFetcher("online-active")


async def main():
    container = make_async_container(LiveDataProvider())
    mapper = AGMMapper(container)

    # Fake Neo4j record
    record = {
        "id": "node-777",
        "text_content": "AGM Integration Example",
        "embedding": [0.12, 0.44, 0.98],
        "friends": [{"id": "node-999"}],
    }

    print("Loading Node with Edges...")
    node = await mapper.load(AetherisBaseNode, record, resolve_live=True)

    print(f"Loaded Node: {node.id}")
    print(f"Friends: {node.friends}")

    print("\nSaving Node...")
    try:
        await mapper.save(node, previous_state=record)
    except Exception as e:
        print(f"Error saving node: {e}")

    builder = QueryBuilder(mapper, AetherisBaseNode)
    query = builder.vector_search(
        "text_index", "find integration", top_k=3
    ).resolve_live()
    print("\nSmart Projection Execution:")
    await query.execute(session=None)


if __name__ == "__main__":
    asyncio.run(main())
