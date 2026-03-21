# Search Module

The `search` module provides web and image search capabilities within the BCor system.

## Core Concepts
- **Search Abstraction**: Unified interface for different search providers (DuckDuckGo, Google, etc.).
- **Image Search**: Specialized support for image search queries.
- **Event-Driven Results**: Emits events with search results for further processing.

## Components
- `SearchImagesCommand`: Command to search for images based on query.
- `SearchProvider`: Dependency provider for search adapters.
- `search_images_handler`: Handler that executes the search and emits results.

## Workflow
1. User sends a `SearchImagesCommand` with search query.
2. `SearchProvider` provides the configured search adapter.
3. `search_images_handler` executes the search via the adapter.
4. Search results are returned and can be processed further.

## Configuration
Configure the search adapter in your application's `app.toml`:
```toml
[modules.search]
adapter = "duckduckgo"  # or "google", "bing", etc.
api_key = "your-api-key"  # if required
```

## Dependencies
- `bubus`: Event bus for message routing.
- `dishka`: Dependency injection.
- Search-specific libraries (e.g., `duckduckgo-search`, `google-api-python-client`).