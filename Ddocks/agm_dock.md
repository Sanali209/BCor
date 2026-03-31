# Модуль AGM (Aetheris Graph Mapper)

## Обзор (Overview)
**AGM** — это высокоуровневый объектно-графовый маппер (OGM) для Neo4j, разработанный для упрощения работы с графами знаний в агентских системах. Он объединяет декларативное описание схем с мощными механизмами реактивной обработки данных.

---

## Декларативные метаданные (Declarative Metadata)
AGM использует `typing.Annotated` для расширения стандартных dataclasses/Pydantic моделей семантикой графа.

### 1. Поля и Индексы (Fields & Indices)
*   **`Unique`**: Помечает поле как уникальное (создает Neo4j Uniqueness Constraint).
*   **`Indexed`**: Создает стандартный Range-индекс для быстрого поиска.
*   **`VectorIndex(dims=N, metric="cosine")`**: Создает векторный индекс Neo4j для семантического поиска.

### 2. Реактивность (Reactivity)
*   **`Stored`**: Указывает, что поле вычисляется асинхронно при изменении исходников (`source_fields`).
    *   `fusion_params`: Настройки комбинирования данных из нескольких источников.
    *   `mime_scope`: Фильтрация обработчиков по MIME-типу актива.
*   **`Live(handler)`**: Поле гидратируется динамически из DI-контейнера при каждой загрузке объекта (не сохраняется в БД).
*   **`OnComplete(depends_on=(...), handler=...)`**: Декларативный хук, который срабатывает только тогда, когда все перечисленные поля заполнены.

### 3. Связи (Relationships)
*   **`Rel(type, direction, metadata=...)`**: Определяет связь в графе.
    *   `metadata`: Класс, описывающий свойства самой связи (properties on edges).

---

## Техническая архитектура (Technical Architecture)

### Core Components
1.  **`AGMMapper`**: The main interface for `load()` and `save()`. It handles polymorphism, relationship traversal, and change detection.
2.  **`QueryBuilder`**: A fluent API in `src/modules/agm/fluent.py` for generating complex Cypher queries with built-in support for vector search.
3.  **`Reactive Processor`**: Monitors changes during `save()` and emits `NodeSyncRequested` events to the common `MessageBus`.

### Event Flow (Modern EDA)
AGM does not execute long-running tasks directly. Instead:
1. `AGMMapper` detects changes to `Stored` fields.
2. It publishes a **`NodeSyncRequested`** event to the `bubus` MessageBus.
3. A background handler (see `src/modules/agm/handlers.py`) routes this to **TaskIQ** for asynchronous execution by workers.

---
*Note: Code reference: [src/modules/agm/](file:///d:/github/BCor/src/modules/agm/)*