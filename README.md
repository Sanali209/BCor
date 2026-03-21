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

### 1. Композитный корень (Composition Root & Settings)
Система собирается воедино классом `System` (`src/core/system.py`).
Вместо глобальных монолитных конфигов, настройки объявляются декларативно внутри каждого модуля через Pydantic-схемы (Fail-Fast принцип). Во время бутстрапа (запуска приложения) `System` обходит все модули, инстанцирует их конфигурацию из переменных окружения и возвращает провалидированный объект `module.settings`.

Также `System` собирает все DI-провайдеры (используя библиотеку `dishka`) в единый асинхронный IoC-контейнер. Жизненный цикл жестко разграничен:
*   `Scope.APP`: Настройки, пулы соединений, Шина сообщений.
*   `Scope.REQUEST`: Открытая транзакция к базе данных (через `AbstractUnitOfWork`).

### 2. Внутренняя Шина Сообщений (bubus CQRS)
Ядро маршрутизации реализовано в `src/core/messagebus.py`, оборачивающем `bubus.EventBus`. Оно строго разделяет два типа сообщений:
*   **Команды (Commands):** Выражают намерение. Маршрутизируются строго к *одному* обработчику. Если возникает ошибка (например, валидация или бизнес-правило), она пробрасывается наверх (Fail Fast).
*   **События (Events):** Факт, который уже произошел (например, `OrderCreated`). Рассылаются *многим* подписчикам. Ошибки в обработчиках событий изолируются: они логируются, но не ломают транзакцию и цикл обработки других событий (Fail Safe).

Шина сообщений автоматически внедряет `UnitOfWork` (запрошенный через Dishka) в обработчики, а после успешного выполнения — собирает из него новые сгенерированные Доменные События (`uow.collect_new_events()`) и публикует их в шину.

### 3. Распределенное выполнение тяжелых задач (TaskIQ + NATS)
Не все операции можно выполнить в рамках синхронного цикла запроса. Для долгих процессов (отправка email, генерация отчетов) используется связка **TaskIQ + NATS** (`src/adapters/taskiq_broker.py`).
Событие или Команда внутри `bubus` вызывает асинхронную функцию через `.kiq()`, которая мгновенно передает задачу в брокер NATS. Затем отдельный фоновый процесс (воркер TaskIQ) вычитывает эту задачу и выполняет её, сохраняя высокую производительность API и UI.

### 4. Доменная Модель и Отказоустойчивость
*   **Агрегаты (Aggregates):** Являются корнями согласованности. Они не публикуют события напрямую, а накапливают их во внутреннем списке `self.events`, откуда их забирает `UnitOfWork`.
*   **Репозитории (Repositories):** Инкапсулируют логику работы с БД. Умеют сохранять и извлекать только Агрегаты.
*   **Result Monads:** Чтобы избежать бизнес-логики, построенной на `try-except` (что является антипаттерном), используется библиотека `returns`. Хэндлеры возвращают типизированные контейнеры `BusinessResult` (Success / Failure).

### 5. Наблюдаемость (Observability)
Для контроля над распределенной и асинхронной системой внедрены следующие инструменты:
*   **Логирование:** Встроенный модуль `logging` заменен на `loguru` (в том числе при обработке событий `bubus`).
*   **Трассировка:** Каждый переход Команды или События внутри `MessageBus` оборачивается в спаны `OpenTelemetry`. Это позволяет видеть сквозной путь данных от HTTP-запроса до NATS-воркера.
*   **Метрики:** NATS-брокер `TaskIQ` содержит встроенный `PrometheusMiddleware`, отдающий метрики на порту 9000.

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
*   [Search Module](src/modules/search/README.md) — Модуль поиска.

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
