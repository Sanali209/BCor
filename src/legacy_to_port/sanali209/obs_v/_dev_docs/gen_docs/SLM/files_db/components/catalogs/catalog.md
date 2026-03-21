# Hierarchical Catalog Record (`catalog.py`)

Этот модуль определяет класс `CatalogRecord`, который реализует **иерархическую систему каталогов**, хранящуюся в MongoDB. Эта система очень похожа по своей структуре и реализации на систему тегов (`TagRecord`), но использует другие имена полей и отдельную коллекцию (`"catalogs_records"`). Каталоги используются для организации записей `FileRecord`.

## Зависимости

*   `os`
*   `pymongo.UpdateOne`
*   `SLM.appGlue.DesignPaterns.allocator`
*   `SLM.files_db.components.File_record_wraper.FileRecord`
*   `SLM.mongoext.MongoClientEXT_f.MongoClientExt`, `SLM.mongoext.MongoClientEXT_f.DBInitializer` (используются в `init`)
*   `SLM.mongoext.wraper.MongoRecordWrapper`, `SLM.mongoext.wraper.FieldPropInfo`

## Класс `CatalogRecord`

Наследуется от `MongoRecordWrapper`.

### Назначение

*   Моделирование иерархической структуры каталогов (возможно, для представления структуры папок или предопределенных категорий).
*   Управление созданием, поиском, переименованием и удалением каталогов.
*   Связывание каталогов с записями `FileRecord`.

### Сходство с `TagRecord`

Реализация `CatalogRecord` **почти идентична** `TagRecord`. Основные отличия заключаются в именах полей (`parentCatalog` вместо `parent_tag`, поле `catalogs` в `FileRecord` вместо `tags`) и отсутствии полей `autotag` и `remap_to_tags`.

### Атрибуты и Поля (`FieldPropInfo`)

*   **`name: str`**: Короткое имя каталога (последний компонент `fullName`).
*   **`fullName: str`**: Полное, уникальное имя каталога, отражающее его положение в иерархии (компоненты разделяются `/` или `\`). **Используется как основной идентификатор при связывании с файлами.**
*   **`parentCatalog: ObjectId`**: Ссылка (`_id`) на документ родительского каталога в MongoDB. Для корневых каталогов `None`.

### Иерархия и Связи

*   **Иерархия:** Реализована через поле `parentCatalog` и структуру `fullName`. Родитель определяется и при необходимости создается рекурсивно при вызове `get_or_create`.
*   **Связь с `FileRecord`:** Отношение многие-ко-многим. В документе `FileRecord` есть поле `catalogs` (список строк), которое хранит `fullName` всех каталогов, к которым относится файл.

### Ключевые Методы

Функциональность методов аналогична `TagRecord`, но адаптирована под имена полей `CatalogRecord`:

*   **Создание и Поиск:** `get_or_create`, `create_record_data`, `get_record_by_name`, `get_all_catalogs`.
*   **Навигация:** `parentCatalog` (property), `child_catalogs` (не реализован, но подразумевается аналог `child_tags`), `get_catalogs_of_file`.
*   **Модификация:** `add_to_file_rec`, `remove_from_file_rec`, `delete` (рекурсивное удаление с обновлением ссылок в `FileRecord`), `rename` (рекурсивное переименование с обновлением ссылок в `FileRecord`).

## Инициализация (`init` function)

*   Функция `init(config)` добавляется в инициализаторы `allocator.Allocator`.
*   При запуске приложения эта функция:
    *   Получает экземпляр `MongoClientExt`.
    *   Регистрирует коллекцию `"catalogs_records"` для использования с классом-оберткой `CatalogRecord`.
    *   Создает индекс в MongoDB по полю `fullName` для ускорения поиска.

## Использование

`CatalogRecord` предоставляет способ организации файлов в иерархическую структуру, отличную от тегов. Взаимодействие с каталогами (создание, поиск, привязка к файлам) осуществляется через методы класса `CatalogRecord`.
