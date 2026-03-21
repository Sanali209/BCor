# Hashing Service (`hashingService.py`)

Этот модуль предоставляет сервис `HashingService` для кэширования результатов выполнения функций на диске с использованием библиотеки `diskcache`. Он позволяет автоматически кэшировать результаты, используя хэш аргументов функции в качестве ключа, и поддерживает отдельные "таблицы" кэша для разных целей, а также пользовательские функции генерации ключей.

## Зависимости

*   `hashlib`: Для генерации хэшей (SHA256 по умолчанию).
*   `functools`: Для использования `wraps` в декораторе.
*   `os`: Для работы с путями и создания директорий.
*   `diskcache` (as `dc`): Основная библиотека для кэширования на диске (`pip install diskcache`).

## Класс `HashStore`

*   **Назначение:** Вспомогательный класс для управления экземплярами `diskcache.Index`.
*   **Статический метод `get_cache(base_directory, name)`:**
    *   Возвращает или создает экземпляр `diskcache.Index` для указанного имени таблицы (`name`) внутри базовой директории (`base_directory`).
    *   Каждая таблица кэша хранится в своей поддиректории.

## Класс `HashingService`

*   **Назначение:** Предоставляет статические методы и декоратор для управления кэшированием.
*   **Атрибуты класса:**
    *   `base_directory` (str): Корневая директория для хранения всех таблиц кэша (по умолчанию "hash_store").
    *   `custom_hash_functions` (dict): Словарь для регистрации пользовательских функций генерации ключей кэша для конкретных таблиц (ключ - имя таблицы, значение - функция).
*   **Статические методы:**
    *   **`initialize(base_directory="hash_store")`:**
        *   Устанавливает базовую директорию (`HashingService.base_directory`) для всех кэшей и создает ее, если она не существует. Должен быть вызван один раз при инициализации приложения, если используется нестандартная директория.
    *   **`register_custom_hash(table_name, hash_function)`:**
        *   Регистрирует пользовательскую функцию `hash_function` для генерации ключей кэша для таблицы `table_name`. Эта функция будет вызываться вместо `_default_generate_key` для данной таблицы.
    *   **`_default_generate_key(*args, **kwargs)`:**
        *   Функция генерации ключа по умолчанию.
        *   Создает строку из всех позиционных и именованных аргументов (именованные сортируются по ключу для консистентности).
        *   Возвращает SHA256 хэш этой строки в шестнадцатеричном формате.
    *   **`_generate_key(table_name, *args, **kwargs)`:**
        *   Выбирает и вызывает либо пользовательскую функцию генерации ключа (если она зарегистрирована для `table_name`), либо функцию по умолчанию (`_default_generate_key`).
    *   **`hashable(hashtable="default", hash_self=True)`:**
        *   **Декоратор** для кэширования результатов функции.
        *   **Параметры декоратора:**
            *   `hashtable` (str): Имя таблицы кэша, которую нужно использовать (по умолчанию "default").
            *   `hash_self` (bool): Если `True` (по умолчанию), первый аргумент функции (обычно `self` или `cls` для методов) включается в расчет ключа кэша. Если `False`, он игнорируется.
        *   **Логика работы декоратора:**
            1.  Получает экземпляр `diskcache.Index` для указанной `hashtable` с помощью `HashStore.get_cache`.
            2.  Фильтрует аргументы (`args`), исключая первый, если `hash_self` равно `False`.
            3.  Генерирует ключ кэша с помощью `_generate_key`, передавая имя таблицы и отфильтрованные аргументы.
            4.  Проверяет наличие ключа в кэше. Если найден, возвращает значение из кэша.
            5.  Если ключ не найден, вызывает оригинальную декорируемую функцию.
            6.  Сохраняет результат в кэше по сгенерированному ключу.
            7.  Возвращает результат.
    *   **`clear_cache(hashtable="default")`:**
        *   Очищает всю указанную таблицу кэша.
    *   **`get_cache_contents(hashtable="default")`:**
        *   Возвращает содержимое указанной таблицы кэша в виде словаря.

## Пример использования

```python
from SLM.appGlue.hashingService import HashingService
import time

# Инициализация (если нужно изменить директорию по умолчанию)
# HashingService.initialize(base_directory="my_app_cache")

class DataProcessor:
    def __init__(self, factor):
        self.factor = factor

    @HashingService.hashable(hashtable="processing_results", hash_self=False)
    def process_data(self, data_id, value):
        """
        Дорогостоящая операция обработки данных.
        hash_self=False означает, что self.factor не влияет на кэш.
        """
        print(f"Processing data {data_id} with value {value} (factor {self.factor})...")
        time.sleep(1) # Имитация долгой работы
        return (data_id * self.factor) + value

    @HashingService.hashable(hashtable="simple_cache") # hash_self=True по умолчанию
    def simple_calculation(self, a, b):
        print(f"Calculating {a} + {b}...")
        time.sleep(0.5)
        return a + b

# --- Использование ---
processor1 = DataProcessor(factor=10)
processor2 = DataProcessor(factor=20) # Другой экземпляр с другим factor

# Первый вызов process_data - будет выполнен и закэширован (ключ зависит только от data_id и value)
result1 = processor1.process_data(data_id=1, value=5)
print(f"Result 1: {result1}")

# Второй вызов с теми же data_id и value - результат вернется из кэша, функция не выполнится
result2 = processor1.process_data(data_id=1, value=5)
print(f"Result 2 (cached): {result2}")

# Третий вызов с теми же data_id и value, но другим экземпляром - результат вернется из кэша,
# так как hash_self=False и self.factor не учитывался
result3 = processor2.process_data(data_id=1, value=5)
print(f"Result 3 (cached, different instance): {result3}")

# Четвертый вызов с другими аргументами - будет выполнен и закэширован
result4 = processor1.process_data(data_id=2, value=10)
print(f"Result 4: {result4}")

# --- Пример с simple_calculation (hash_self=True) ---
calc_res1 = processor1.simple_calculation(a=3, b=4)
print(f"Calc Result 1: {calc_res1}")

# Этот вызов будет закэширован отдельно от processor1, т.к. self учитывается
calc_res2 = processor2.simple_calculation(a=3, b=4)
print(f"Calc Result 2 (different instance): {calc_res2}")

# Очистка кэша
# HashingService.clear_cache(hashtable="processing_results")
# print("Cache 'processing_results' cleared.")

# Посмотреть содержимое кэша
# contents = HashingService.get_cache_contents(hashtable="processing_results")
# print(f"Cache contents: {contents}")
