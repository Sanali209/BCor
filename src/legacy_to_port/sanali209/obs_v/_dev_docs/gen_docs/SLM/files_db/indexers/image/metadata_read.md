# Image Metadata Reader (`metadata_read.py`)

Этот модуль реализует индексатор для чтения, нормализации и сохранения метаданных изображений из различных источников (EXIF, IPTC, XMP и др.).

## Зависимости

*   `SLM.files_db.indexers.image.content_md5.files_db_indexer`: Базовый класс для индексаторов.
*   `SLM.files_db.components.fs_tag.TagRecord`: Для работы с тегами.
*   `SLM.chains.chains_main`: Функции для обработки данных в цепочке.
    *   `DictFieldMergeChainFunction`: Для объединения полей по схеме.
    *   `DictFormatterChainFunction`: Для форматирования и валидации полей.
*   `SLM.metadata.MDManager.mdmanager.MDManager`: Менеджер для чтения метаданных.

## Конфигурация метаданных

### Схема объединения полей (`collect_descr_coollect_mapping`)

Определяет, как группировать различные поля метаданных в коллекции:

*   **`SLMMeta:collected_description`**: Объединяет поля с описаниями (комментарии, заголовки, подписи) из:
    *   EXIF (`ImageDescription`, `UserComment`)
    *   IPTC (`Caption-Abstract`, `DocumentNotes`, др.)
    *   XMP (`About`, `Caption`, `ArtworkPhysicalDescription`, др.)

*   **`SLMMeta:collected_objects`**: Объединяет поля с именами объектов:
    *   `IPTC:ObjectName`
    *   `XMP:PersonInImage`
    *   `XMP:Personality`

*   **`SLMMeta:collected_authors`**: Объединяет поля с информацией об авторах из XMP.

### Схема мапирования полей (`fields_mapping`)

Определяет, как отображать различные поля метаданных на стандартизированные поля SLM:

*   `SLMMeta:modified_date`: Дата модификации из XMP/EXIF
*   `SLMMeta:rating`: Рейтинг из XMP/EXIF
*   `SLMMeta:tags`: Теги/ключевые слова из XMP/IPTC
*   `SLMMeta:categories`: Категории из IPTC/XMP
*   `SLMMeta:autor`: Информация об авторе
*   `SLMMeta:title`: Заголовок/название
*   `SLMMeta:description`: Описание
*   `SLMMeta:notes`: Заметки/комментарии
*   `SLMMeta:MIMETYPE`: MIME-тип файла
*   `SLM:meta_error`: Ошибки чтения метаданных

## Класс `Image_MetadataRead`

```python
class Image_MetadataRead(files_db_indexer):
    # ... реализация ...
```

### Инициализация

*   **`__init__`:**
    *   Устанавливает `fieldName = "MetadataRead"`.
    *   Имеет флаг `embed_all_metadata` (по умолчанию `False`) для контроля сохранения всех метаданных.

### Вспомогательные методы

*   **`add_metadata(self, item, key, value)`:**
    *   Добавляет пару ключ-значение в поле `metadata` записи, если `embed_all_metadata=True`.

*   **`keyword_validator(x)`:**
    *   Преобразует различные форматы входных данных (строки, списки, числа) в список строк.
    *   Разделяет строки по запятым.

### Основная функциональность

**`index(self, parent_indexer: ItemIndexer, item, need_index)`:**

1.  **Чтение метаданных:**
    *   Получает `FileRecord` для доступа к файлу.
    *   Создает `MDManager` и читает метаданные.

2.  **Настройка обработки:**
    *   Определяет валидаторы для разных типов полей.
    *   Создает цепочку обработки из:
        *   `DictFieldMergeChainFunction` для объединения полей.
        *   `DictFormatterChainFunction` для форматирования и валидации.

3.  **Обработка тегов:**
    *   Извлекает теги из результата.
    *   Обрабатывает иерархические теги (разделенные `|`).
    *   Создает или получает `TagRecord` для каждого тега.
    *   Добавляет теги к списку тегов файла.
    *   Удаляет дубликаты.

4.  **Сохранение результатов:**
    *   Копирует поля с префиксом `SLMMeta:` в корень записи (без префикса).
    *   Другие поля добавляются в `metadata` если `embed_all_metadata=True`.
    *   Устанавливает флаг `item_indexed` и отмечает запись как обработанную.

## TODO

1.  `# todo :implement force _reindex metadata`: Реализовать принудительное переиндексирование метаданных.
2.  `# todo: implement import tags from file`: Реализовать импорт тегов из файла.

## Использование

Этот индексатор является критически важным компонентом для:
*   Извлечения метаданных из различных форматов (EXIF, IPTC, XMP).
*   Нормализации и стандартизации метаданных.
*   Создания единой системы тегов из разных источников.
*   Сохранения важной информации о файлах в структурированном виде.
