# Duplicate/Similarity Search (`dubsearch.py`)

Этот модуль реализует функциональность поиска визуально похожих изображений (файлов `FileRecord`) и обнаруженных объектов (`Detection`, например, лиц или персон) с использованием векторных представлений (embeddings). Он тесно интегрирован с `VectorDB` и управляет созданием записей `RelationRecord` для хранения найденных связей схожести.

## Зависимости

*   `os`, `copy`, `concurrent.futures.ThreadPoolExecutor`
*   `pymongo.InsertOne`
*   `tqdm`
*   `SLM.appGlue.core.Allocator`
*   `SLM.files_data_cache.tensor.Embeddings_cache` (не используется напрямую, но подразумевается `VectorDB`)
*   `SLM.files_db.components.File_record_wraper.FileRecord`, `get_file_record_by_folder`
*   `SLM.files_db.components.relations.relation.RelationRecord`
*   Различные функции векторизации из `SLM.files_db.files_db_module` (например, `vectorize_face_FaceNet`, `vectorize_FileRecord_CLIP_DML`)
*   `SLM.files_db.object_recognition.object_recognition.Detection`
*   `SLM.iterable.bach_builder.BatchBuilder`
*   `SLM.appGlue.iotools.pathtools.get_files`
*   `SLM.vector_db.vector_db.VectorDB`, `SearchScopeList`, `ResultGroup`, `ResultItem`
*   Различные CNN-энкодеры из `SLM.vision.imagetotensor.backends.*` и `SLM.vision.imagetotensor.custom.*`

## Ключевые Компоненты

### Класс `DubRelation`

*   Служит **конфигурационным классом**, не хранящимся в БД.
*   **`prefs_dict`**: Статический словарь, определяющий пресеты (настройки) для поиска схожести **объектов** (`Detection`). Каждый пресет для класса объекта (например, 'face', 'person') содержит список конфигураций, включающих:
    *   `preset_name`: Имя для регистрации в `VectorDB`.
    *   `vector_size`: Размерность вектора эмбеддинга.
    *   `vectorize_func`: Функция для получения вектора из объекта `Detection`.
    *   `metric`: Метрика расстояния (обычно 'angular').

### Регистрация Пресетов в `VectorDB`

При импорте модуля происходит **регистрация множества пресетов** в `VectorDB` с помощью `VectorDB.register_pref`. Регистрируются:
1.  Пресеты для **объектов** (лиц, персон) из `DubRelation.prefs_dict`.
2.  Пресеты для **целых файлов** (`FileRecord`), используя различные CNN-энкодеры (ResNet50, MobileNetV3, InceptionV3, InceptionResNetV2, CLIP, DINO, BLIP, FaceNet, кастомные).

Эта регистрация позволяет `VectorDB` корректно обрабатывать запросы на векторизацию и поиск схожести для разных типов данных и с использованием разных моделей.

## Основные Функции

*   **`find_dubs_2(paths: list[str], related, threshold=0.95, format=..., pats_dubs_search=True, related_search=True)`**:
    *   Находит похожие **файлы** (`FileRecord`).
    *   Собирает файлы из `paths`.
    *   Использует `VectorDB` и `SearchScopeList` для поиска:
        *   Дубликатов внутри `paths` (если `pats_dubs_search=True`).
        *   Файлов из `related` внутри `paths` (если `related_search=True`).
    *   Возвращает список `ResultGroup`, содержащий результаты поиска для каждого исходного файла.
*   **`write_list_filtrate(write_list)`**:
    *   Утилита для фильтрации списка операций `InsertOne` для `RelationRecord`, чтобы избежать создания дублирующих связей (A->B и B->A).
*   **`create_graf_dubs(paths: list[str], related: list[str], th=0.95, encoder=..., ...)`**:
    *   Оркестрирует процесс поиска похожих **файлов**.
    *   Вызывает `find_dubs_2`.
    *   Обрабатывает результаты, проверяет наличие существующих связей `RelationRecord` типа `"similar_search"`.
    *   Создает новые записи `RelationRecord` типа `"similar_search"` с указанием `emb_type` (имя энкодера) и `distance` через `bulk_write`.
*   **`create_face_graph()`**:
    *   Оркестрирует процесс поиска похожих **объектов** (`Detection`), таких как лица или персоны.
    *   Использует пресеты из `DubRelation.prefs_dict`.
    *   Для каждого класса объектов и пресета выполняет поиск дубликатов (`find_dubs`) среди объектов `Detection`.
    *   Проверяет наличие существующих связей `RelationRecord` типа `"similar_obj_search"`.
    *   Создает новые записи `RelationRecord` типа `"similar_obj_search"` с указанием `emb_type`, `distance` и `object_class` через `bulk_write`.
*   **`project_object_to_image_graps()`**:
    *   "Проецирует" существующие связи схожести между **объектами** (`similar_obj_search`) на уровень **файлов**.
    *   Находит родительские `FileRecord` для связанных объектов.
    *   Создает или обновляет связи `RelationRecord` типа `"similar_search"` между этими файлами, перенося информацию (`sub_type`, `emb_type`, `distance`) из объектной связи.
*   **`del_image_search_refs(max_distance=0.95)`**:
    *   Удаляет "слабые" (`distance > max_distance`) связи между файлами (`similar_search`), которые не были получены из схожести объектов (`sub_type == 'none'`).

## Рабочий Процесс

1.  **Регистрация Пресетов:** При запуске приложения регистрируются все необходимые конфигурации векторизации в `VectorDB`.
2.  **Поиск Схожести:** Вызываются функции `create_graf_dubs` (для файлов) или `create_face_graph` (для объектов).
3.  **Векторизация и Поиск:** Эти функции используют `VectorDB` и `SearchScopeList` для получения векторных представлений и выполнения поиска ближайших соседей.
4.  **Создание Связей:** Найденные пары похожих элементов (файлы или объекты) проверяются на наличие существующих связей `RelationRecord`. Новые связи создаются с соответствующим типом (`"similar_search"` или `"similar_obj_search"`) и метаданными (тип эмбеддинга, расстояние).
5.  **Проекция (опционально):** `project_object_to_image_graps` может быть вызвана для переноса информации о схожести объектов на уровень файлов.
6.  **Очистка (опционально):** `del_image_search_refs` может использоваться для удаления слабых или нерелевантных связей.

Этот модуль обеспечивает основу для построения графа схожести между элементами в базе данных SLM.
