# Главный модуль (`files_db_module.py`)

Этот файл содержит класс `FilesDBModule`, который действует как точка инициализации для всего модуля `files_db` в рамках приложения `SLM`.

## `FilesDBModule(Module)`

*   **Назначение**: Инициализация и настройка компонентов модуля `files_db` при загрузке приложения.
*   **Метод `load()`**:
    *   Получает экземпляр `MongoClientExt` (клиент MongoDB).
    *   Устанавливает этот клиент для всех классов, наследующих `MongoRecordWrapper`.
    *   Регистрирует коллекции MongoDB и связывает их с соответствующими классами-обертками (`FileRecord`, `TagRecord`, `RelationRecord`, `AnnotationRecord`, `AnnotationJob`, `Detection`, `Recognized_object`, `DetectionObjectClass`).
    *   Создает необходимые индексы MongoDB для зарегистрированных коллекций для оптимизации запросов.
    *   Инициализирует кэш эмбеддингов (`Embeddings_cache`) с поддержкой различных моделей (BLIP, DINO, CLIP, ResNet, Inception, MobileNet, FaceNet, custom).
    *   Регистрирует обработчики событий для каскадного удаления связанных данных (например, удаление `RelationRecord` при удалении `CollectionRecord`).

## Функции векторизации

Файл также определяет набор вспомогательных функций для получения эмбеддингов для объектов `Detection` (лиц) или `FileRecord` с использованием различных моделей через `Embeddings_cache`. Примеры:

*   `vectorize_face_FaceNet(face: Detection)`
*   `vectorize_FileRecord_ResNet50(file: FileRecord)`
*   `vectorize_FileRecord_CLIP_DML(file: FileRecord)`
*   ... и другие для разных моделей.

*Примечание: Эти функции помечены TODO для улучшения производительности за счет использования API превью.*

[Назад к главной странице](./index.md)
