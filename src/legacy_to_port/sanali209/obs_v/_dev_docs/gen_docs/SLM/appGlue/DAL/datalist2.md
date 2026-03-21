# Observable Data Models and Views (`datalist2.py`)

Этот модуль предоставляет фреймворк для работы с коллекциями данных, реализуя паттерн Наблюдатель (Observer) и разделяя модель данных, логику запросов и представление/адаптер. Он позволяет создавать наблюдаемые модели данных (как в памяти, так и на основе MongoDB), выполнять запросы с фильтрацией и пагинацией, а также предоставлять "вид" (view) этих данных с возможностью преобразования и навигации.

**Примечание:** В коде есть комментарии TODO, указывающие на возможную интеграцию с моделью аннотаций и замену предыдущей версии `datalist`.

## Зависимости

*   `loguru`: Для логирования.
*   `tqdm`: Для отображения прогресс-баров при фильтрации (в `DataQuery`).
*   `SLM.appGlue.DAL.DAL.GlueDataConverter`, `ForwardConverter`: Для преобразования данных в `DataViewCursor`.
*   `SLM.appGlue.DesignPaterns.specification.Specification`, `AllSpecification`: Для фильтрации данных в `DataQuery` и `DataViewCursor`.
*   `pymongo`: Для работы с MongoDB в `MongoDataModel` и `MongoDataQuery` (`pip install pymongo`).
*   `abc.ABC`, `abstractmethod`: Для определения абстрактных базовых классов.

## Абстрактные Базовые Классы

*   **`AbstractDataModel(ABC)`**:
    *   Определяет интерфейс для наблюдаемой модели данных.
    *   **Абстрактные методы:** `attach(observer)`, `detach(observer)`, `_notify(change_type, item=None)`, `append(item)`, `remove(item)`, `clear()`.
*   **`AbstractDataQuery(ABC)`**:
    *   Определяет интерфейс для выполнения запросов к модели данных.
    *   **Абстрактные методы:** `get_by_query(skip, limit, sort)`, `obj_to_query(obj)`, `count_all()`.

## Наблюдатель

*   **`DataObserver`**:
    *   Базовый класс для наблюдателей, которые подписываются на изменения в `AbstractDataModel`.
    *   **Методы для переопределения:** `update(data_model, change_type, item=None)` (хотя в коде используется `list_update`).

## Модель Данных в Памяти

*   **`DataListModelBase(AbstractDataModel)`**:
    *   Базовая реализация `AbstractDataModel`. Управляет списком наблюдателей (`_observers`) и предоставляет базовую логику уведомлений (`_notify`).
    *   Связан с `DataQuery` по умолчанию.
*   **`DataListModel(DataListModelBase)`**:
    *   Конкретная реализация модели данных, хранящая элементы в списке `_data`.
    *   **Атрибуты:**
        *   `_data` (list): Список элементов данных.
        *   `_version` (int): Счетчик версий, увеличивается при каждом изменении данных. Используется `DataQuery` для кэширования.
    *   **Методы:** Переопределяет `append`, `extend`, `remove`, `clear` для модификации `_data` и уведомления наблюдателей. Добавляет метод `exist`.
*   **`DataQuery(AbstractDataQuery)`**:
    *   Реализация запросов для `DataListModel`.
    *   **Атрибуты:**
        *   `_data_model`: Ссылка на `DataListModel`.
        *   `_specification`: Текущий объект `Specification` для фильтрации (по умолчанию `AllSpecification`).
        *   `_filtered_data`: Кэшированный список отфильтрованных данных.
        *   `_last_version`: Последняя версия модели, для которой был построен кэш.
    *   **Методы:**
        *   `get_by_query(skip, limit, sort, sort_algs)`: Фильтрует данные из `_data_model` с использованием `_specification`, применяет сортировку (если `sort` и `sort_algs` предоставлены), применяет пагинацию (skip/limit) и возвращает результат. Использует кэширование на основе версии модели.
        *   `obj_to_query(obj)`: Устанавливает спецификацию для фильтрации.
        *   `count_all()`: Возвращает количество элементов после фильтрации.

## Модель Данных MongoDB

