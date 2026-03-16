# Первые шаги (First Steps)

Добро пожаловать в репозиторий! Это руководство создано, чтобы помочь вам начать работу с нашим архитектурным фреймворком (Модульный Монолит + Event-Driven Architecture) с использованием `uv`, `bubus`, `dishka` и `TaskIQ`.

## 1. Установка окружения (Инструмент `uv`)
Мы используем сверхбыстрый менеджер зависимостей `uv` (написан на Rust), который заменяет `pip`, `poetry` и `virtualenv`.

1.  Установите `uv` (если еще не установлен):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  Клонируйте репозиторий и перейдите в папку проекта.
3.  Инициализируйте окружение и установите зависимости:
    ```bash
    uv sync
    ```
4.  Вы можете запускать скрипты внутри изолированного окружения с помощью `uv run`:
    ```bash
    uv run python main.py
    ```

## 2. Запуск тестов (TDD)
Архитектура спроектирована так, чтобы вся бизнес-логика тестировалась сверхбыстро (за миллисекунды) без базы данных. Это достигается за счет использования `FakeRepository` и `FakeUnitOfWork` (см. `tests/conftest.py`).

Запуск всех модульных тестов:
```bash
PYTHONPATH=. uv run pytest tests/unit/
```

## 3. Как создать новый бизнес-модуль
Модуль инкапсулирует свою бизнес-логику (DDD) и не зависит от других модулей. Взаимодействие происходит только через отправку Событий в Шину (`MessageBus`).

### Шаг 1: Определите настройки (pydantic-settings)
Каждый модуль должен декларативно описывать свои настройки. Ядро само подтянет их из `.env` файла или окружения.

```python
# src/modules/billing/domain.py
from pydantic_settings import BaseSettings

class BillingSettings(BaseSettings):
    payment_gateway_url: str
    retry_attempts: int = 3
```

### Шаг 2: Определите Команды и События (bubus.BaseEvent)
Сообщения выступают контрактом (DTO) для модуля.

```python
from src.core.messages import Command, Event

class ProcessPaymentCommand(Command):
    order_id: str
    amount: float

class PaymentSucceededEvent(Event):
    order_id: str
```

### Шаг 3: Напишите Обработчики (Handlers)
Обработчики получают DTO-сообщение и доступ к `UnitOfWork` (для работы с базой) через Dependency Injection (Dishka).
Они должны возвращать Result Monad (`BusinessResult`), чтобы избегать неявных исключений.

```python
from src.core.monads import BusinessResult, success, failure
from src.core.unit_of_work import AbstractUnitOfWork

async def handle_process_payment(cmd: ProcessPaymentCommand, uow: AbstractUnitOfWork) -> BusinessResult:
    # 1. Открыть транзакцию (with uow:)
    # 2. Получить Агрегат из репозитория (uow.repo.get(cmd.order_id))
    # 3. Выполнить бизнес-логику
    # 4. Добавить событие (agg.add_event(PaymentSucceededEvent(order_id=cmd.order_id)))
    # 5. Сохранить изменения (uow.commit())

    return success({"status": "paid"})
```

### Шаг 4: Соберите класс модуля (BaseModule)
Модуль регистрирует свои обработчики и настройки в базовом классе.

```python
from src.core.module import BaseModule

class BillingModule(BaseModule):
    settings_class = BillingSettings

    # Маршрутизация (CQRS)
    command_handlers = {
        ProcessPaymentCommand: handle_process_payment
    }
    event_handlers = {}
```

### Шаг 5: Подключите модуль к Системе (Composition Root)
В вашей главной точке входа (например, `main.py` или `FastAPI startup`):

```python
from src.core.system import System
from src.modules.billing.domain import BillingModule

# Система сама соберет все настройки, маршруты и DI-провайдеры
system = System(modules=[BillingModule()])

# Теперь вы можете получить MessageBus из контейнера и отправить команду:
# async with system.container() as container:
#     bus = await container.get(MessageBus)
#     await bus.dispatch(ProcessPaymentCommand(...))
```

## 4. Как отправлять тяжелые фоновые задачи (TaskIQ + NATS)
Если ваш обработчик (например, генерация PDF-отчета) занимает слишком много времени и заблокирует UI или API-шлюз, делегируйте эту работу внешнему воркеру.

1.  Определите задачу, используя брокер из адаптеров (`src/adapters/taskiq_broker.py`):
    ```python
    from src.adapters.taskiq_broker import broker

    @broker.task
    async def build_heavy_report_task(user_id: str):
        # Эта функция будет выполнена в отдельном процессе NATS-воркера
        pass
    ```
2.  Внутри вашего обработчика (из Шага 3) вызовите метод `.kiq()`:
    ```python
    async def handle_generate_report(cmd: GenerateReportCommand, uow: AbstractUnitOfWork):
        # Асинхронно отправляет задачу в NATS и мгновенно возвращает управление
        await build_heavy_report_task.kiq(cmd.user_id)
        return success({"status": "processing"})
    ```
3.  Запустите фоновый воркер в отдельном окне терминала:
    ```bash
    uv run taskiq worker src.adapters.taskiq_broker:broker
    ```

## 5. Наблюдаемость (Observability)
Для отладки мы используем:
*   **Loguru:** Вместо стандартного `logging`. Ядро автоматически логгирует в него все успешные обработки и изолированные сбои событий.
*   **OpenTelemetry:** Каждое событие и команда, проходящие через `MessageBus`, оборачиваются в Span-трассировку, чтобы вы могли видеть цепочку вызовов в Grafana/Jaeger.
*   **Метрики:** Фоновые воркеры `TaskIQ` отдают Prometheus-метрики на порту 9000.
