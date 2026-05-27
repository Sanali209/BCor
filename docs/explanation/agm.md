# Explanation: AGM — Graph-Object Mapper для Neo4j

AGM (Agentic Grid Management) — это объектно-графовый маппер (GOM) для Neo4j, реализованный в модуле `src.modules.agm`. Он позволяет работать с Neo4j через декларативные Python-датаклассы, не пиша Cypher-запросы вручную.

## Проблема

Neo4j не имеет встроенного ORM. Стандартный подход — сырые Cypher-запросы и преобразование результатов вручную. При этом типичные задачи (сохранение связанных сущностей, обновление индексов, миграции) требуют большого объёма шаблонного кода.

## Решение AGM

AGM вводит декларативные аннотации полей, которые определяют, как каждое поле отображается на граф:

```python
@dataclass
class Asset:
    id: Annotated[str, Unique(), Hidden()]                  # UNIQUE constraint
    uri: Annotated[str, Indexed(), Searchable(priority=5)]   # RANGE index
    description: Annotated[
        str,
        Stored(source_field="uri", handler="BLIP", use_taskiq=True)  # Фоновый AI-пересчёт
    ] = ""
    tags: Annotated[
        list["Tag"],
        Rel(type="HAS_TAG"),                                 # Графовая связь
    ] = field(default_factory=list)
    embedding: Annotated[
        list[float],
        VectorIndex(dims=768)                                # Векторный индекс для поиска
    ] = field(default_factory=list)
```

## Ключевые концепции

### 1. Аннотации метаданных (`src.modules.agm.metadata.py`)

| Аннотация | Назначение | Где используется |
|-----------|-----------|------------------|
| `@Stored(source_field="uri", handler="CLIP")` | Поле вычисляется фоновым хендлером при изменении `uri` | `AGMMapper._handle_side_effects()` |
| `@Live(handler=SomeDIType)` | Поле заполняется из DI-контейнера при загрузке | `AGMMapper._hydrate_instance()` |
| `@Rel(type="HAS_TAG", direction="OUTGOING")` | Определяет графовую связь | `AGMMapper._handle_side_effects()` |
| `@Unique` | Создаёт UNIQUE constraint в Neo4j | `AGMSchemaManager.sync_class()` |
| `@Indexed` | Создаёт RANGE index | `AGMSchemaManager.sync_class()` |
| `@VectorIndex(dims=512, metric="cosine")` | Создаёт векторный индекс | `AGMSchemaManager.sync_class()` |
| `@OnComplete(depends_on=[...], handler="...")` | Действие после готовности полей (запланировано) | — |

### 2. AGMMapper (`src.modules.agm.mapper.py`)

Основной класс маппера. Выполняет три задачи:

**Загрузка (load):**
```python
record = {"id": "abc123", "uri": "file:///image.jpg", "labels": ["Asset", "ImageAsset"]}
asset = await mapper.load(ImageAsset, record, resolve_live=True)
```

- Парсит запись через Retort (адаптация типов: datetime, UUID, float).
- Проверяет Identity Map — не создаёт дубликатов.
- Определяет фактический класс через полиморфический реестр (по `labels`).
- Выполняет Live Hydration для полей c `@Live`.

**Сохранение (save/save_batch):**
```python
await mapper.save(image_asset, session=neo4j_session)
```

- **UNWIND-батчинг**: свойства сохраняются массово через `UNWIND $batch AS row MERGE (n {id: row.id}) SET n += row.props`.
- **Мерж лейблов**: `MATCH (n) WHERE n.id IN $ids SET n:Asset:ImageAsset`.
- **Связи**: для каждого `@Rel` поля создаёт/мержит отношение: `MATCH (n {id: $id}) MERGE (n)-[:HAS_TAG]->(m {id: $tid})`.
- **Side effects**: для каждого `@Stored` поля, если изменился исходный атрибут, публикует `NodeSyncRequested` с информацией о необходимых фоновых вычислениях.

**Идентификационная карта (Identity Map):**
```python
self._identity_map: dict[tuple[type, Any], Any] = {}
self._uri_map: dict[str, Any] = {}
```

Гарантирует, что каждый узел загружается только один раз за сессию маппера.

### 3. Fluent Queries (`src.modules.agm.fluent.py` и `query.py`)

Два API для построения Cypher-запросов:

**Fluent (QueryBuilder):**
```python
results = await mapper.query(ImageAsset) \
    .resolve_live() \
    .vector_search("vec_ImageAsset_clip_embedding", "sunset landscape", top_k=5) \
    .execute(session)
```

