# Asset Explorer Dashboard Design Spec

**Date**: 2026-03-29
**Status**: DRAFT
**Author**: Antigravity

## 1. Goal
Create a 10x-productive, framework-native desktop application for exploring, searching, and managing image assets within the BCor environment. 

## 2. Architecture Overview

### 2.1 Technology Stack
- **UI Framework**: PySide6 (Qt for Python).
- **Concurrency**: `qasync` for integration with BCor's `asyncio` base.
- **Dependency Injection**: `Dishka` for component wiring (AGMMapper, IngestionService).
- **Database**: Neo4j (via AGMMapper).
- **Processing**: TaskIQ background workers (monitored via companion logic).

### 2.2 MVVM Structure
- **Models**: BCor Domain Models (`ImageAsset`).
- **ViewModels**:
    - `AssetExplorerViewModel`: Orchestrates search, selection, and collection of assets.
    - `MetadataViewModel`: Reactive proxy for a single asset, providing dynamic field descriptors.
    - `InfrastructureViewModel`: Monitors service health and background task logs.
- **Views**:
    - `MainWindow`: Splitter-based 3-panel layout.
    - `TabWidget`: Separates "Explorer" and "Infrastructure" (Embedded Companion).

## 3. UI/UX Design

### 3.1 The 3-Panel Explorer Tab
*   **Left (Query Constructor)**:
    - Text search for tags.
    - MIME-type filters.
    - Similarity Search area (drop image to find similar).
*   **Middle (Preview Results)**:
    - Grid/List of `AssetCard` widgets.
    - Lazy-loaded thumbnails from CAS.
*   **Right (Auto-GUI Metadata)**:
    - Dynamic form generation via `typing.get_type_hints` inspection.
    - `Stored` annotations -> Text fields + "Recompute" buttons.
    - `Rel` annotations -> Read-only Tag Clouds.
    - Automatic UI updates on `MessageBus` events (`AssetInferredEvent`).

### 3.2 The Infrastructure Tab (Embedded Companion)
- Integrates the logic from `src/apps/experemental/declarative_imgededupe/companion.py`.
- **Worker Panel**: Status and controls for TaskIQ.
- **Task Monitor**: Live table of background task statuses.
- **AI Progress**: Fine-grained logs for models (BLIP, CLIP, etc.).

## 4. Key Workflows

### 4.1 Asset Ingestion
- **Single**: File dialog -> Ingestion Service -> Graph Persistence -> Task Trigger.
- **Mass**: Directory dialog -> Recursive Scan -> Batch Ingestion.

### 4.2 Search & Discovery
- Query Constructor builds an `AGMQuery`.
- `AGMMapper` executes query in Neo4j.
- Results update the reactive `AssetCollectionViewModel`.

### 4.3 Database Maintenance
- "Clear DB" button: Purges Neo4j nodes (with confirmation) and resets CAS if requested.

## 5. Security & Stability
- Async/Await everywhere to prevent UI freezing on heavy I/O or AI inference.
- Error handling at the "Service" layer with UI notifications via `StatusMessageBus`.
