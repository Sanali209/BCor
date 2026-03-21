# Files Database Module (`files_db_module.py`)

Этот модуль определяет `FilesDBModule`, который является частью модульной архитектуры `appGlue`. Его основная задача - инициализация и конфигурация всех аспектов, связанных с базой данных файлов и связанными с ней компонентами, такими как кэш эмбеддингов и модели данных MongoDB.

## Зависимости

*   **Core Framework:** `SLM.appGlue.core` (`Module`, `TypedConfigSection`, `Allocator`)
*   **Embedding Cache:** `SLM.files_data_cache.tensor.Embeddings_cache`
*   **MongoDB Extensions:** `SLM.mongoext.MongoClientEXT_f.MongoClientExt`, `SLM.mongoext.wraper.MongoRecordWrapper`
*   **Data Models:**
    *   `SLM.files_db.components.File_record_wraper.FileRecord`
    *   `SLM.files_db.components.collectionItem.CollectionRecord`
    *   `SLM.files_db.components.fs_tag.TagRecord`
    *   `SLM.files_db.components.relations.relation.RelationRecord`
    *   `SLM.files_db.object_recognition.object_recognition` (`DetectionObjectClass`, `Detection`, `Recognized_object`)
    *   `SLM.files_db.annotation_tool.annotation` (`AnnotationRecord`, `AnnotationJob`)
*   **Vision Encoders:** Множество классов `CNN_Encoder_*` из `SLM.vision.imagetotensor.backends.*` и `SLM.vision.imagetotensor.custom.*` (BLIP, DINO, CLIP_DML, InceptionV3, InceptionResNetV2, MobileNetV3, ResNet50, FaceNet, custom, mv2_custom).

## Глобальные переменные

*   `emb_cache` (`Embeddings_cache` | None): Глобальный экземпляр кэша эмбеддингов. Инициализируется значением `None` и заполняется в методе `FilesDBModule.load()`.

## Функции векторизации (`vectorize_*`)

Модуль содержит набор функций с именами вида `vectorize_[object_type]_[encoder_name]`, например:

*   `vectorize_face_FaceNet(face: Detection)`
*   `vectorize_FileRecord_ResNet50(file: FileRecord)`
*   `vectorize_face_CLIP_DML(face: Detection)`
*   ... и так далее для всех импортированных энкодеров и для типов `Detection` и `FileRecord`.

**Назначение:** Эти функции предоставляют унифицированный способ получения предварительно вычисленного векторного представления (эмбеддинга) для объекта (`Detection` или `FileRecord`) с использованием конкретной модели-энкодера.

**Принцип работы:**
1.  Принимают объект (`face` или `file`).
2.  Извлекают путь к соответствующему изображению (`obj_image_path` для `Detection`, `full_path` для `FileRecord`).
3.  Используют глобальный `emb_cache.get_by_path()`, передавая путь и строку формата энкодера (например, `CNN_Encoder_FaceNet.format`), для получения вектора из кэша.
4.  Возвращают полученный вектор.

**Примечание:** Все эти функции содержат комментарий `#todo improve by using tumb api`. Это указывает на то, что текущая реализация, напрямую использующая путь к оригинальному файлу или вырезанному объекту, может быть неоптимальной и в будущем может быть заменена на использование API для работы с миниатюрами (thumbnails), возможно, для повышения производительности или унификации доступа к изображениям.

## Конфигурация (`IndexerConfig`)

*   **`IndexerConfig(TypedConfigSection)`**:
    *   Определяет секцию конфигурации `"Indexer"` с использованием `TypedConfigSection` из `appGlue.core`.
    *   Содержит параметр `detectFaces` (bool, по умолчанию `True`), который, вероятно, управляет включением/выключением детекции лиц во время индексации файлов.
    *   Регистрируется в глобальном конфигурационном менеджере `Allocator.config`.

## Основной Модуль (`FilesDBModule`)

*   **`FilesDBModule(Module)`**:
    *   Наследуется от `Module`, интегрируясь в систему модулей `appGlue`.
    *   **`__init__(self)`**: Инициализирует модуль с именем "FilesDBModule".
    *   **`load(self)`**: Ключевой метод, выполняющий всю инициализацию при загрузке модуля:
        1.  **Инициализация кэша эмбеддингов:** Создает экземпляр `Embeddings_cache`, передавая ему список форматов всех поддерживаемых энкодеров. Этот кэш используется функциями `vectorize_*`.
        2.  **Настройка MongoDB:**
            *   Получает экземпляр `MongoClientExt`.
            *   Устанавливает этот клиент для `MongoRecordWrapper`.
        3.  **Регистрация Коллекций/Моделей:** Регистрирует все необходимые классы моделей данных (`CollectionRecord`, `FileRecord`, `TagRecord`, `RelationRecord`, `DetectionObjectClass`, `Detection`, `Recognized_object`, `AnnotationRecord`, `AnnotationJob`) в `MongoClientExt`. Это связывает классы Python с коллекциями MongoDB.
        4.  **Маппинг типов:** Настраивает `CollectionRecord.itemTypeMap` для полиморфных связей (например, чтобы `CollectionRecord` мог содержать `FileRecord`, `Detection` и т.д.).
        5.  **Создание Индексов:** Вызывает `create_index()` для различных коллекций (`FileRecord`, `TagRecord`, `RelationRecord`, `DetectionObjectClass`, `Detection`, `AnnotationJob`, `AnnotationRecord`), чтобы оптимизировать запросы к базе данных по часто используемым полям (например, пути, MD5, текстовый поиск, ID связей).
        6.  **Настройка Обработчиков Удаления:** Подписывает методы очистки (`RelationRecord.delete_all_relations`, `Detection.del_detection`) на события удаления родительских записей (`CollectionRecord.onDelete`, `FileRecord.onDelete`) для поддержания целостности данных (каскадное удаление связей и детекций).

**Роль в приложении:** `FilesDBModule` действует как точка входа для настройки всего, что связано с хранением и доступом к информации о файлах, их метаданных, результатах анализа (детекции, эмбеддинги) и аннотациях в MongoDB. Он обеспечивает готовность базы данных и связанных сервисов (как кэш эмбеддингов) к использованию другими частями приложения.
