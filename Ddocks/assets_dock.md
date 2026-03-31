# Модуль Assets (Asset Explorer Core)

## Обзор (Overview)
Модуль **Assets** является центральным компонентом системы для управления цифровыми и физическими активами. Он обеспечивает декларативное описание моделей, автоматизированный захват метаданных (Ingestion) и интеграцию с графовой базой данных через модуль `AGM`.

---

## Доменные модели (Domain Models)
Все модели наследуются от базового класса `Asset` и используют аннотации `AGM` для управления персистентностью.

### 1. Цифровые активы (Digital Assets)
*   **ImageAsset**: Растровые изображения (JPEG, PNG, RAW). Поддерживает извлечение EXIF, генерацию перцептивных хэшей и эмбеддингов.
*   **VideoAsset**: Видеофайлы. Интеграция с FFmpeg для извлечения кадров и метаданных контейнера.
*   **AudioAsset**: Аудиофайлы. Спектральный анализ и транскрибация (в планах).
*   **TextAsset**: Текстовые документы, логи, markdown.
*   **DocumentAsset** *(TD-0003)*: Сложные документы (PDF, DOCX). Находится в стадии реализации.

### 2. Организационные модели
*   **Tag**: Свободные теги для классификации.
*   **Project**: Группировка активов в рамках рабочих процессов.
*   **Product**: Привязка активов к конкретным товарным единицам.

---

## Техническая спецификация (Technical Reference)

### Lifecycle & DI Integration
The module is initialized via `AssetsModule` in `src/modules/assets/module.py`.
1.  **Registration**: During the `startup()` phase, the module automatically registers all domain subclasses with the `AGMMapper` to ensure correct polymorphic loading from Neo4j.
2.  **Providers**: Infrastructure is managed by `AssetsInfrastructureProvider`, which injects:
    *   `AssetIngestionService`: Orchestrates the import pipeline.
    *   `AssetFactory`: Determines the correct asset type based on MIME/Extension mapping.

### Ingestion Pipeline
Managed by `AssetIngestionService`. The flow is as follows:
1.  **Discovery**: Scans the filesystem (via `VFS` or local OS walk).
2.  **Identification**: Uses `AssetFactory` to instantiate the correct domain model.
3.  **Persistance**: Saves the initial record to Neo4j via `AGMMapper.save()`.
4.  **Enrichment**: Publishes `NodeSyncRequested` events to trigger background metadata extraction (embeddings, object detection).

---
*Note: Code reference: [src/modules/assets/](file:///d:/github/BCor/src/modules/assets/)*
