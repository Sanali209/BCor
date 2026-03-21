# ADR 0008: Infrastructure for ML Models and Metadata I/O

## Status
Proposed (Draft)

## Context
Phase 2 involves porting the `llm_tags_to_xmp` functionality, which uses Deep Learning models (`wd-vit-tagger-v3`) and direct file metadata operations (`pyexiv2`). 
According to ADR 0007, LLM/NLP concepts belong to Phase 3 and `src/modules/llm/`. However, the current requirement is to port this functionality into `ImageDedup` in Phase 2.

Additionally, legacy code uses complex structured logging (`ProcessingPhase`) that is not present in `BCor Core`.

## Decision
1.  **Experimental Phase 2 (Local App Logic)**:
    - We will implement the `llm_tags_to_xmp` functionality *directly* within `src/apps/ImageDedup/` following the "Experimental First" principle (ADR 0004).
    - AI Model logic (`WD-Tagger`) and XMP Write logic (`PyExiv2`) will be encapsulated in `ImageDedup/adapters/`.
    
2.  **Metadata Interfaces**:
    - `IXmpMetadata` and `IImageTagger` remain at the domain level of the application.
    - If these interfaces prove universal, they will be migrated to `src/common` or `src/modules` in Phase 3.

3.  **Dependency Handling**:
    - Heavy dependencies (`torch`, `timm`, `pyexiv2`) are registered under `[project.optional-dependencies] legacy-phase1` to keep the core lean.

4.  **Logging Strategy**:
    - We will **NOT** port the legacy `ProcessingPhase` structured logging to BCor Core yet.
    - Instead, we will use standard `loguru` with contextual `extra` fields to track operations, keeping infrastructure-specific logging simple.

## Consequences
- **Positive**: Enables immediate porting of tagging features without waiting for the full LLM module structure. Aligns with ADR 0004's Experimental First principle.
- **Negative**: Temporary duplication if the same logic is needed in `ImageAnalyze` before the migration to System Modules.
- **Collision**: Slight deviation from Phase 3 timeline in ADR 0007, justified by immediate application need.
