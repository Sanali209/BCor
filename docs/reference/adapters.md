# Reference: Adapters

## SQLAlchemy

### SqlAlchemyRepository

**Модуль:** `src.adapters.repository.py`

```python
class SqlAlchemyRepository(AbstractRepository[T]):
    def __init__(self, session: Session, model_class: type[T])
```

- `_add()`: `self.session.add(aggregate)`
- `_get()`: сначала `session.get(model_class, reference)`, затем fallback `query.filter_by(ref=reference).first()`

### SqlAlchemyUnitOfWork

**Модуль:** `src.adapters.unit_of_work.py`

```python
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: Callable[[], Session], model_class: type[Aggregate])
```

- `__enter__`: создаёт сессию, инициализирует `SqlAlchemyRepository`.
- `_commit`: `self.session.commit()`.
- `rollback`: `self.session.rollback()`.

### ORM Mapper

**Модуль:** `src.adapters/orm.py`

```python
metadata = MetaData()
mapper_registry = registry(metadata=metadata)

def start_mappers() -> None:  # заглушка
    pass
```

Подготовлен для imperative mapping (связывание доменных классов с таблицами без декларативного базового класса).

---

## TaskIQ + NATS

### Broker

**Модуль:** `src.adapters.taskiq_broker.py`

```python
def get_broker(is_test: bool = False) -> AsyncBroker
broker = get_broker(is_test=...)  # глобальный инстанс
```

**Режимы:**
- **Test** (`is_test=True`, `TASKIQ_FORCE_REAL_BROKER!=1`): `InMemoryBroker` — для тестов.
- **Production**: `NatsBroker(servers=["nats://localhost:4222"])` с `RedisAsyncResultBackend(redis://localhost:6380/1)`.

**Middleware (настраивается через env):**
- `PrometheusMiddleware(server_port=9000)` — всегда.
- `DashboardMiddleware(url, api_token, broker_name)` — если `TASKIQ_DASHBOARD=1`.
- `LocalMonitorMiddleware` — если `BCOR_GUI_MONITOR=1`.

### LocalMonitorMiddleware

**Модуль:** `src.adapters.taskiq_local_monitor.py`

```python
class LocalMonitorMiddleware(TaskiqMiddleware):
    async def post_send(self, message): ...  # событие "queued"
    async def pre_execute(self, message): ...  # событие "started"
    async def post_execute(self, message, result): ...  # событие "executed"
```

Печатает JSON-строки с префиксом `[BCOR_TASK]` для захвата GUI-монитором:

```
[BCOR_TASK] {"event": "queued", "task_id": "...", "task_name": "...", "timestamp": "..."}
[BCOR_TASK] {"event": "started", "task_id": "...", "task_name": "...", "timestamp": "..."}
[BCOR_TASK] {"event": "executed", "task_id": "...", "status": "success", "execution_time": 1.23, "timestamp": "..."}
```

---

## Neo4j AGM (Graph-Object Mapper)

### AGMMapper

**Модуль:** `src.modules.agm.mapper.py`

```python
class AGMMapper:
    def __init__(self, container: AsyncContainer, message_bus: MessageBus, schema_manager: AGMSchemaManager | None = None)
    async def register_subclass(self, label: str, cls: type)
    def query(self, model_class: type[T]) -> CypherQuery[T]
    async def load(self, model_class: type[T], record: dict, resolve_live: bool = True) -> T
    async def save(self, model, previous_state=None, session=None)
    async def save_batch(self, models, session=None, previous_states=None)
```

**Ключевые возможности:**
- **Identity Map**: кеш (type, node_id) → instance. Не создаёт дубликатов.
- **Polymorphic loading**: по полю `labels` определяет подкласс через `register_subclass()`.
- **UNWIND batch**: сохранение через `UNWIND $batch AS row MERGE...`.
- **Live Hydration**: поля с `@Live` автоматически разрешаются из DI-контейнера.
- **Side Effects**: при сохранении создаёт/обновляет `@Rel`-связи и публикует `NodeSyncRequested`.

### AGMSchemaManager

**Модуль:** `src.modules.agm.schema.py`

```python
class AGMSchemaManager:
    def __init__(self, driver: Driver)
    async def sync_class(self, cls: type)
    def get_search_schema(self, classes: list[type]) -> list[dict]
```

Создаёт в Neo4j:
- `UNIQUE` constraint для полей с `@Unique`.
- `RANGE` index для полей с `@Indexed`.
- `VECTOR` index для полей с `@VectorIndex`.

### QueryBuilder / CypherQuery

**Модуль:** `src.modules.agm.fluent.py` / `src.modules.agm/query.py`

```python
# Fluent Query (src.modules.agm.fluent)
class QueryBuilder[T]:
    def resolve_live() -> QueryBuilder[T]
    def vector_search(index: str, query_text: str, top_k: int = 5) -> QueryBuilder[T]
    async def execute(session) -> list[T]

# CypherQuery (src.modules.agm/query)
class CypherQuery[T]:
    def where(**kwargs) -> CypherQuery[T]
    def contains(field, value) -> CypherQuery[T]
    def range(field, start, end) -> CypherQuery[T]
    def near(field, vector, limit=10) -> CypherQuery[T]
    def limit(n) -> CypherQuery[T]
    def build_cypher() -> tuple[str, dict]
    async def all(session) -> list[T]
    async def first(session) -> T | None
    async def delete(session) -> int
```

