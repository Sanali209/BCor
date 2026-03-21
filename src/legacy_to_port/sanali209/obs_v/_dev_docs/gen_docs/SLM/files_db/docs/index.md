# Files DB Documentation (`docs/`)

Эта директория содержит существующие файлы документации, описывающие структуру данных и концепции, связанные с модулем `files_db`.

## Содержимое

*   [`file_db_entities.md`](file_db_entities.md): Краткий список основных сущностей базы данных файлов (File Record, Annotation Record, Annotation job).
*   [`file_record_structure.md`](file_record_structure.md): Подробное описание структуры документов MongoDB для `File Record` и `Tag Record`.
*   [`Annotation/`](Annotation/index.md): Поддиректория с документацией по аннотациям (в формате `.rst`).
    *   `Annotation.rst`: Описание структуры записей заданий аннотаций и самих аннотаций.
    *   `anotation_types.rst`: Заготовка для списка типов аннотаций.

**Примечание:** Часть документации в этой директории (в подпапке `Annotation/`) находится в формате reStructuredText (`.rst`). Документация может быть не полностью синхронизирована с текущей реализацией кода.
