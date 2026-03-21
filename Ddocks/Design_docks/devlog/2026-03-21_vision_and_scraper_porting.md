# Devlog: Phase 2 & 3 - Vision & Scraper Porting (2026-03-21)

## Context
As part of the BCor modernization effort, we targeted two major legacy components for porting:
1.  **AI Image Tagging** (`llm_tags_to_xmp` logic).
2.  **Web Scraping Engine** (legacy site-specific scrapers).

The goal was to move from monolithic/script-based logic to a decoupled, async-first, and type-safe hexagonal architecture.

## Accomplishments

### 1. Unified Vision Infrastructure (`src/modules/vision`)
- **Shared Port**: Defined `IVisionTagger` in the `vision` module to standardize image analysis.
- **WD-Tagger Implementation**: Refactored the experimental `WDTaggerAdapter` from `ImageDedup` into the shared module. It now uses `timm` and `torch` for high-performance localized tagging (optimized for anime/art).
- **LLM-Vision Integration**: Enhanced the `llm` module's `ILlmAdapter` to support multimodal requests (Gemini-1.5-Flash).
- **App Integration**: `ImageDedup` now leverages both adapters via its `IImageTagger` port, allowing for a mix of local and cloud-based AI tagging.

### 2. Modular Web Scraping Engine (`src/adapters/web`)
- **Clean Separation**: Created `IBrowser` (Playwright) and `IExtractor` (BeautifulSoup) ports.
- **Scraper Engine**: Implemented a re-usable `ScraperEngine` that orchestrates navigation, pagination, and data extraction using site-specific JSON configurations.
- **Resilience**: Added `ResourceDownloader` with async support, referrer handling, and automated file extension detection.
- **Portability**: Transitioned legacy site configurations (e.g., `danbooru.json`) to the new framework.

### 3. Code Quality & Standards
- **Type Safety**: Achieved 100% Mypy compliance in all new modules (`vision`, `llm`, `adapters/web`).
- **Linting**: 100% Ruff compliance, resolving over 50+ violations through refactoring.
- **Dependency Isolation**: Confirmed zero direct imports of legacy `SLM` files in the new BCor components.

## Key Design Decisions
- **Experimental First -> Shared**: Followed ADR-0008 by starting tagging in `ImageDedup` and then scaling it to `src/modules/vision` once stable.
- **Async-First Web**: Chose Playwright's async API to ensure high concurrency without blocking the event loop.
- **DI-Driven Adapters**: Integrated both systems into Dishka providers for seamless swapping of implementations (e.g., Mock browser for testing).

## Technical Gotchas
- **Mypy on BS4**: Required specific `# type: ignore` and casts for dynamic attribute access (`el.get(attr)`).
- **Qt vs Asyncio**: Navigated complex concurrency issues in the `ImageDedup` GUI to ensure AI inference doesn't freeze the interface.

## Next Steps
- Implement Phase 4: Full project-wide verification.
- Scale the scraper to support more complex JavaScript-heavy sites.
- Benchmark the local `WDTagger` against Gemini Flash for accuracy and cost.