*   **`MongoDataModel(DataListModelBase)`**:
    *   Реализация модели данных, использующая коллекцию MongoDB в качестве хранилища.
    *   **Атрибуты:**
        *   `_client`, `_database`, `_collection`: Экземпляры `pymongo` для подключения к БД.
    *   **Методы:** Переопределяет `append`, `remove`, `clear` для выполнения соответствующих операций (`insert_one`, `delete_one`, `delete_many`) в MongoDB и уведомления наблюдателей.
*   **`MongoDataQuery(AbstractDataQuery)`**:
    *   Реализация запросов для `MongoDataModel`.
    *   **Атрибуты:**
        *   `_data_model`: Ссылка на `MongoDataModel`.
        *   `_filter` (dict): Фильтр MongoDB.
    *   **Методы:**
        *   `get_by_query(skip, limit, sort)`: Выполняет запрос `find()` к MongoDB с использованием `_filter`, сортировки и пагинации.
        *   `count_all()`: Выполняет `count_documents()` с `_filter`.
        *   `obj_to_query(obj)`: Устанавливает фильтр MongoDB (ожидает `dict`).

## Представление/Адаптер Данных

*   **`DataViewCursor(DataObserver)`**:
    *   **Назначение:** Представляет собой "вид" или "курсор" над `AbstractDataModel`. Позволяет просматривать данные постранично, применять фильтры (`Specification`), конвертировать данные и уведомлять своих собственных наблюдателей (например, элементы GUI).
    *   **Атрибуты:**
        *   `_data_model`: Ссылка на базовую модель данных.
        *   `data_converter`: Экземпляр `GlueDataConverter` для преобразования данных (по умолчанию `ForwardConverter`).
        *   `items_per_page`, `current_page`, `max_page`: Параметры пагинации.
        *   `_current_index`: Индекс текущего элемента (концепция курсора).
        *   `_specification`: Текущая спецификация фильтрации.
        *   `child_observers`: Список наблюдателей этого `DataViewCursor`.
        *   `sort`, `sort_alg`: Параметры сортировки.
        *   `_view_model`: Кэш текущей отображаемой страницы.
    *   **Методы:**
        *   `attach(observer)`: Добавляет дочернего наблюдателя.
        *   `set_specification(spec)`: Устанавливает спецификацию, передает ее в `dataQuery` модели и обновляет представление.
        *   `get_filtered_data(skip, limit, all_pages)`: Получает данные из `dataQuery` модели для текущей страницы/фильтра/сортировки и применяет `data_converter`.
        *   `all_items_count()`: Получает общее количество элементов (после фильтрации) из `dataQuery` модели.
        *   `page_next()`, `page_previous()`: Переход между страницами.
        *   `refresh()`: Принудительно обновляет представление и уведомляет дочерних наблюдателей.
        *   `list_update(data_model, change_type, item)`: Реализация `DataObserver`. Получает уведомления от базовой модели, обновляет свое состояние (например, кэш `_view_model`) и уведомляет дочерних наблюдателей, применяя конвертер к `item`.
        *   `append(item)`, `remove(item)`, `clear()`: Методы для модификации базовой модели данных через `DataViewCursor` (применяют обратное преобразование `ConvertBack`).
        *   Методы для навигации по "курсору": `get_current_item`, `move_next`, `move_previous`, `move_to_start`, `move_to_end`, `move_to_index`.

## Принцип работы

1.  Создается экземпляр модели данных (`DataListModel` или `MongoDataModel`).
2.  Создается экземпляр `DataViewCursor`, связанный с моделью данных. Опционально передается `GlueDataConverter`.
3.  К `DataViewCursor` прикрепляются наблюдатели (например, элементы GUI).
4.  Устанавливается спецификация фильтрации (`set_specification`) для `DataViewCursor`.
5.  `DataViewCursor` получает данные для текущей страницы у `DataQuery` модели, конвертирует их и уведомляет своих наблюдателей (`refresh`).
6.  При изменении базовой модели (`append`, `remove`, `clear`), она уведомляет `DataViewCursor` (`list_update`).
7.  `DataViewCursor` обновляет свое состояние (например, пересчитывает страницы, обновляет кэш `_view_model`) и уведомляет своих наблюдателей, передавая им уже конвертированные данные.
8.  Пользователь может перемещаться по страницам (`page_next`, `page_previous`), что вызывает `refresh` у `DataViewCursor`.

Этот подход позволяет отделить источник данных и логику запросов от представления, обеспечивая гибкость и возможность легкой смены источника данных или способа их отображения.
