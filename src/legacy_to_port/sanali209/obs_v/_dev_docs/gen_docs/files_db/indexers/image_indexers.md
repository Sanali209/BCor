# Индексаторы изображений

Этот раздел описывает индексаторы, специфичные для извлечения метаданных и информации из файлов изображений.

## Доступные индексаторы

*   **`content_md5.py`**:
    *   **Назначение**: Определяет базовый класс `files_db_indexer` для других индексаторов `files_db`. **Не вычисляет MD5!**
    *   **Класс `files_db_indexer(ItemFieldIndexer)`**:
        *   `fieldName`: `"files_db_indexer"`
        *   `isNeedIndex()`: Проверяет, присутствует ли `self.fieldName` в поле `indexed_by` элемента `item`. Если да, возвращает `False`.
        *   `mark_as_indexed()`: Добавляет `self.fieldName` в поле `indexed_by` элемента `item`.
    *   *Примечание: Вычисление `file_content_md5` происходит при создании `FileRecord` с помощью `ImageDataCacheManager`.*
*   **`deepdanboru.py`**:
    *   **Класс**: `DeepDunBoru(files_db_indexer)`
    *   **`fieldName`**: `"deepdanbooru"`
    *   **Назначение**: Генерирует теги для изображения с помощью модели DeepDanbooru.
    *   **Логика**:
        1.  Использует `SLM.vision.imagetotext.backends.deep_dan_boru.DeepDanbury` для получения тегов.
        2.  Для каждого полученного тега создает/получает `TagRecord` с префиксом `auto/deepdanboru/`.
        3.  Добавляет `fullName` этих тегов в поле `tags` документа `FileRecord`.
    *   **Зависимости**: Модель DeepDanbooru.
*   **`face_detection.py`**:
    *   **Класс**: `FaceDetector(ItemFieldIndexer)`
    *   **`fieldName`**: `"face_detection"`
    *   **Назначение**: Обнаруживает лица на изображении с помощью различных бэкендов, сохраняет информацию о каждом обнаруженном лице как отдельную запись `Detection`.
    *   **Конфигурация**: Включается/выключается параметром `Indexer.detectFaces` в конфигурации.
    *   **Логика**:
        1.  Использует `ObjectDetectorProvider` для получения доступных бэкендов детекции.
        2.  Запускает каждый бэкенд, который еще не выполнялся для этого файла (отслеживается по полю `backend_indexed` в `FileRecord`).
        3.  Применяет Non-Max Suppression (`cv2.dnn.NMSBoxes`) для фильтрации перекрывающихся детекций.
        4.  Для каждой итоговой детекции:
            *   Сохраняет вырезанное изображение лица в файл (путь **жестко задан** в коде, TODO).
            *   Создает запись `Detection` в MongoDB (коллекция `collection_records`), связывая ее с исходным `FileRecord` через `parent_image_id` и сохраняя путь к изображению лица в `obj_image_path`.
            *   Связывает `Detection` с `DetectionObjectClass` ("face") и `Recognized_object` ("unknown").
        5.  Если лица найдены, добавляет тег `object_detect/face` к исходному `FileRecord`.
    *   **Зависимости**: `ObjectDetectorProvider`, `cv2`, `DetectionObjectClass`, `Detection`, `Recognized_object`, `TagRecord`.
*   **`llava_describe.py`**:
    *   **Класс**: `ImageLLavaDescribe(files_db_indexer)`
    *   **`fieldName`**: `"ImageLLavaDescribe"`
    *   **Назначение**: Генерирует детальное текстовое описание изображения с помощью модели LLaVA и сохраняет его в поле `description` записи `FileRecord`.
    *   **Логика**:
        1.  Использует метод `FileRecord.get_ai_expertise` для вызова бэкенда LLaVA (`mc_llava_13b_4b`) с промптом "detailed describe image".
        2.  Метод `get_ai_expertise` кэширует результат в поле `ai_expertise` документа `FileRecord`.
        3.  Полученное описание сохраняется в поле `description` документа `FileRecord`.
    *   **Зависимости**: `FileRecord`, бэкенд модели LLaVA (`mc_llava_13b_4b`).
*   **`metadata_read.py`**:
    *   **Класс**: `Image_MetadataRead(files_db_indexer)`
    *   **`fieldName`**: `"MetadataRead"`
    *   **Назначение**: Читает встроенные метаданные файла (EXIF, IPTC, XMP), нормализует их и сохраняет в полях `FileRecord` (`description`, `title`, `rating`, `tags`, `notes` и др.).
    *   **Логика**:
        1.  Использует `MDManager` для чтения метаданных.
        2.  Применяет цепочку `DictFieldMergeChainFunction` и `DictFormatterChainFunction` с предопределенными мэппингами для консолидации и нормализации различных полей метаданных (например, `XMP:Subject`, `IPTC:Keywords` -> `tags`; `XMP:Rating` -> `rating`).
        3.  Обрабатывает извлеченные теги: поддерживает иерархию (через `|`), создает/получает `TagRecord` и добавляет их в поле `tags` документа `FileRecord`.
        4.  Копирует нормализованные значения (описание, рейтинг, заголовок и т.д.) в соответствующие поля `FileRecord`.
        5.  Опционально (`embed_all_metadata=True`) сохраняет все исходные метаданные в поле `metadata` документа `FileRecord`.
    *   **Зависимости**: `FileRecord`, `MDManager`, `TagRecord`, `SLM.chains`.
*   **`tags_from_name.py`**:
    *   **Класс**: `ImageTagsFromName(files_db_indexer)`
    *   **`fieldName`**: `"Tags_from_name"`
    *   **Назначение**: Извлекает теги из полного пути к файлу (`FileRecord.full_path`), используя NLP-обработку и фильтрацию по словарю ("bag of words").
    *   **Логика**:
        1.  Использует `NLPPipline` для обработки `FileRecord.full_path`.
        2.  Выполняет шаги: замена разделителей, токенизация, приведение к нижнему регистру, удаление стоп-слов, чисел, коротких токенов, дубликатов.
        3.  **Важно**: Загружает "bag of words" из **жестко заданного пути** (`D:\data\bags_of_words.json`) и удаляет все токены, которых нет в этом словаре.
        4.  Для каждого оставшегося токена создает/получает `TagRecord` с префиксом `from_name/`.
        5.  Добавляет `fullName` этих тегов в поле `tags` документа `FileRecord`.
    *   **Зависимости**: `FileRecord`, `NLPPipline`, `TagRecord`, файл `bags_of_words.json`.

*TODO: Уточнить детали некоторых индексаторов (например, `NLPTokensDeleteRandString`).*

[Назад к обзору индексаторов](./index.md)
[Назад к главной странице](../../index.md)
