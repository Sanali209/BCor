# Chains Module (`chains_main.py`)

Этот модуль предоставляет классы для создания и выполнения последовательных цепочек операций обработки данных, в основном работающих со словарями. Каждое звено цепочки (`ChainFunction`) выполняет свою операцию и передает результат (словарь) следующему звену.

## Базовый класс `ChainFunction`

*   **Назначение:** Основа для всех звеньев цепочки. Управляет связыванием звеньев и последовательным выполнением операций.
*   **Атрибуты:**
    *   `next_f: ChainFunction`: Ссылка на следующее звено в цепочке.
    *   `operation`: Функция или метод, выполняющий основную логику звена. Должен принимать `**kwargs` и возвращать словарь.
    *   `in_dict`: Словарь, передаваемый в `operation`.
    *   `pass_truth_in_dict`: (Не используется в базовом классе, но есть в наследниках) Флаг для передачи исходного словаря дальше по цепочке.
*   **Методы:**
    *   `set_last(last_f)`: Добавляет `last_f` в конец текущей цепочки.
    *   `__or__(other)`: Перегрузка оператора `|` для удобного связывания звеньев (`chain1 | chain2`).
    *   `execute_operation()`: Выполняет `self.operation` с `self.in_dict`.
    *   `run(**kwargs)`: Основной метод запуска. Инициализирует `in_dict`, выполняет `execute_operation` и, если есть `next_f`, рекурсивно вызывает `run` для следующего звена с результатом текущего.

## Реализации `ChainFunction`

### `PrintToChainFunction`
Простое звено для вывода сообщения в консоль.
*   **`operation`**: Внутренняя функция `printTest`, которая печатает значение аргумента `message` и возвращает `{'response': 'ok'}`.
*   **`run(message="", **kwargs)`**: Переопределенный метод `run`, который добавляет аргумент `message` в `kwargs` перед вызовом базового `run`.

### `DictFormatterChainFunction`
Форматирует поля входного словаря на основе правил маппинга и валидации.
*   **Атрибуты:**
    *   `mapping`: Словарь вида `{"target_key": ["source_key1", "source_key2"], ...}`. Определяет, из каких ключей (`source_key`) брать значение для целевого ключа (`target_key`). Берется первое найденное значение из списка `source_key`.
    *   `validators`: Словарь вида `{"target_key": validation_function, ...}`. Позволяет применить функцию валидации/преобразования к значению перед записью в `target_key`.
    *   `copy_source`: `bool`. Если `True`, копирует все поля из входного словаря в выходной перед форматированием.
    *   `verbose`: `bool`. (Не используется в текущей логике).
*   **`operation`**: Метод `format`, реализующий логику форматирования.

### `DictFieldMergeChainFunction`
Объединяет значения нескольких полей входного словаря в одно строковое поле.
*   **Атрибуты:**
    *   `map`: Словарь вида `{"target_key": ["source_key1", "source_key2"], ...}`. Определяет, какие поля (`source_key`) объединять для целевого ключа (`target_key`).
    *   `pass_truth_dict`: `bool`. Если `True`, копирует все поля из входного словаря в выходной перед объединением.
    *   `splitter`: `str`. Разделитель, используемый при объединении значений в строку (по умолчанию `|`).
    *   `include_source_name`: `bool`. Если `True`, при объединении добавляет имя исходного поля (`key=value`), иначе добавляет только значение (`value`).
    *   `verbose`: `bool`. (Не используется в текущей логике).
*   **`operation`**: Метод `collect`, реализующий логику объединения.

## Пример использования

```python
from Python.SLM.chains.chains_main import PrintToChainFunction, DictFormatterChainFunction, DictFieldMergeChainFunction

# Создание звеньев
formatter = DictFormatterChainFunction()
formatter.mapping = {"name": ["first_name", "user_name"], "email": ["email_address"]}
formatter.validators = {"email": lambda e: e.lower()} # Преобразовать email к нижнему регистру
formatter.copy_source = True # Копировать остальные поля

merger = DictFieldMergeChainFunction()
merger.map = {"full_info": ["name", "email", "age"]}
merger.splitter = "; "
merger.include_source_name = False # Только значения

printer = PrintToChainFunction()

# Связывание в цепочку
pipeline = formatter | merger | printer

# Входные данные
input_data = {
    "user_name": "JohnDoe", 
    "email_address": "John.Doe@Example.COM", 
    "age": 30,
    "city": "New York" 
}

# Запуск цепочки
result = pipeline.run(**input_data)

# Ожидаемый вывод в консоль (от printer):
# {'user_name': 'JohnDoe', 'email_address': 'John.Doe@Example.COM', 'age': 30, 'city': 'New York', 'name': 'JohnDoe', 'email': 'john.doe@example.com', 'full_info': 'JohnDoe; john.doe@example.com; 30', 'response': 'ok'}

print(f"Final result: {result}") 
# Final result: {'response': 'ok'} 
```

## Связанные концепции

*   [Core Concepts](../core_concepts.md)
*   [Architecture](../architecture.md)
*   [Actions Module](../actions/index.md) (Операции внутри звеньев цепочки могут вызывать действия)
