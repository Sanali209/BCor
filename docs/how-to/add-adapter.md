# How-to: Добавить новый адаптер инфраструктуры

В BCor адаптеры живут в `src/adapters/`. Каждый адаптер — это конкретная реализация абстрактного интерфейса из `src/core/`.

## 1. Выберите, какой паттерн реализовать

BCor поддерживает четыре типа адаптеров:

| Паттерн | Абстракция в core | Существующие реализации |
|---------|-------------------|----------------------|
| Repository | `AbstractRepository[T]` | `SqlAlchemyRepository`, `JsonRepository` |
| Unit of Work | `AbstractUnitOfWork` | `SqlAlchemyUnitOfWork` |
| Browser | `IBrowser` | `PlaywrightAdapter` |
| Extractor | `IExtractor` | `BS4Extractor` |

## 2. Пример: новый репозиторий для PostgreSQL через asyncpg

```python
# src/adapters/persistence/postgres_repository.py
from typing import TypeVar
from src.core.domain import Aggregate
from src.core.repository import AbstractRepository

T = TypeVar("T", bound=Aggregate)

class PostgresRepository(AbstractRepository[T]):
    def __init__(self, pool, model_class: type[T]):
        super().__init__()
        self.pool = pool
        self.model_class = model_class

    def _add(self, aggregate: T) -> None:
        # INSERT INTO ... ON CONFLICT ...
        pass  # реальная имплементация

    def _get(self, reference: str) -> T | None:
        # SELECT * FROM ... WHERE ref = $1
        pass  # реальная имплементация
```

**Контракт `AbstractRepository`:**
- `add(aggregate)` — добавляет и помечает в `self.seen`.
- `get(reference)` — возвращает агрегат и помечает в `self.seen`.
- `_add()`, `_get()` — вы реализуете их в конкретном классе.

## 3. Пример: новый адаптер браузера (Selenium)

Интерфейс `IBrowser` определён в `src/core/web/i_browser.py`:

```python
from src.core.web.i_browser import IBrowser

class SeleniumAdapter(IBrowser):
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    async def goto(self, url: str, wait_until=None) -> bool:
        # driver.get(url)
        return True

    async def get_content(self) -> str:
        return self.driver.page_source

    async def screenshot(self, path: str) -> None:
        self.driver.save_screenshot(path)

    async def close(self) -> None:
        if self.driver:
            self.driver.quit()
```

## 4. Пример: новый адаптер извлечения данных (lxml)

Интерфейс `IExtractor` в `src/core/web/i_extractor.py`:

```python
from src.core.web.i_extractor import IExtractor

class LxmlExtractor(IExtractor):
    def __init__(self):
        self._tree = None

    def set_content(self, html: str) -> None:
        from lxml import html
        self._tree = html.fromstring(html)

    def select_text(self, selector: str, multiple=False):
        if not self._tree:
            return [] if multiple else None
        results = self._tree.cssselect(selector)
        texts = [r.text_content().strip() for r in results]
        return texts if multiple else texts[0]

    def select_attr(self, selector: str, attr: str, multiple=False):
        if not self._tree:
            return [] if multiple else None
        results = self._tree.cssselect(selector)
        values = [r.get(attr) for r in results if r.get(attr)]
        return values if multiple else values[0]
```

## 5. Регистрация адаптера в DI-контейнере

Адаптер регистрируется в Dishka Provider вашего модуля:

```python
# src/modules/mymodule/module.py
from dishka import Provider, Scope, provide
from src.adapters.persistence.postgres_repository import PostgresRepository
from src.core.repository import AbstractRepository

class MyModuleProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_repo(self, pool) -> AbstractRepository:
        return PostgresRepository(pool=pool, model_class=MyAggregate)
```

## 6. Существующие адаптеры для справки

- **SqlAlchemyRepository** (`src/adapters/repository.py`): принимает `session` + `model_class`.
- **SqlAlchemyUnitOfWork** (`src/adapters/unit_of_work.py`): принимает `session_factory` + `model_class`.
- **JsonRepository** (`src/adapters/persistence/json_repository.py`): файловое хранилище с Pydantic-сериализацией.
- **MotorMongoAdapter** (`src/adapters/mongodb/motor_adapter.py`): MongoDB через `motor`.
- **PlaywrightAdapter** (`src/adapters/web/playwright_adapter.py`): headless Chrome.
- **BS4Extractor** (`src/adapters/web/bs4_extractor.py`): BeautifulSoup с CSS-селекторами.
- **ScraperEngine** (`src/adapters/web/scraper_engine.py`): оркестратор браузера + экстрактора с пагинацией.
- **TaskIQ broker** (`src/adapters/taskiq_broker.py`): NATS/InMemory брокер с Prometheus + Dashboard.

---

**Итог:** 1) наследуетесь от абстракции в `src/core/`, 2) реализуете конкретные методы, 3) регистрируете в Dishka Provider.
