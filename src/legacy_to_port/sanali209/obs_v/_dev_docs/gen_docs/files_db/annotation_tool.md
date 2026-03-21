# Инструмент аннотации

Этот раздел описывает компоненты и функции, связанные с аннотированием данных в модуле `files_db`.

## Основные классы и модули

*   **`AnnotationJob` (`annotation.py`)**: Представляет задачу аннотирования.
    *   Хранит имя (`name`), тип (`type`, например, "multiclass/image"), и возможные метки (`choices`).
    *   Предоставляет методы для управления аннотациями (`AnnotationRecord`), связанными с этой задачей: создание, поиск, обновление, удаление, экспорт.
    *   Использует `DataViewCursor` для навигации по элементам для аннотирования.
    *   См. [Основные концепции](../core_concepts.md#annotation-job-annotationpyannotationjob) для деталей полей MongoDB и методов.
*   **`AnnotationRecord` (`annotation.py`)**: Представляет одну аннотацию для конкретного файла в рамках задачи.
    *   Хранит значение аннотации (`value`), ссылку на родительскую задачу (`parent_id`) и ссылку на файл (`file_id`).
    *   См. [Основные концепции](../core_concepts.md#annotation-record-annotationpyannotationrecord) для деталей полей MongoDB.
*   **`annotation_export.py`**:
    *   **`DataSetExporterManager(Service)`**: Менеджер для регистрации и получения экспортеров.
    *   **`DataSetExporter` (ABC)**: Базовый класс для экспортеров с методами `is_job_type_supported` и `ExportToDataset`.
    *   **Реализации экспортеров (для `multiclass/images`)**:
        *   `DataSetExporterImageMultiClass_dirs`: Экспортирует изображения в папки по именам классов (`[dataset_path]/[label]/[uuid].jpg`). Копирует уменьшенные изображения.
        *   `DataSetExporterImageMultiClass_dirs_cum`: **(Зарегистрирован по умолчанию)**. Выполняет кумулятивный экспорт по батчам (`[dataset_path]/[batch_num]/[label]/[filename].jpg`), избегая дубликатов с помощью MD5-списка (`data.json`).
        *   `DataSetExporterImageMultiClass_anomali`: Экспортирует изображения, которые не удовлетворяют условию внешнего `Annotator`'а (для поиска аномалий/ошибок).
*   **Скрипты обучения/настройки**:
    *   **`single_label_tune.py`**:
        *   **Назначение**: Тонкая настройка (fine-tuning) гиперпараметров модели классификации изображений (`google/vit-base-patch16-224`) с использованием `Ray Tune`.
        *   **Вход**: Данные из `AnnotationJob` (например, "NSFWFilter").
        *   **Процесс**: Загружает аннотации, разделяет на train/validation, использует `Ray Tune` для поиска лучших `lr` и `optimizer_type`, обучает модель внутри `Ray Tune` trials, сообщает метрики и чекпоинты.
        *   **Выход**: Сохраняет лучшую модель локально и загружает на Hugging Face Hub.
        *   **Библиотеки**: `torch`, `transformers`, `ray[tune]`, `sklearn`, `huggingface_hub`.
    *   **`singl_label_train.py`**:
        *   **Назначение**: Простое обучение (fine-tuning) модели классификации изображений (`google/vit-base-patch16-224`) с **фиксированными** гиперпараметрами. **Не использует Ray Tune.**
        *   **Вход**: Данные из `AnnotationJob` (например, "NSFWFilter"), фиксированные `LEARNING_RATE`, `NUM_EPOCHS`.
        *   **Процесс**: Загружает аннотации, разделяет на train/validation, обучает модель заданное число эпох, сохраняет локально лучшую модель по `val_acc`.
        *   **Выход**: Сохраняет лучшую модель локально и загружает на Hugging Face Hub.
        *   **Библиотеки**: `torch`, `transformers`, `sklearn`, `huggingface_hub`.
    *   **`singl_label_tune2.py`**:
        *   **Назначение**: Оптимизированная версия `single_label_tune.py` для настройки гиперпараметров `google/vit-base-patch16-224` с `Ray Tune`.
        *   **Отличия**: Использует **`diskcache`** для кэширования предобработанных изображений (ускорение), расширенное пространство поиска (`batch_size`, `weight_decay`), динамические `num_workers` для `DataLoader`.
        *   **Вход/Выход/Библиотеки**: Аналогичны `single_label_tune.py`, плюс `diskcache`, `hashlib`.
*   **Предопределенные задачи (`predefained_jobs/`)**:
    *   **`jobs_multiclass.py`**:
        *   **Назначение**: Создает или обновляет набор предопределенных задач аннотирования (`AnnotationJob`) типа `multiclass/image` в MongoDB.
        *   **Данные**: Содержит словарь `job_map` с именами задач ("NSFWFilter", "worlds", "image genres", "rating" и др.) и списками их меток (`choices`).
        *   **Использование**: Запуск скрипта (`python jobs_multiclass.py`) наполняет коллекцию `annotation_jobs` этими задачами.
*   **`SLMAnnotationClient` (`annotation.py`)**: Клиентский класс для работы с несколькими `AnnotationJob`, включая сохранение/восстановление аннотаций в/из JSON.
*   **`annotate_folder` (`annotation.py`)**: Вспомогательная функция для быстрой аннотации всех файлов в папке одной меткой.

## Типы задач аннотирования (`annotation.py:all_jobTypes`)

*   `binary/image`
*   `multiclass/image`
*   `multilabel/image`
*   `image_object_detection`
*   `image_segmentation`
*   `image_to_text`

## Существующая документация

*   См. также существующие файлы в `Python/SLM/files_db/docs/Annotation/` (хотя `anotation_types.rst` был почти пуст).

[Назад к главной странице](./index.md)
