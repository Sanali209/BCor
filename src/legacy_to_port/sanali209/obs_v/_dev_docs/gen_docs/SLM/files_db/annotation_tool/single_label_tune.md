# Hyperparameter Tuning (Basic) for Single-Label Classification (`single_label_tune.py`)

Этот скрипт, как и `singl_label_tune2.py`, использует библиотеку **Ray Tune** для автоматического **поиска и оптимизации гиперпараметров** модели классификации изображений. Он обучается на аннотациях из SLM, но представляет собой **более раннюю или упрощенную версию** по сравнению с `singl_label_tune2.py`, **не используя кэширование признаков**.

## Зависимости

*   **Основные ML/DL:** `torch`, `transformers`, `sklearn` (для `train_test_split`), `PIL (Pillow)`.
*   **Hyperparameter Tuning:** `ray`, `ray.tune`, `ray.air`.
*   **Утилиты:** `os`, `random`, `tqdm`, `loguru`, `tempfile`, `shutil`, `functools.partial`.
*   **Hugging Face Hub:** `huggingface_hub`.
*   **SLM:** `SLM.appGlue.core.Allocator`, `SLM.files_data_cache.thumbnail.ImageThumbCache`, `SLM.files_db.annotation_tool.annotation` (`AnnotationRecord`, `AnnotationJob`).
*   *(Неиспользуемый импорт: `diskcache`)*.

## Ключевые компоненты и отличия от `singl_label_tune2.py`

1.  **`ImageClassificationDataset(Dataset)` (Без кэширования)**:
    *   Стандартная реализация датасета PyTorch.
    *   **Отличие:** Не использует `diskcache`. Предобработка изображений (`feature_extractor`) выполняется **каждый раз** при вызове `__getitem__`. Это может существенно замедлить обучение, особенно при большом количестве эпох или параллельных испытаний Ray Tune.

2.  **`evaluate_model(...)`**:
    *   Функция оценки идентична версии в `singl_label_tune2.py`.

3.  **`train_model_tune(...)` (Адаптировано для Ray Tune)**:
    *   Функция обучения, вызываемая внутри каждого trial Ray Tune.
    *   Идентична версии в `singl_label_tune2.py`, использует `ray.air.session.report()` для передачи метрик и чекпоинтов в Ray Tune.

4.  **`train_tune_wrapper(config, ...)` (Обертка для Ray Tune Trial)**:
    *   Функция, запускаемая для каждого trial.
    *   **Отличия:**
        *   Создает `DataLoader` с фиксированным `batch_size=16` и `num_workers=0`.
        *   Не включает `weight_decay` в настраиваемые параметры оптимизатора.
        *   Не использует и не очищает кэш `diskcache`.

5.  **`predict_image(...)`**:
    *   Функция инференса идентична.

## Основной блок (`if __name__ == "__main__":`) (Оркестрация Ray Tune)

*   Процесс в целом схож с `singl_label_tune2.py`: инициализация SLM, предварительная загрузка данных, помещение данных в Ray Object Store, инициализация Ray, определение пространства поиска, настройка планировщика, запуск `tune.Tuner`, анализ результатов, сохранение/загрузка лучшей модели.
*   **Отличия:**
    *   **Пространство поиска (`search_space`):** Меньше параметров (только `lr` и `optimizer_type`).
    *   **Ресурсы (`tune.with_resources`):** Запрашиваются фиксированные ресурсы (`cpu=6, gpu=1`).
    *   **Имя эксперимента:** `"image_classification_tune_v2"`.
    *   **Токен HF:** Захардкожен в коде (менее безопасно, чем использование переменных окружения).
    *   **Загрузка чекпоинта:** Используется `best_checkpoint.path` напрямую (может быть менее надежно, чем `best_checkpoint.as_directory()` в `singl_label_tune2.py`).

## Вывод

`single_label_tune.py` предоставляет базовую функциональность для поиска гиперпараметров с помощью Ray Tune, интегрированную с данными SLM. Однако отсутствие кэширования признаков делает его менее эффективным по сравнению с `singl_label_tune2.py`, особенно для больших датасетов или длительных процессов тюнинга. Он может служить отправной точкой или примером интеграции с Ray Tune до внедрения оптимизаций кэширования.
