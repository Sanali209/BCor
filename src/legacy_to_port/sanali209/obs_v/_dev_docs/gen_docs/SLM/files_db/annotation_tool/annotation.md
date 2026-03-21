# Annotation Data Models and Management (`annotation.py`)

Этот модуль определяет основные классы и функции для управления аннотациями данных в SLM. Он тесно интегрирован с MongoDB через `MongoRecordWrapper` и предоставляет структуру для создания, управления и использования аннотированных данных, вероятно, для обучения моделей машинного обучения.

## Зависимости

*   `json`, `os.path`: Стандартные библиотеки Python.
*   `loguru`, `tqdm`: Внешние библиотеки для логирования и отображения прогресса.
*   **SLM Core & DAL:** `SLM.appGlue.DAL.datalist2` (`MongoDataModel`, `DataViewCursor`, `MongoDataQuery`, `DataListModelBase`), `SLM.appGlue.core.Allocator`.
*   **SLM Files DB:** `SLM.files_db.annotation_tool.annotation_export.DataSetExporterManager`, `SLM.files_db.components.File_record_wraper` (`FileRecord`, `get_file_record_by_folder`).
*   **SLM Utils:** `SLM.appGlue.iotools.pathtools.get_files`.
*   **SLM MongoDB Extensions:** `SLM.mongoext.MongoClientEXT_f.MongoClientExt`, `SLM.mongoext.wraper` (`MongoRecordWrapper`, `FieldPropInfo`).

## Глобальные переменные

*   `all_jobTypes` (list[str]): Список предопределенных типов заданий аннотирования (например, "binary/image", "multiclass/image", "image_object_detection").

## Класс `AnnotationRecord(MongoRecordWrapper)`

*   **Назначение:** Представляет отдельную запись аннотации, связывающую файл (`FileRecord`) с заданием аннотирования (`AnnotationJob`) и присвоенным значением (меткой).
*   **Поля (определены через `FieldPropInfo`):**
    *   `value` (Any): Значение аннотации (метка, координаты, текст и т.д.). `None` означает, что элемент не аннотирован.
    *   `parent_id` (str): ID родительского `AnnotationJob`.
    *   `file_id` (str): ID связанного `FileRecord`.
*   **Свойства:**
    *   `parent` (`AnnotationJob` | None): Возвращает экземпляр `AnnotationJob`, связанный с этой записью (через `parent_id`).
    *   `file` (`FileRecord` | None): Возвращает экземпляр `FileRecord`, связанный с этой записью (через `file_id`).

## Классы для работы со списком неаннотированных элементов (`AnnJobDataQuery`, `AJDataModel`)

*   **`AnnJobDataQuery(MongoDataQuery)`**:
    *   **Назначение:** Специализированный класс запросов для получения **неаннотированных** записей (`AnnotationRecord.value == None`) для конкретного `AnnotationJob`.
    *   **Методы:**
        *   `get_by_query(...)`: Извлекает список неаннотированных `AnnotationRecord` для заданного `job_id`. *(Примечание: Реализация загружает все записи и затем применяет `skip`/`limit` в памяти, что может быть неэффективно для больших наборов данных. Комментарий `todo for improve performance...` в начале файла указывает на это)*.
        *   `count_all()`: Возвращает количество неаннотированных записей для задания.
*   **`AJDataModel(DataListModelBase)`**:
    *   **Назначение:** Модель данных (вероятно, для использования в UI), которая использует `AnnJobDataQuery` для предоставления доступа к списку неаннотированных элементов задания.
    *   **Методы:** Переопределяет `append`, `remove`, `clear` для взаимодействия с коллекцией MongoDB.

## Класс `AnnotationJob(MongoRecordWrapper)`

*   **Назначение:** Представляет собой задание или проект по аннотированию данных. Содержит метаданные о задании (имя, тип, возможные метки) и управляет связанными `AnnotationRecord`.
*   **Поля (определены через `FieldPropInfo`):**
    *   `not_annotated` (list): *Поле выглядит устаревшим или не до конца реализованным, так как основная логика работы с неаннотированными элементами реализована через `AnnJobDataQuery` и проверку `AnnotationRecord.value == None`.*
    *   `name` (str): Имя задания.
    *   `type` (str): Тип задания (из `all_jobTypes`).
    *   `choices` (object): Возможные значения/метки для аннотации (например, список строк для классификации).
