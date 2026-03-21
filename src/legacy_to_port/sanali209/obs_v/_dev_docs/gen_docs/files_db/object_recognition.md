# Распознавание объектов (`object_recognition.py`)

Этот раздел описывает компоненты, отвечающие за хранение и управление информацией об объектах, обнаруженных на изображениях. Сама детекция обычно выполняется [индексаторами](./indexers/image_indexers.md) (например, `FaceDetector`).

## Основные классы

1.  **`DetectionObjectClass(MongoRecordWrapper)`**:
    *   **Назначение**: Представляет *класс* обнаруживаемых объектов (например, "face", "person", "cat").
    *   **Коллекция MongoDB**: `object_class_dict`.
    *   **Поля**: `_id`, `name` (имя класса).
    *   **Методы**: `get_recognized_objects()` (находит все `Recognized_object` этого класса), `get(name)` (находит класс по имени).

2.  **`Detection(CollectionRecord)`**:
    *   **Назначение**: Представляет *конкретный экземпляр* объекта, обнаруженный на *конкретном изображении*. Создается индексаторами (например, `FaceDetector`).
    *   **Коллекция MongoDB**: `collection_records` (с `itemType='Detection'`).
    *   **Поля**:
        *   `object_class` (str): Имя класса объекта (ссылка на `DetectionObjectClass.name`).
        *   `rect_region` (list): Координаты рамки объекта.
        *   `region_format` (str): Формат координат (`RegionFormat`).
        *   `backend` (str): Имя модели/бэкенда, выполнившего обнаружение.
        *   `obj_image_path` (str): **Путь к файлу с вырезанным изображением** обнаруженного объекта.
        *   `score` (float): Уверенность детектора.
        *   `is_wrong` (bool): Флаг для пометки ложных срабатываний.
        *   `parent_image_id` (ObjectId): Ссылка на `_id` родительского `FileRecord`.
        *   `parent_obj_id` (ObjectId): Ссылка на `_id` родительского `Recognized_object` (если объект был распознан).
    *   **Методы**:
        *   `get_rect()`/`set_rect()`: Работа с координатами рамки.
        *   `parent_file`/`parent_obj` (properties): Доступ к родительским записям.
        *   `delete()`: **Удаляет файл с вырезанным изображением (`obj_image_path`)**, связанные `RelationRecord` и саму запись `Detection`.
        *   `set_recognized_object(rec_obj)`: Устанавливает связь с `Recognized_object`.
        *   `update_rect_image()`: Пересохраняет вырезанное изображение при изменении рамки.

3.  **`Recognized_object(CollectionRecord)`**:
    *   **Назначение**: Представляет конкретный *распознанный* объект (например, "Человек А"). Группирует несколько записей `Detection` одного и того же объекта с разных изображений.
    *   **Коллекция MongoDB**: `collection_records` (с `itemType='Recognized_object'`).
    *   **Поля**:
        *   `name` (str): Уникальное имя распознанного объекта (например, "unknown", "person_1").
        *   `obj_class_id` (ObjectId): Ссылка на `_id` соответствующего `DetectionObjectClass`.
    *   **Методы**:
        *   `get_detections()`: Находит все `Detection`, связанные с этим `Recognized_object`.
        *   `set_detection()`: Связывает `Detection` с этим `Recognized_object`.

4.  **`RegionFormat(Enum)`**: Перечисление форматов координат (`abs_xywh`, `abs_xyxy`, `norm_xywh`, `norm_xyxy`, `proc_xywh`, `proc_xyxy`).

Эта структура позволяет отделить факт обнаружения объекта (`Detection`) от его идентификации (`Recognized_object`) и классификации (`DetectionObjectClass`).

[Назад к главной странице](./index.md)
