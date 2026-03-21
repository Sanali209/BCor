# Компонент: Каталоги (`catalog.py`)

Этот компонент отвечает за управление иерархическими каталогами или коллекциями, к которым могут принадлежать файлы. Основным классом является `CatalogRecord`.

## `CatalogRecord(MongoRecordWrapper)`

*   **Назначение**: Представляет каталог в базе данных MongoDB. Структура и функциональность очень похожи на [`TagRecord`](../../core_concepts.md#tag-record-fs_tagpytagrecord).
*   **Коллекция MongoDB**: `catalogs_records` (регистрируется функцией `init`).
*   **Наследование**: Наследуется от `SLM.mongoext.wraper.MongoRecordWrapper`.
*   **Ключевые поля MongoDB**:
    *   `_id`: Уникальный идентификатор.
    *   `name` (str): Базовое имя каталога (последняя часть пути).
    *   `fullName` (str): Полное иерархическое имя каталога (например, `photos/vacation/2024`). Используется как идентификатор при связывании с файлами.
    *   `parentCatalog` (ObjectId): Ссылка на `_id` родительского `CatalogRecord`. `None` для корневых каталогов.
*   **Связь с файлами**: Поле `catalogs` в `FileRecord` хранит список `fullName` каталогов, к которым принадлежит файл.
*   **Основные методы**:
    *   `get_or_create(fullName)`: Находит или создает каталог по `fullName`.
    *   `get_record_by_name(fullName)`: Находит каталог по `fullName`.
    *   `parentCatalog` (property): Возвращает родительский `CatalogRecord`.
    *   `add_to_file_rec(file)`: Добавляет `fullName` каталога в поле `catalogs` объекта `FileRecord`.
    *   `remove_from_file_rec(file)`: Удаляет `fullName` каталога из поля `catalogs` объекта `FileRecord`.
    *   `rename(new_fullName)`: Переименовывает каталог (обновляет `name`, `fullName`, `parentCatalog`), обновляет ссылки в `FileRecord.catalogs` и рекурсивно переименовывает дочерние каталоги.
    *   `delete()`: Удаляет каталог, удаляет ссылки из `FileRecord.catalogs` и рекурсивно удаляет дочерние каталоги.
    *   `get_catalogs_of_file(file)`: Возвращает список `CatalogRecord`, связанных с файлом.
    *   `get_all_catalogs()`: Возвращает список всех каталогов.

## Инициализация

Функция `init(config)` в `catalog.py` регистрирует коллекцию `catalogs_records` и создает индекс по полю `fullName`. Эта функция добавляется в список инициализаторов `allocator`.

[Назад к обзору компонентов](./index.md)
[Назад к главной странице](../../index.md)
