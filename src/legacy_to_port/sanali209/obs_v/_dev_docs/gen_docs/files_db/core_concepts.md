# Основные концепции и структуры данных

Этот раздел описывает ключевые сущности, используемые в модуле `files_db`.

## Основные сущности

*   **File Record:** Представление файла в базе данных MongoDB. Подробную структуру полей см. ниже.
    *   *TODO: Детализировать структуру на основе `docs/file_record_structure.md` и анализа кода. Указать используемые поля MongoDB.*
*   **Tag Record (`fs_tag.py:TagRecord`)**: Представление тега в базе данных MongoDB.
    *   Наследуется от `SLM.mongoext.wraper.MongoRecordWrapper`.
    *   **Ключевые поля MongoDB:**
        *   `_id`: Уникальный идентификатор.
        *   `name` (str): Базовое имя тега (например, "cat").
        *   `fullName` (str): Полное иерархическое имя тега (например, "animals/mammals/cat"). Используется как основной идентификатор в связях (например, в `FileRecord.tags`).
        *   `parent_tag` (ObjectId): Ссылка на `_id` родительского `TagRecord`. `None` для корневых тегов.
        *   `autotag` (bool): Флаг, указывающий, был ли тег добавлен автоматически.
        *   `remap_to` (str, optional): Строка с `fullName` тегов (через ";"), на которые следует переназначить файлы при вызове `remap_tag()`.
        *   *(Возможно также `description`, `sinonims` - неявно)*
    *   **Основные методы:**
        *   `get_or_create(fullName)`: Находит или создает тег по `fullName`.
        *   `get_record_by_name(fullName)`: Находит тег по `fullName`.
        *   `parent_tag` (property): Возвращает родительский `TagRecord`.
        *   `child_tags()`: Возвращает список дочерних `TagRecord`.
        *   `tagged_files()`: Возвращает список `FileRecord`, отмеченных этим тегом.
        *   `add_to_file_rec(file)` / `remove_from_file_rec(file)`: Добавляет/удаляет `fullName` тега из поля `tags` объекта `FileRecord`.
        *   `rename(new_fullName)`: Переименовывает тег (обновляет `name`, `fullName`, `parent_tag`), обновляет ссылки в файлах и рекурсивно переименовывает дочерние теги.
        *   `delete()`: Удаляет тег, удаляет ссылки из файлов и рекурсивно удаляет дочерние теги.
        *   `remap_tag()`: Выполняет переназначение файлов на теги из поля `remap_to`.
        *   `get_tags_report()`: Генерирует JSON-отчет (`tags_report.json`) со статистикой использования тегов.
*   **Annotation Record (`annotation.py:AnnotationRecord`)**: Представление аннотации, связанной с файлом.
    *   Наследуется от `MongoRecordWrapper`.
    *   **Ключевые поля MongoDB:**
        *   `_id`: Уникальный идентификатор.
        *   `value` (Any): Значение аннотации (метка, координаты и т.д.). `None`, если еще не аннотировано.
        *   `parent_id` (ObjectId): Ссылка на `_id` родительского `AnnotationJob`.
        *   `file_id` (ObjectId): Ссылка на `_id` связанного `FileRecord`.
        *   *(Возможно также `AI`, `AI_wrong_annotation`, `description`, `score`, `created`, `updated`, `object_detection_region` из `docs/Annotation/Annotation.rst` - TODO: проверить использование в коде)*
    *   **Свойства:** `parent` (возвращает `AnnotationJob`), `file` (возвращает `FileRecord`).
*   **Annotation Job (`annotation.py:AnnotationJob`)**: Описание задачи аннотирования.
    *   Наследуется от `MongoRecordWrapper`.
    *   **Ключевые поля MongoDB:**
        *   `_id`: Уникальный идентификатор.
        *   `name` (str): Имя задачи.
        *   `type` (str): Тип задачи (например, "multiclass/image", "image_object_detection"). См. `all_jobTypes` в `annotation.py`.
        *   `choices` (list): Список допустимых меток/классов для задачи.
        *   `not_annotated` (list): *Похоже, не используется активно.*
    *   **Основные методы:** Управляет жизненным циклом `AnnotationRecord` для задачи, включая создание, поиск, обновление, удаление, экспорт, управление метками. Использует `DataViewCursor` для навигации.
