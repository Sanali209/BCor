# Компонент: Веб-ссылки (`web_link_record.py`)

Этот компонент отвечает за хранение и потенциальную обработку ссылок на внешние веб-ресурсы (URI).

## `WebLinkRecord(CollectionRecord)`

*   **Назначение**: Представляет веб-ссылку (URI) в базе данных MongoDB.
*   **Коллекция MongoDB**: `collection_records` (используется `itemType='WebLinkRecord'` для различения).
*   **Наследование**: Наследуется от `SLM.files_db.components.collectionItem.CollectionRecord`.
*   **Ключевые поля MongoDB**:
    *   `_id`: Уникальный идентификатор.
    *   `itemType` (str): Установлено в `'WebLinkRecord'`.
    *   `name` (str): Хранит сам URI (веб-адрес). Используется свойство `uri` в классе.
    *   *(Другие поля из `CollectionRecord` могут наследоваться).*
*   **Инициализация**: Функция `init(config)` регистрирует `WebLinkRecord` в `CollectionRecord.itemTypeMap`.

## Обработка URI (`uriDecoder`, `uriDecoderManager`)

В файле также определены классы для обработки содержимого URI, хотя их интеграция с `WebLinkRecord` не показана явно.

*   **`uriDecoderManager`**: Задуман как реестр для различных обработчиков URI. Определяет место хранения (`screen_shot/`) и размер скриншотов.
*   **`uriDecoder`**: Предоставляет базовую функциональность для обработки URL:
    *   `create_thumbnail(url)`: Делает скриншот URL с помощью `html2image`.
        *   **Зависимости**: `html2image`, браузер Microsoft Edge.
        *   **Выход**: Сохраняет JPG файл в папку `screen_shot/`.
    *   `get_page_text(url)`: Загружает страницу и извлекает весь видимый текст.
        *   **Зависимости**: `requests`, `beautifulsoup4`.
    *   `get_summary(page_text)`: Генерирует краткое содержание текста с помощью LLM через `langchain`.
        *   **Зависимости**: `langchain`, `langchain_core`, Hugging Face `transformers`, конкретная LLM (например, `mistralai/Mistral-7B-Instruct-v0.2`).

*   **TODO**: Уточнить механизм связи `WebLinkRecord` с другими записями (например, `FileRecord`). Возможные варианты: поле `source_uri` в `FileRecord`, использование `RelationRecord`. Также необходимо описать, как и когда инициируется обработка URI с помощью `uriDecoder` (например, через индексатор, отдельный скрипт или вручную).

[Назад к обзору компонентов](./index.md)
[Назад к главной странице](../../index.md)
