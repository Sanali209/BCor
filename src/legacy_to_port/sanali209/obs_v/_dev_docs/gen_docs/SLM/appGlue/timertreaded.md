# Threaded Timer System (`timertreaded.py`)

Этот модуль реализует систему для управления таймерами, которые выполняют проверку и срабатывают в отдельном фоновом потоке. Это позволяет выполнять периодические действия или действия с задержкой, не блокируя основной поток приложения.

## Зависимости

*   `threading`: Для создания и управления фоновым потоком.
*   `time`: Для работы со временем (паузы, получение текущего времени).
*   `SLM.appGlue.core.Service`, `SLM.appGlue.core.Allocator`: Для интеграции `TimerManager` в систему сервисов `appGlue`.
*   `loguru`: Для логирования ошибок и предупреждений (`pip install loguru`).

## Класс `TimerManager`

*   **Наследование:** `SLM.appGlue.core.Service`
*   **Назначение:** Сервис, который запускает и управляет фоновым потоком, периодически проверяющим все активные таймеры (`Timer`).
*   **Атрибуты:**
    *   `timers` (list): Список всех зарегистрированных экземпляров `Timer`.
    *   `timer_thread` (threading.Thread): Фоновый поток, выполняющий метод `run`.
    *   `_stop_event` (threading.Event): Событие для сигнализации потоку о необходимости завершения.
    *   `sleep_time` (float): Время в секундах, на которое поток засыпает между проверками таймеров (по умолчанию 0.2).
    *   `verbose` (bool): Флаг для вывода сообщений об ошибках в наблюдателях в консоль (по умолчанию `False`).
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует атрибуты и создает, но не запускает, фоновый поток.
    *   **`init(self, config)`:** Метод жизненного цикла сервиса. Запускает фоновый поток `timer_thread`.
    *   **`run(self)`:** Основной цикл фонового потока. Пока не установлено `_stop_event`:
        1.  Итерирует по всем `timers`.
        2.  Вызывает метод `check()` у каждого таймера.
        3.  Засыпает на `sleep_time`.
    *   **`stop(self)`:** Устанавливает `_stop_event`, сигнализируя потоку о необходимости завершения.
    *   **`_finalize(self)`:** Внутренний метод, вызываемый при завершении потока (или принудительно). Устанавливает `_stop_event`, ожидает завершения потока (`join`), вызывает `destroy()` у всех таймеров и очищает список `timers`.

## Класс `Timer`

*   **Назначение:** Представляет отдельный таймер с заданным интервалом срабатывания. Автоматически регистрируется в `TimerManager` при создании.
*   **Атрибуты:**
    *   `elapsed_time` (float): Общее время, прошедшее с момента последнего сброса или старта таймера.
    *   `last_time` (float): Метка времени (`time.time()`) последней проверки.
    *   `running` (bool): Флаг, указывающий, запущен ли таймер.
    *   `observers` (list): Список зарегистрированных объектов-наблюдателей (`TObserver`).
    *   `event_time` (float): Интервал в секундах, по истечении которого таймер должен сработать (вызвать `on_timer_notify`).
    *   `single` (bool): Если `True`, таймер остановится после первого срабатывания. Если `False` (по умолчанию), он будет сбрасываться и срабатывать повторно через каждый `event_time`.
    *   `name` (str): Имя таймера для идентификации (по умолчанию "Timer").
    *   `owner` (any): Необязательная ссылка на владельца таймера (не используется в текущей логике).
*   **Методы:**
    *   **`__init__(self, interval)`:** Инициализирует таймер с заданным `interval` (устанавливается как `event_time`) и регистрирует его в `TimerManager.instance().timers`.
    *   **`start(self)`:** Запускает таймер (устанавливает `running = True`) и сбрасывает время.
    *   **`destroy(self)`:** Удаляет таймер из `TimerManager`. Должен вызываться, когда таймер больше не нужен, чтобы избежать утечек памяти и лишних проверок.
    *   **`register(self, observer: TObserver)`:** Добавляет наблюдателя в список `observers`.
    *   **`check(self)`:** Вызывается `TimerManager`'ом. Если таймер запущен (`running`):
        1.  Вычисляет время, прошедшее с последней проверки (`last_from_prev`).
        2.  Обновляет `elapsed_time`.
        3.  Обновляет `last_time`.
        4.  Вызывает `observer.on_timer_event(self, self.elapsed_time, last_from_prev)` у всех наблюдателей.
        5.  Проверяет, достигло ли `elapsed_time` значения `event_time`.
        6.  Если достигло:
            *   Вызывает `observer.on_timer_notify(self)` у всех наблюдателей.
            *   Если `single` равно `True`, останавливает таймер (`self.stop()`).
            *   Сбрасывает таймер (`self.reset()`).
    *   **`stop(self)`:** Останавливает таймер (устанавливает `running = False`).
    *   **`reset(self)`:** Сбрасывает `elapsed_time` в 0.