*   **Detection, Recognized Object, Detection Object Class**: Сущности для хранения результатов [распознавания объектов](./object_recognition.md).
*   **Relation Record**: Сущность для хранения [связей](./components/relations.md) между записями.

## Определение типа файла и индексаторы (`CollectionRecordScheme.py`)

Модуль использует систему схем для определения типа файла и связанных с ним операций, в первую очередь индексации:

*   **`FileTypeRouter`**: Сервис, который определяет соответствующую схему (`FileScheme`) для файла на основе его расширения (`get_type_by_path`) или имени типа (`get_type_by_name`).
*   **`FileScheme`**: Базовый класс для схем файлов. Определяет имя типа (`name`), шаблоны расширений (`mach_patterns`), тип контента (`content`) и содержит словарь `attachments`, где могут храниться связанные объекты, например, конвейер индексаторов (`base_indexer`).
*   **`ImageJPG`, `ImagePNG`**: Конкретные реализации `FileScheme` для JPG и PNG файлов. Они инициализируют конвейер `ItemIndexer` с набором индексаторов изображений (например, `Image_MetadataRead`, `FaceDetector`, `DeepDunBoru`), некоторые из которых могут быть отключены по умолчанию.

*Примечание: Этот файл не определяет структуру записи в MongoDB, а скорее логику обработки файлов в зависимости от их типа.*

## Ключевые классы-обертки

*   **`FileRecord` (`File_record_wraper.py`)**: Основной класс-обертка для работы с записями файлов в MongoDB.
    *   Наследуется от `CollectionRecord` (и, вероятно, `MongoRecordWrapper`).
    *   Предоставляет методы для поиска (`get_record_by_path`, `find_one`, `find`), создания (`create_record_data`, `add_file_records_from_folder`), удаления (`delete`, `remove_files_record_by_mach_pattern`) и модификации записей файлов.
    *   Управляет связью между записью в БД и файлом на диске (свойство `full_path`, методы `move_to_folder`, `delete`).
    *   Взаимодействует с другими компонентами, такими как `FileTypeRouter` (для определения типа файла при создании), `ImageDataCacheManager` (для получения MD5 содержимого), `ImageThumbCache` (для работы с превью), `ImageToLabel` (для получения данных от ИИ через `get_ai_expertise`).
    *   Поле `ai_expertise` (вероятно, список словарей) используется для хранения результатов работы различных ИИ-моделей, примененных к файлу.

## Структура записей в MongoDB

Ниже приведено описание полей для основных коллекций, основанное на анализе кода (`FieldPropInfo` и методов). Поля, не подтвержденные в коде, но упомянутые в старой документации, помечены как "не подтверждено".

### File Record (Коллекция `collection_records`, `item_type='FileRecord'`)