### Metadata (аннотации)

**Модуль:** `src.modules.agm.metadata.py`

| Декоратор | Описание | Параметры |
|-----------|----------|-----------|
| `@Stored` | Фоновый пересчёт поля | `source_field`, `source_fields`, `handler`, `use_taskiq`, `priority` |
| `@Live` | DI-инжекция при загрузке | `handler` — тип из контейнера |
| `@Rel` | Графовая связь | `type`, `direction` ("OUTGOING"/"INCOMING") |
| `@Unique` | UNIQUE constraint | — |
| `@Indexed` | RANGE index | — |
| `@VectorIndex` | Векторный индекс | `dims`, `metric` |
| `@OnComplete` | Действие после готовности полей | `depends_on`, `handler` |

**Пример:**

```python
class ImageAsset(Asset):
    clip_embedding: Annotated[
        list[float],
        Stored(source_fields=["uri"], mime_scope="image/*", handler="CLIP", use_taskiq=True),
        VectorIndex(dims=512)
    ] = field(default_factory=list)
```

---

## MongoDB

### MotorMongoAdapter

**Модуль:** `src.adapters.mongodb.motor_adapter.py`

```python
class MotorMongoAdapter:
    def __init__(self, host: str, port: int, database: str)
    async def find_one(self, collection, query) -> dict | None
    async def find(self, collection, query, limit=100) -> list[dict]
    async def insert_one(self, collection, document) -> str
    async def update_one(self, collection, query, update, upsert=False)
    async def delete_one(self, collection, query)
    def close(self)
```

---

## Web (Scraping)

### IBrowser / IExtractor (абстракции)

**Модуль:** `src.core.web/`

```python
class IBrowser(ABC):
    async def goto(self, url, wait_until=None) -> bool
    async def get_content(self) -> str
    async def screenshot(self, path) -> None
    async def close(self) -> None

class IExtractor(ABC):
    def set_content(self, html: str) -> None
    def select_text(self, selector, multiple=False) -> str | list[str] | None
    def select_attr(self, selector, attr, multiple=False) -> str | list[str] | None
```

### PlaywrightAdapter

**Модуль:** `src.adapters.web.playwright_adapter.py`

```python
class PlaywrightAdapter(IBrowser):
    def __init__(self, headless: bool = True)
```

- Использует Playwright Chromium.
- Поддерживает `networkidle` для дожидания загрузки.
- Устанавливает User-Agent Chrome + viewport 1920×1080.

### BS4Extractor

**Модуль:** `src.adapters.web.bs4_extractor.py`

```python
class BS4Extractor(IExtractor):
    def __init__(self)
```

- Использует BeautifulSoup с парсером "lxml".
- `select_text()` и `select_attr()` работают через `soup.select()` (CSS-селекторы).

### ScraperEngine

**Модуль:** `src.adapters.web.scraper_engine.py`

```python
class ScraperEngine:
    def __init__(self, browser: IBrowser, extractor: IExtractor, downloader: ResourceDownloader, config: ScraperConfig)
    async def scrape_site(self) -> list[TopicData]
```

- Для каждого start_url обрабатывает пагинацию (ищет `pagination_next` селектор).
- Для каждой темы: загружает страницу, парсит поля, скачивает ресурсы через `ResourceDownloader`.
- Используется в Boruscrapper и Asset Explorer.

---

## JSON Repository

**Модуль:** `src.adapters.persistence.json_repository.py`

```python
class JsonRepository(AbstractRepository[T], Generic[T]):
    def __init__(self, file_path: str | Path, model_class: type[T])
    def list(self) -> list[T]
    def remove(self, reference: str) -> bool
```

- Хранит агрегаты в JSON-файле.
- Использует Pydantic `TypeAdapter` для валидации.
- Автоматически загружает из файла при инициализации и сохраняет при `_add()`.
- Сериализация через `model_dump(mode="json")`.

---

## HandlerRegistry

**Модуль:** `src.modules.assets.infrastructure.registry.py`

```python
class HandlerRegistry:
    def register(self, mime_pattern: str, handler: type)
    def register_named(self, name: str, handler: type)
    def resolve(self, mime_type: str, handler_name: str | None = None) -> type | None
```

MIME-диспетчеризация с приоритетом:
1. Явное имя (`handler_name`).
2. Полное совпадение MIME.
3. Категория (`image/*`).
4. Wildcard (`*/*`).

---

## Портируемые адаптеры

**Модуль:** `src.porting/`

- `LegacyAllocatorBridge` — мост для старого кода.
- `BaseGuiAdapter` — адаптация PySide6 GUI.
- `ui_bridge.py` — интеграция с `sanali`/`SLM` legacy кодом.
