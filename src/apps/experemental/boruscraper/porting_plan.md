# План портирования boruscraper с использованием BCor Porting Kit

Данный план описывает шаги по модернизации `boruscraper` с использованием новых утилит `src/porting` и извлечение новых паттернов для расширения Porting Kit.

## Ожидаемые преимущества
- **Стабильность на Windows**: Устранение зависаний Playwright при закрытии приложения.
- **Унификация UI**: Стандартизация сигналов прогресса и логов.
- **Безопасность данных**: Исключение `AttributeError` при работе с базой данных.

---

## 🏗Proposed Changes (boruscraper refactoring)

### 1. Точка входа (`main.py`)
- **[MODIFY]**: Подключить `WindowsLoopManager.setup_loop()` в начале `main()`.
- **[MODIFY]**: Использовать `WindowsLoopManager.drain_loop()` в блоке `finally` или через сигнал `aboutToQuit`, чтобы гарантированно дать Playwright время на закрытие страниц и браузера.

### 2. UI Слой (`infrastructure/events_adapter.py`)
- **[MODIFY]**: Перевести `GuiEventAdapter` на наследование от `BaseGuiAdapter`.
- **[REFACTOR]**: Заменить кастомные сигналы `started/completed/error` на стандартные из базового класса.

### 3. Репозитории и Данные
- **[MODIFY]**: Обеспечить наследование `DatabaseManager` от `SqliteRepositoryBase`.
- **[FIX]**: Использовать `get_field` для доступа к полям из `sqlite3.Row`, чтобы избежать падений при отсутствии ключей.

### 4. Обработка путей
- **[NEW]**: Применить `@PathNormalizer.normalize_args` к методам создания проектов и загрузки файлов в Scraping-движке.

---

## 🛠 Экстракция паттернов в Porting Kit

В ходе работы с `boruscraper` мы можем извлечь следующие универсальные компоненты в `src/porting/`:

### 1. `PlaywrightManager` (`src/porting/playwright_utils.py`)
Паттерн для безопасного управления жизненным циклом браузера.
- Автоматическое закрытие ресурсов при получении сигнала завершения.
- Обработка специфичных для Windows ошибок "Event loop is closed" при очистке Playwright.

### 2. `UiLogBridge` (`src/porting/ui_bridge.py`)
Интеграция `loguru` с Qt сигналами.
- Позволяет легко перенаправлять системные логи в GUI виджет (текстовое поле "Консоль") без прямой зависимости Core-логики от UI.

### 3. `TaskThrottler` (`src/porting/async_utils.py`)
Утилита на базе `asyncio.Semaphore`.
- Стандартный способ ограничения конкурентности для сетевых операций и парсинга, инжектируемый через Dishka.

---

## 🧪 План верификации
1. **Unit-тесты**: Написание тестов для новых компонентов `src/porting`.
2. **E2E Test**: Создание `tests/apps/experemental/boruscraper/test_boruscraper_e2e.py` с использованием `BCorTestSystem`.
3. **Stress-test**: Проверка корректности закрытия множества вкладок Playwright при экстренном выходе из приложения.
