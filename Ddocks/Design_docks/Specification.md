**РАЗВЕРНУТАЯ СПЕЦИФИКАЦИЯ АРХИТЕКТУРНОГО ЯДРА СИСТЕМЫ**

Данный документ описывает спецификацию архитектурного ядра приложения, построенного на принципах предметно-ориентированного проектирования (DDD), разделения ответственности команд и запросов (CQRS) и событийно-ориентированной архитектуры (EDA).

---

### 1. Фундаментальные архитектурные принципы

*   **Инверсия зависимостей (Dependency Inversion Principle, DIP):** Модули верхнего уровня не зависят от деталей инфраструктуры. Абстракции реализуются через абстрактные базовые классы (`abc.ABC`). *(В коде реализовано через `src/core/repository.py` и `src/core/unit_of_work.py`)*.
*   **Слабая связанность через события (Event-Driven Architecture):** Сервисы взаимодействуют асинхронно через обмен событиями. *(В коде реализовано: шина `bubus` и брокер `TaskIQ/NATS`)*.
*   **CQRS (Command Query Responsibility Segregation):** Separation of write (Commands) and read (Queries) models.
    *   *Implementation:* Commands are handled via `MessageBus`. Read models utilize direct SQL/Cypher projections (e.g., in `src/modules/*/queries.py` or via `AGM` fluent builder).
*   **Railway Oriented Programming (ROP):** Business flows use the `Result` monad for graceful error handling. *(Implemented via `src/core/monads.py`)*.

---

### 2. Спецификация слоев и компонентов

#### 2.1. Предметная область (Domain Model)
*   **Агрегаты (Aggregates):** Кластеры логически связанных объектов. *(В коде реализовано базовая абстракция `Aggregate` с `self.events`)*. 
*   **События предметной области (Domain Events):** Описывают факты внутри агрегата. *(В коде реализовано наследованием от `Event`)*.

#### 2.2. Инфраструктурные абстракции доступа к данным
*   **Репозиторий (Repository Pattern):** *(В коде реализована абстракция `AbstractRepository` и конкретный `SqlAlchemyRepository` в `src/adapters/repository.py`)*.
*   **Единица работы (Unit of Work, UoW):** *(Реализовано в `src/core/unit_of_work.py` и `src/adapters/unit_of_work.py`)*.
*   **Маппинг (ORM):** Imperative mapping implemented in `src/adapters/orm.py`.

#### 2.3. Сервисный слой (Service Layer / Handlers)
*   **Обработчики (Handlers):** Асинхронные функции, принимающие Команды или События. *(В коде реализовано, например, `handle_move_entity_command` в модуле ECS)*.

#### 2.4. Шина сообщений (Message Bus)
*   **Шина `bubus`:** *(Реализовано в `src/core/messagebus.py`. Поддерживает команды, события и сбор событий из UoW)*.
*   **Мидлвары (Middlewares):** *(В коде логирование `Loguru` и трассировка `OpenTelemetry` вшиты напрямую в обертки обработчиков внутри `MessageBus`, а не через мидлвары bubus. Prometheus вынесен в адаптер TaskIQ)*.

#### 2.5. Модель Чтения (CQRS Read Model)
*   *Спецификация:* Запросы обращаются к оптимизированным представлениям.
*   *(Примечание: CQRS Read Model в коде пока полностью не реализована)*.

---

### 3. Композитный корень (Bootstrap & Dependency Injection)
*   **Сценарий начальной загрузки:** Используется фреймворк **Dishka** и класс `System`. Поддерживается динамическое обнаружение модулей через манифесты `app.toml` (`src/core/discovery.py`). Провайдеры и обработчики регистрируются автоматически в композитном корне.

---

### 4. Паттерны отказоустойчивости и распределенной работы
*   *(Примечание: Реализована базовая поддержка распределенных задач через `TaskIQ` и `NATSBroker`. Сложные паттерны Saga, Circuit Breaker в ядре пока явно не реализованы, хотя инфраструктура позволяет их добавить)*.

---

### 5. Стратегия тестирования (Testing Pyramid)
*   *(В коде реализовано: Базовая пирамида тестирования, включая in-memory хранилища `FakeRepository`, `FakeUnitOfWork` в неймспейсе тестов и покрытие бизнес-логики в директории `tests/`).*