## Класс `TObserver`

*   **Назначение:** Базовый класс (интерфейс) для объектов, которые хотят получать уведомления от `Timer`.
*   **Методы (предназначены для переопределения):**
    *   **`on_timer_event(self, timer: Timer, elapsed_time: float, last_from_prev: float)`:** Вызывается при каждой проверке таймера методом `Timer.check()`. Позволяет отслеживать прошедшее время непрерывно.
    *   **`on_timer_notify(self, timer: Timer)`:** Вызывается, когда `elapsed_time` таймера достигает `event_time`. Сигнализирует о срабатывании таймера по интервалу.
    *   *Примечание: В коде есть TODO о рефакторинге на использование `callable` вместо наследования, что может упростить использование.*

## Класс `TimerBuilder`

*   **Назначение:** Предоставляет текучий интерфейс (fluent interface) для удобного создания и настройки экземпляров `Timer`.
*   **Методы:**
    *   **`__init__(self)`:** Создает внутренний экземпляр `Timer` и `TObserver`.
    *   **`set_interval(self, interval)`:** Устанавливает интервал срабатывания (`event_time`).
    *   **`set_single(self, single)`:** Устанавливает режим `single`.
    *   **`set_name(self, name)`:** Устанавливает имя таймера.
    *   **`set_on_timer_notyfy(self, on_timer_notify)`:** Позволяет напрямую установить функцию, которая будет вызываться при срабатывании таймера (переопределяет `on_timer_notify` у внутреннего `TObserver`).
    *   **`build(self)`:** Завершает настройку: регистрирует внутренний `TObserver` у `Timer`, запускает таймер (`start()`) и возвращает готовый экземпляр `Timer`.

## Пример использования

```python
from SLM.appGlue.core import Allocator
from SLM.appGlue.timertreaded import TimerManager, Timer, TObserver, TimerBuilder
import time

# 1. Убедитесь, что TimerManager зарегистрирован как сервис
# (Это должно быть сделано при инициализации приложения/модуля)
# allocator = Allocator() # Пример
# if not allocator.res.has_service(TimerManager):
#     timer_manager = TimerManager()
#     allocator.res.register(timer_manager)
#     # Обычно init вызывается через allocator.init_modules() или init_services()
#     timer_manager.init(allocator.config) 

# 2. Создание наблюдателя
class MyObserver(TObserver):
    def on_timer_event(self, timer, elapsed_time, last_from_prev):
        # Вызывается каждые ~0.2 секунды (TimerManager.sleep_time)
        # print(f"Timer '{timer.name}': Event - Elapsed: {elapsed_time:.2f}s")
        pass # Обычно здесь ничего не делают, если нужен только интервал

    def on_timer_notify(self, timer):
        # Вызывается каждые 5 секунд (интервал таймера)
        print(f"!!! Timer '{timer.name}': Notify !!!")

# 3. Создание и запуск таймера
observer = MyObserver()
timer1 = Timer(interval=5) # Таймер на 5 секунд
timer1.name = "Repeating Timer"
timer1.register(observer)
timer1.start()

# 4. Использование TimerBuilder для одноразового таймера
def single_shot_action(timer):
    print(f"--- Timer '{timer.name}': Single Shot Action Executed! ---")

timer2 = TimerBuilder() \
    .set_interval(3) \
    .set_single(True) \
    .set_name("Single Shot Timer") \
    .set_on_timer_notyfy(single_shot_action) \
    .build()

print("Timers started. Waiting...")

# Имитация работы приложения
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping application...")
    # При завершении приложения нужно остановить TimerManager
    timer_manager_instance = Allocator.get_instance(TimerManager)
    timer_manager_instance.stop() 
    print("Timer manager stopped.")

```

Эта система позволяет легко добавлять фоновые периодические задачи или задачи с отложенным выполнением в приложение.
