# Vector DB Core (`vector_db.py`)

Этот файл содержит основные классы для создания и использования индексов векторного поиска в памяти с помощью библиотеки `Annoy`. Он позволяет регистрировать различные конфигурации векторизации и выполнять поиск ближайших соседей.

## Зависимости

*   `annoy`: Библиотека для Approximate Nearest Neighbors (`pip install annoy`).
*   `loguru`: Для логирования (`pip install loguru`).
*   `tqdm`: Для отображения прогресс-баров (`pip install tqdm`).
*   Компоненты SLM: `Allocator`, `BatchBuilder`.

## Классы данных

*   **`ResultItem`**: Простой класс для хранения одного результата поиска.
    *   `data_item`: Исходный элемент данных, найденный в результате поиска.
    *   `distance`: Расстояние от элемента запроса до `data_item`.
*   **`ResultGroup`**: Класс для хранения группы результатов поиска для одного запроса.
    *   `data_item`: Элемент данных, для которого выполнялся поиск (если применимо, например, при поиске дубликатов).
    *   `results`: Список (`list`) объектов `ResultItem`.

## Классы управления и конфигурации

*   **`VectorDB`**: Статический класс, действующий как реестр для конфигураций векторных индексов.
    *   `table_initializers` (dict): Словарь для хранения функций-инициализаторов и параметров для различных типов индексов. Ключ - имя индекса. Значение - кортеж `(vector_function, metric_name, vector_size)`.
    *   `tables` (dict): Словарь для хранения созданных экземпляров `VectorDBPreferences`.
    *   `get_path()`: Статический метод, возвращающий путь для хранения файлов векторной БД (использует `Allocator.config.mongoConfig.path`).
    *   `register_pref(name, vector_size, vector_function, metric_name)`: Статический метод для регистрации новой конфигурации индекса.
        *   `metric_name`: Метрика расстояния, поддерживаемая Annoy ("angular", "euclidean", "manhattan", "hamming", "dot").
    *   `get_pref(name)`: Статический метод для получения (и создания при необходимости) экземпляра `VectorDBPreferences` по имени.

*   **`VectorDBPreferences`**: Класс для хранения конфигурации конкретного векторного индекса.
    *   `name` (str): Имя индекса.
    *   `vector_function` (function): Функция, которая принимает элемент данных и возвращает его векторное представление (эмбеддинг).
    *   `metric_name` (str): Метрика расстояния Annoy.
    *   `vector_size` (int): Размерность векторов.

## Классы поиска

*   **`SearchScope`** (ABC - Abstract Base Class): Базовый класс для создания и поиска по индексу Annoy.
    *   **`__init__(self, db_table: VectorDBPreferences)`**: Конструктор.
        1.  Инициализирует `AnnoyIndex` с размером вектора и метрикой из `db_table`.
        2.  Вызывает `get_items_to_vectorization()` (должен быть реализован в подклассах) для получения списка элементов для индексации.
        3.  Использует `BatchBuilder` для обработки элементов пачками.
        4.  Для каждого элемента вызывает `vector_function` для получения вектора.
        5.  Обрабатывает ошибки векторизации.
        6.  Сохраняет элементы (`items_set`) и их векторы/индексы Annoy (`index_dict`).
        7.  Строит индекс Annoy (`self.index.build(20)`).
    *   **`get_items_to_vectorization(self)`**: Абстрактный метод, должен возвращать итерируемый объект с элементами для индексации.
    *   **`search(self, search_term, limit=10, distance_threshold=0) -> ResultGroup`**: Выполняет поиск. Сначала получает вектор для `search_term` с помощью `vector_function`, затем вызывает `search_by_vector`.
    *   **`search_by_vector(self, search_vector, limit=10, distance_threshold=0, search_term_index=None) -> ResultGroup`**: Выполняет поиск в индексе Annoy по заданному вектору `search_vector`, фильтрует по `distance_threshold` и возвращает результаты в виде `ResultGroup`. Исключает сам элемент запроса из результатов, если он был найден.
    *   **`find_dubs(self, limit: int = 10, distance_threshold=0) -> list[ResultGroup]`**: Ищет потенциальные дубликаты (или близкие элементы) для каждого элемента в индексе, вызывая `search` для каждого элемента. Возвращает список `ResultGroup`. Использует `tqdm` для прогресса. *Примечание: Содержит закомментированный код для `ThreadPoolExecutor`, указывающий на возможность распараллеливания.*

*   **`SearchScopeList(SearchScope)`**: Конкретная реализация `SearchScope`, которая принимает список элементов (`items_list`) непосредственно в конструкторе и использует его в `get_items_to_vectorization`.

## Пример использования

```python
from Python.SLM.vector_db.vector_db import VectorDB, SearchScopeList
import numpy as np

# 1. Определить функцию векторизации (пример)
def simple_vectorizer(item_id):
    # Простая функция для примера: вектор - это ID и его квадрат
    if isinstance(item_id, int):
        vec = np.array([item_id, item_id**2], dtype='float32')
        # print(f"Vectorizing {item_id}: {vec}")
        return vec
    return None # Важно обрабатывать случаи, когда векторизация невозможна

# 2. Зарегистрировать конфигурацию
vector_size = 2
metric = 'euclidean' # или 'angular', etc.
db_name = 'my_simple_db'
VectorDB.register_pref(db_name, vector_size, simple_vectorizer, metric)

# 3. Подготовить данные
items_to_index = list(range(10)) + [5] # Добавим дубликат 5

# 4. Создать SearchScope (используя SearchScopeList)
db_prefs = VectorDB.get_pref(db_name)
search_engine = SearchScopeList(db_prefs, items_to_index)
print(f"Index built for {len(search_engine.items_set)} unique items.")

# 5. Выполнить поиск
search_item = 6
results = search_engine.search(search_item, limit=3)

print(f"\nSearching for items similar to: {search_item}")
if results.data_item: # Если сам элемент был в индексе
     print(f"(Query item found in index: {results.data_item})")
for item in results.results:
    print(f" - Found: {item.data_item}, Distance: {item.distance:.4f}")

# 6. Найти дубликаты/близкие элементы
print("\nFinding duplicates/near items (distance_threshold=0.1):")
duplicate_groups = search_engine.find_dubs(limit=5, distance_threshold=0.1)
for group in duplicate_groups:
    print(f"Item {group.data_item} is similar to:")
    for item in group.results:
         print(f" - Found: {item.data_item}, Distance: {item.distance:.4f}")