**CypherQuery (builder with filters):**
```python
query = CypherQuery(mapper, ImageAsset)
query.where(mime_type="image/jpeg") \
     .range("size", 1000, 100000) \
     .contains("name", "sunset") \
     .limit(20)

results = await query.all(session)
```

Поддерживает:
- Равенство: `.where(field=value)`.
- CONTAINS: `.contains("name", "sunset")`.
- RANGE: `.range("size", 1000, 100000)`.
- Vector NEAR: `.near("embedding", vector, limit=10)`.
- Delete: `.delete(session)` — DETACH DELETE всех совпавших узлов.

### 4. AGMSchemaManager (`src.modules.agm.schema.py`)

Автоматически синхронизирует схему Neo4j с классами Python:

```python
manager = AGMSchemaManager(driver)
await manager.sync_class(ImageAsset)
# → CREATE CONSTRAINT uniq_ImageAsset_id IF NOT EXISTS ...
# → CREATE INDEX idx_ImageAsset_uri IF NOT EXISTS ...
# → CALL db.index.vector.createNodeIndex('vec_ImageAsset_clip_embedding', ...)
```

Анализирует `typing.Annotated` поля и для каждого метаданного (`@Unique`, `@Indexed`, `@VectorIndex`) выполняет соответствующую Cypher-команду.

Также генерирует search schema для GUI:

```python
schema = manager.get_search_schema([Asset, ImageAsset, Tag])
# → [{"name": "name", "label": "Name", "type": "str", "widget": "text", "priority": 1}, ...]
```

### 5. Фоновая обработка (Stored fields)

Когда поле с `@Stored` меняется, AGMMapper не вычисляет его сам. Вместо этого он публикует событие:

```python
await self.message_bus.dispatch(NodeSyncRequested(
    node_id=node_id,
    fields=[SyncFieldInfo(field_name="description", handler="BLIP", ...)],
    mime_type="image/jpeg",
    use_taskiq=True,
))
```

Событие обрабатывается `handle_node_sync_requested` (`src.modules.agm/handlers.py`):

```python
async def handle_node_sync_requested(event, uow=None):
    if event.use_taskiq:
        await tasks.sync_node_metadata.kiq(node_id=..., fields=..., mime_type=...)
    else:
        await tasks.sync_node_metadata(node_id=..., fields=..., mime_type=...)
```

TaskIQ-таска вызывает конкретный хендлер (например, `CLIPHandler.run()`, `PHashHandler.run()`), результат записывается в Neo4j.

## Поток данных: от вставки до AI-обработки

```
1. Asset добавлен в AGMMapper.save()
   ↓
2. UNWIND MERGE в Neo4j (сохранение свойств + лейблов)
   ↓
3. MERGE связей (@Rel)
   ↓
4. Анализ @Stored-полей: что изменилось?
   ↓
5. NodeSyncRequested опубликован в MessageBus
   ↓
6. handle_node_sync_requested → TaskIQ sync_node_metadata
   ↓
7. CLIPHandler.run(uri) → 512-dim вектор
   ↓
8. Результат сохранён обратно в Neo4j
```

## Assets + AGM: самая мощная комбинация

В модуле `assets` (`src/modules/assets/domain/models.py`) определены 10+ классов с AGM-аннотациями. Когда `AssetsModule` стартует, он регистрирует их все в AGMMapper:

```python
async def startup(self):
    mapper = await self.container.get(AGMMapper)
    for model in [Asset, ImageAsset, VideoAsset, ...]:
        await mapper.register_subclass(model.__name__, model)
```

Это позволяет:
- Хранить изображения, видео, аудио, текст, физические объекты в одном графе.
- Автоматически запускать CLIP/BLIP/PHash при добавлении файла.
- Делать гибридный поиск (векторный + фильтры + отношения).

## Почему не использовать готовый OGM (Neomodel, Py2neo)?

| Критерий | Neomodel | AGM |
|----------|----------|-----|
| Асинхронность | Нет (синхронный) | Да (asyncio + Neo4j Async Driver) |
| DI-инжекция (@Live) | Нет | Да (Dishka) |
| Фоновые вычисления | Нет | Да (@Stored + TaskIQ) |
| Векторные индексы | Нет | Да (@VectorIndex) |
| Identity Map | Частично | Полная (id + uri) |
| UNWIND batch saves | Нет | Да |
| Polymorphic loading | Нет (только наследование моделей) | Да (через register_subclass) |

---

**Итог:** AGM — это async-native GOM для Neo4j с декларативными аннотациями, автоматической синхронизацией схемы, векторным поиском, фоновыми AI-вычислениями и полной интеграцией с BCor MessageBus и Dishka DI.
