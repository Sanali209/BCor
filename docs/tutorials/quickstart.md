# Tutorial: Быстрый старт в BCor

Создадим работающий модуль с командой, обработчиком и событием — на примере `hello_app`.

## 1. Структура модуля

Модуль — это наследник `BaseModule`. Он живёт в отдельной папке и содержит файлы:

```
myapp/
  app.toml                  # манифест приложения
  main.py                   # точка входа
  modules/
    greeting/               # ваш модуль
      __init__.py
      module.py             # BaseModule + опциональный Dishka Provider
      domain.py             # доменная логика (Aggregate / сервис)
      messages.py           # Command и Event (наследники Message)
      handlers.py           # функции-обработчики
```

## 2. Создаём сообщения (`messages.py`)

```python
from src.core.messages import Command, Event

class SayHelloCommand(Command):
    name: str

class HelloSaidEvent(Event):
    message: str
```

`Command` — намерение изменить состояние, маршрутизируется **ровно одному** обработчику.

`Event` — факт, что что-то произошло, рассылается **всем** подписчикам.

## 3. Пишем доменную логику (`domain.py`)

```python
class Greeter:
    def __init__(self, default_name: str, style: str):
        self.default_name = default_name
        self.style = style

    def generate_greeting(self, name: str | None) -> str:
        target = name.strip() if name and name.strip() else self.default_name
        if self.style == "enthusiastic":
            return f"HELLO, {target.upper()}!!! Welcome to BCor!"
        elif self.style == "formal":
            return f"Greetings, {target}. It is a pleasure to meet you."
        else:
            return f"Hello, {target}."
```

Это чистый Python — без SQLAlchemy, без фреймворков. Вся бизнес-логика здесь.

## 4. Пишем обработчики (`handlers.py`)

```python
from src.apps.hello_app.modules.greeting.messages import HelloSaidEvent, SayHelloCommand

async def handle_say_hello(cmd: SayHelloCommand, uow):
    message = uow.greeter.generate_greeting(cmd.name)
    uow.events.append(HelloSaidEvent(message=message))
    return message

async def on_hello_said(event: HelloSaidEvent, uow):
    print(f"\n>> App Output: {event.message}\n")
```

Первый параметр — сообщение. Второй — `uow` (AbstractUnitOfWork), автоматически инжектится MessageBus'ом.

## 5. Собираем модуль (`module.py`)

```python
from dishka import Provider
from src.core.module import BaseModule
from src.apps.hello_app.modules.greeting.handlers import handle_say_hello, on_hello_said
from src.apps.hello_app.modules.greeting.messages import HelloSaidEvent, SayHelloCommand

class GreetingModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.provider = GreetingProvider()       # Dishka DI
        self.command_handlers = {
            SayHelloCommand: handle_say_hello,   # 1 команда → 1 хендлер
        }
        self.event_handlers = {
            HelloSaidEvent: [on_hello_said],     # 1 событие → N хендлеров
        }
```

Если модулю нужны зависимости — создаём `GreetingProvider` (наследник `dishka.Provider`) и вешаем на него `self.provider`.

## 6. Манифест приложения (`app.toml`)

```toml
[app]
app_name = "Hello BCor"
log_level = "DEBUG"

[modules]
paths = ["src.apps.hello_app.modules", "src.modules"]
enabled = ["greeting"]

[greeting]
default_name = "World"
greeting_style = "enthusiastic"
```

`System.from_manifest()` прочитает этот файл, обнаружит `GreetingModule` через `ModuleDiscovery`, загрузит настройки секции `[greeting]` в `GreetingSettings`.

## 7. Точка входа (`main.py`)

```python
import asyncio
from pathlib import Path
from src.core.system import System

async def main():
    manifest = Path(__file__).parent / "app.toml"
    system = System.from_manifest(str(manifest))
    await system.start()

    async with system.container() as request_container:
        from src.core.messagebus import MessageBus
        bus = await request_container.get(MessageBus)

        result = await bus.dispatch(SayHelloCommand(name="BCor"))
        print(f"Result: {result}")

    await system.stop()

asyncio.run(main())
```

**Что здесь происходит:**

1. `System.from_manifest()` — Composition Root: создаёт Dishka-контейнер, регистрирует модули.
2. `system.start()` — запускает `@on_start` хуки и `module.startup()`.
3. `bus.dispatch(command)` — отправляет команду в `MessageBus`. Bus находит зарегистрированный хендлер, исполняет его, собирает новые события и публикует их.
4. `system.stop()` — корректно завершает все процессы.

## 8. Запуск

```bash
cd BCor
python src/apps/hello_app/main.py
```

В консоли появится приглашение ввода имени. BCor скомпонует приложение, выполнит `SayHelloCommand`, сгенерирует приветствие и опубликует `HelloSaidEvent`.

---

**Итог:** вы создали сообщения, доменную логику, обработчики, модуль, манифест и точку входа. Весь жизненный цикл — от команды до события — управляется `MessageBus` и `System`.
