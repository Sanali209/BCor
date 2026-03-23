# Модульный Монолит, Управляемый Событиями (Event-Driven Modular Monolith)

Это ядро архитектурного фреймворка, построенное на принципах чистой архитектуры, предметно-ориентированного проектирования (DDD), разделения команд и запросов (CQRS) и асинхронного выполнения задач.

Вся документация в этом репозитории следует правилу **Code First** (Сначала Код): источником истины является актуальная реализация, описанная здесь.

## Основной стек технологий (The Stack)
*   **Управление пакетами:** `uv`
*   **Внутренняя шина событий (In-Memory Bus):** `bubus`
*   **DI-Контейнер:** `dishka`
*   **Декларативные настройки (Settings):** `pydantic-settings`
*   **Внешний брокер (Фоновые задачи):** `TaskIQ` + `NATS` (`taskiq-nats`)
*   **Отказоустойчивость и обработка ошибок:** `returns` (Result Monad)
*   **Наблюдаемость (Observability):** `loguru` (Логирование), `OpenTelemetry` (Распределенная трассировка), `Prometheus` (Метрики воркеров)
*   **Тестирование:** `pytest`, `pytest-asyncio`

---

## Архитектура системы
Система построена на принципах чистой архитектуры. Подробное описание компонентов, таких как MessageBus, UnitOfWork и паттерны DDD/CQRS, перенесено в профильные документы.

> 👉 **См. раздел "Explanation" (Документация) ниже для полных руководств по архитектуре.**

---

## Структура проекта
```text
.
├── src/
│   ├── adapters/         # Внешние системы (ORM мапперы, брокеры NATS)
│   ├── core/             # Ядро (MessageBus, UnitOfWork, Monads, System)
│   ├── entrypoints/      # Точки входа (FastAPI, CLI, PySide)
│   └── modules/          # Бизнес-модули (Изолированные домены)
├── tests/
│   ├── conftest.py       # FakeRepository, FakeUnitOfWork
│   └── unit/             # Быстрые тесты бизнес-логики (TDD)
├── Ddocks/               # Концептуальная документация
├── pyproject.toml        # Конфигурация uv и зависимостей
└── README.md             # Этот файл
```

## Документация (Documentation)
Подробное описание компонентов и руководства доступны в директории `Ddocks/`:

### Архитектура и дизайн
*   [ARCHITECTURE.md](ARCHITECTURE.md) — Полная документация архитектуры системы.
*   [Roadmap](Ddocks/Roadmap.md) — Текущий статус и план разработки.
*   [Concept Doc](Ddocks/Conceptdock.md) — Общее архитектурное видение.
*   [Design Document](Ddocks/Dizdok.md) — Дизайн-документ ядра и структуры монорепозитория.
*   [Specification](Ddocks/Specification.md) — Развернутая спецификация архитектурного ядра.
*   [Technical Task](Ddocks/Tech%20tasck.md) — Техническое задание на разработку ядра.

### ADR (Architecture Decision Records)
*   [ADR 0001: Strangler Fig](Ddocks/Design_docks/ADR/0001-strangler-fig-bcor-integration.md) — Паттерн "Душитель" для миграции.
*   [ADR 0002: Domain Core](Ddocks/Design_docks/ADR/0002-domain-core-design.md) — Проектирование Domain Core.
*   [ADR 0003: Infrastructure Adapters](Ddocks/Design_docks/ADR/0003-infrastructure-adapters.md) — Реализация адаптеров.
*   [ADR 0004: Code Layering](Ddocks/Design_docks/ADR/0004-code-layering-strategy.md) — Стратегия разделения уровней.
*   [ADR 0005: UV Package Management](Ddocks/Design_docks/ADR/0005-uv-package-management.md) — Управление пакетами.
*   [ADR 0006: Python 3.12](Ddocks/Design_docks/ADR/0006-python-3.12-syntax.md) — Синтаксис Python 3.12.
*   [ADR 0007: Legacy Migration ACL](Ddocks/Design_docks/ADR/0007-legacy-migration-acl-strategy.md) — Стратегия миграции легаси.

### Модули
*   [Orders Module](Ddocks/orders_dock.md) — Описание эталонного бизнес-модуля.
*   [AGM Module](Ddocks/agm_dock.md) — Детали графового маппера.
*   [ECS Module](Ddocks/ecs_dock.md) — Entity Component System.
*   [VFS Module](Ddocks/vfs_dock.md) — Virtual File System.
*   [Analytics Module](src/modules/analytics/README.md) — Модуль аналитики.
*   [LLM Module](src/modules/llm/README.md) — Модуль LLM и NLP.
*   [Files Module](src/modules/files/README.md) — Модуль работы с файлами.

### Руководства
*   [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Полное руководство разработчика.
*   [How-to: Add New Module](Ddocks/How-tos/Add_New_Module.md) — Гид для создания новых модулей.
*   [First Steps](firststeps.md) — Как начать работу с репозиторием.

### Русскоязычные версии
*   [ARCHITECTURE_ru.md](ARCHITECTURE_ru.md) — Документация архитектуры на русском языке.
*   [DEVELOPER_GUIDE_ru.md](DEVELOPER_GUIDE_ru.md) — Руководство разработчика на русском языке.

### Спецификации
*   [Linting Strategy](Ddocks/Design_docks/specs/2026-03-19-linting-strategy.md) — Стратегия линтинга (Ruff + Mypy).
*   [Legacy Import Map](Ddocks/Design_docks/specs/2026-03-19-legacy-import-map.md) — Карта импортов легаси кода.
*   [Class Map](Ddocks/Design_docks/Class%20map.md) — Карта классов и их расположения.

## Разработка
Все новые фичи разрабатываются через **TDD (Test-Driven Development)** с использованием `pytest`.
Поддельные адаптеры (`FakeRepository`, `FakeUnitOfWork` в `conftest.py`) позволяют мгновенно тестировать сервисный слой без необходимости поднимать Docker-контейнеры с базами данных.

➡️ **Как начать работу с репозиторием:** Читайте руководство [First Steps](firststeps.md).