*   **Атрибуты экземпляра:**
    *   `job_data` (`AJDataModel`): Экземпляр модели данных для доступа к неаннотированным элементам.
    *   `coll_view` (`DataViewCursor`): Курсор для навигации по неаннотированным элементам (`job_data`).
*   **Статический метод:**
    *   `get_by_name(job_name)`: Находит и возвращает `AnnotationJob` по имени.
*   **Методы управления аннотациями:**
    *   `mark_not_annotated(file: FileRecord)`: Создает (если не существует) запись `AnnotationRecord` для данного файла и задания, помечая его как требующий аннотации (устанавливая `value=None`).
    *   `mark_not_annotated_in_directory(path)`: Применяет `mark_not_annotated` ко всем файлам в указанной директории.
    *   `file_exist_in_annotation(file_id)`: Проверяет, существует ли `AnnotationRecord` для данного файла в этом задании.
    *   `move_next_annotation_item()` / `move_prev_annotation_item()`: Перемещает курсор `coll_view` к следующему/предыдущему неаннотированному элементу.
    *   `annotate(value, override_exist=True)`: Присваивает значение `value` текущему элементу в `coll_view`.
    *   `annotate_file(file: FileRecord, value, override_annotation=False)`: Находит `AnnotationRecord` для указанного файла и присваивает ему значение `value`.
    *   `remove_annotation_record(file: FileRecord)`: Удаляет `AnnotationRecord` для указанного файла.
    *   `get_annotation_record(file: FileRecord)`: Получает `AnnotationRecord` для указанного файла.
*   **Методы запросов и статистики:**
    *   `count_annotated_items(value=None)`: Подсчитывает количество аннотированных записей (опционально с конкретным значением).
    *   `get_all_annotated()`: Возвращает список всех аннотированных `AnnotationRecord` для этого задания.
    *   `get_all_not_annotated()`: Возвращает список всех неаннотированных `AnnotationRecord` для этого задания.
    *   `get_ann_records_by_label(label)`: Возвращает список `AnnotationRecord` с указанной меткой.
*   **Методы управления заданием:**
    *   `export_to_dataset(path, _format)`: Экспортирует аннотированные данные в указанный формат датасета, используя `DataSetExporterManager`.
    *   `clear_not_annotated_list()`: Удаляет все неаннотированные `AnnotationRecord` из задания.
    *   `rename_annotation_label(old_name, new_name)`: Переименовывает метку в `choices` и обновляет все `AnnotationRecord` со старой меткой.
    *   `add_annotation_choices(new_choises)`: Добавляет новые возможные метки в `choices`.
    *   `clear_job()`: Удаляет все `AnnotationRecord`, связанные с этим заданием.
    *   `remove_annotation_dublicates()` / `remove_annotation_dublicates2()`: Удаляет дублирующиеся `AnnotationRecord` (основываясь на `file_id` или `file.full_path`).
    *   `remove_broken_annotations()`: Удаляет `AnnotationRecord`, ссылающиеся на несуществующие файлы.

## Класс `SLMAnnotationClient`

*   **Назначение:** Предоставляет интерфейс для управления несколькими `AnnotationJob`.
*   **Методы:**
    *   `get_all_jobs(records_filter=None)`: Возвращает список всех `AnnotationJob`, опционально с фильтром.
    *   `restore_from_json(path)`: Загружает аннотации из JSON файла. Находит соответствующие `AnnotationJob` по имени и `FileRecord` по MD5 хэшу, затем создает или обновляет `AnnotationRecord`. *(Примечание: Логика обновления `not_annotated` выглядит сложной и потенциально медленной)*.
    *   `save_to_json(path)`: Сохраняет все задания и их аннотации (MD5 файла и метка) в JSON файл.

## Утилитарная функция `annotate_folder`

*   **`annotate_folder(path, job, label)`**:
    *   Находит все файлы изображений в указанной папке.
    *   Для каждого файла находит соответствующий `FileRecord`.
    *   Вызывает `job.annotate_file()` для присвоения указанной метки `label` каждому найденному файлу в рамках задания `job`.

Этот модуль формирует основу для системы аннотирования данных в SLM, позволяя создавать задания, управлять процессом разметки и экспортировать результаты для дальнейшего использования.
