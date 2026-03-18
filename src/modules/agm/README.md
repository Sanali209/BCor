# Agentic Grid Management (AGM) Module

The `agm` module provides a powerful Graph-Object Mapping (GOM) layer designed for advanced agentic workflows involving knowledge graphs.

## Core Features
1. **GOM (Graph-Object Mapper)**: Transparently maps Python domain models to Neo4j nodes and relationships.
2. **Polymorphism**: Automatically loads the correct Python subclass based on Neo4j labels.
3. **Live Hydration**: Injects real-time data or service instances into model fields via Dishka dependency injection.
4. **Stored Fields**: Automatically triggers background recalculations (e.g., embeddings) when source fields change.
5. **Fluent API**: Provides a natural, high-level interface for querying the graph with built-in vector search support.

## Architectural Components
- `AGMMapper`: The central conversion engine.
- `QueryBuilder`: Fluent interface for Cypher query generation.
- `Live`, `Stored`, `Rel`: Semantic metadata for domain model fields.
- `TaskIQ Integration`: Handles asynchronous computations for data consistency.

## Example Domain Model
```python
class Agent(Aggregate):
    id: str
    name: str
    knowledge: Annotated[str, Stored(source_field="name")]  # Computed field
    tools: Annotated[list[Tool], Rel(type="HAS_TOOL")]     # Relationship
    status: Annotated[Status, Live(handler=StatusService)] # Live DI field
```