*   `_id` (ObjectId): Уникальный идентификатор.
*   `item_type` (str): `'FileRecord'`.
*   `name` (str): Имя файла (из `FieldPropInfo`).
*   `local_path` (str): Локальный путь к папке с файлом (из `FieldPropInfo`).
*   `extension` (str): Расширение файла (из `create_record_data`).
*   `size` (int): Размер файла в байтах (из `create_record_data`).
*   `file_type` (str): Тип файла, определенный `FileTypeRouter` (например, "image/jpeg") (из `create_record_data`).
*   `file_content_md5` (str): MD5 хэш содержимого файла (из `create_record_data`).
*   `tags` (list[str]): Массив полных имен (`fullName`) тегов (добавляются индексаторами и `TagRecord.add_to_file_rec`).
*   `indexed_by` (list[str]): Список имен (`fieldName`) примененных индексаторов (добавляются методами `mark_as_indexed`).
*   `backend_indexed` (list[str], optional): Список имен бэкендов, примененных индексатором `FaceDetector`.
*   `file_corrupted` (bool, optional): Устанавливается в `True`, если возникла ошибка при доступе к файлу во время `create_record_data`.
*   `ai_expertise` (list[dict], optional): Список результатов работы ИИ-моделей (добавляется `FileRecord.get_ai_expertise`). Структура словаря: `{ 'name': str, 'type': str, 'version': str, 'kwargs': str, 'data': Any }`.
*   `description` (str, optional): Описание файла (добавляется `Image_MetadataRead`, `ImageLLavaDescribe`).
*   `title` (str, optional): Заголовок файла (добавляется `Image_MetadataRead`).
*   `rating` (int, optional): Рейтинг файла (добавляется `Image_MetadataRead`).
*   `notes` (str, optional): Заметки к файлу (добавляется `Image_MetadataRead`).
*   `autor` (str, optional): Автор файла (добавляется `Image_MetadataRead`).
*   `modified_date` (Any, optional): Дата модификации из метаданных (добавляется `Image_MetadataRead`).
*   `categories` (Any, optional): Категории из метаданных (добавляется `Image_MetadataRead`).
*   `collected_description` (Any, optional): Собранное описание из метаданных (добавляется `Image_MetadataRead`).
*   `collected_objects` (Any, optional): Собранные объекты из метаданных (добавляется `Image_MetadataRead`).
*   `collected_authors` (Any, optional): Собранные авторы из метаданных (добавляется `Image_MetadataRead`).
*   `meta_error` (Any, optional): Ошибка чтения метаданных (добавляется `Image_MetadataRead`).
*   `metadata` (dict, optional): Полные исходные метаданные, если `Image_MetadataRead.embed_all_metadata=True`.
*   **Не подтверждено в коде:** `source_uri`, `created`, `modified`, `file_md5`, `favorite`, `embeddings`, `thumbnails`, `annotations`, `external_metadata`.

### Tag Record (Коллекция `tags_records`)

*   `_id` (ObjectId): Уникальный идентификатор.
*   `name` (str): Базовое имя тега (из `FieldPropInfo`).
*   `fullName` (str): Полное иерархическое имя тега (из `FieldPropInfo`).
*   `parent_tag` (ObjectId, optional): Ссылка на `_id` родительского `TagRecord` (из `FieldPropInfo`).
*   `autotag` (bool): Флаг автоматического добавления (из `FieldPropInfo`).
*   `remap_to` (str, optional): Строка с `fullName` тегов для переназначения (используется в `remap_tag`).
*   **Не подтверждено в коде:** `description`, `AI`, `path`, `sinonims`.

### Annotation Record (Коллекция `annotation_records`)

*   `_id` (ObjectId): Уникальный идентификатор.
*   `value` (Any): Значение аннотации (метка, координаты и т.д.) (из `FieldPropInfo`).
*   `parent_id` (ObjectId): Ссылка на `_id` родительского `AnnotationJob` (из `FieldPropInfo`).
*   `file_id` (ObjectId): Ссылка на `_id` связанного `FileRecord` (из `FieldPropInfo`).
*   **Не подтверждено в коде:** `type`, `AI`, `AI_wrong_annotation`, `label` (используется `value`), `description`, `score`, `created`, `updated`, `object_detection_region`.

### Annotation Job Record (Коллекция `annotation_jobs`)

*   `_id` (ObjectId): Уникальный идентификатор.
*   `name` (str): Имя задачи (из `FieldPropInfo`).
*   `type` (str): Тип задачи (например, "multiclass/image") (из `FieldPropInfo`).
*   `choices` (list): Список допустимых меток/классов (из `FieldPropInfo`).
*   **Не подтверждено в коде:** `not_annotated`.

[Назад к главной странице](./index.md)
