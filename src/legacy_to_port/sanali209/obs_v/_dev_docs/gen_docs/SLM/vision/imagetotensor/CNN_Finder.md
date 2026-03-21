# CNN Finder (`CNN_Finder.py`)

Этот файл определяет класс `CNN_Dub_Finder`, предназначенный для поиска визуально похожих изображений (потенциальных дубликатов) в наборе данных. Он использует эмбеддинги, полученные с помощью CNN (по умолчанию MobileNetV3 Small), кэшированные с помощью `Embeddings_cache`, и строит индекс `Annoy` для эффективного поиска ближайших соседей.

**Примечание:** В коде есть TODO-заметки, указывающие на возможное удаление зависимостей от `dask` и `imagededup` (хотя последняя не импортируется явно) и необходимость унификации интерфейсов.

## Зависимости

*   `annoy`: Для построения индекса и поиска ближайших соседей (`pip install annoy`).
*   `tqdm`: Для отображения прогресс-баров (`pip install tqdm`).
*   `dask.distributed`: Используется в методе `_BuildIndex_dusk` (`pip install dask distributed`). *Помечен как потенциально удаляемый.*
*   `SLM.files_data_cache.tensor.Embeddings_cache`: Для доступа к кэшированным эмбеддингам изображений.
*   `SLM.iterable.bach_builder.BatchBuilder`: Используется в `_BuildIndex_dusk`.
*   `concurrent.futures.ThreadPoolExecutor`: Для параллельного выполнения поиска.
*   `SLM.vision.imagetotensor.backends.mobile_net_v3.CNN_encoder_ModileNetv3_Small`: Для получения имени формата тензора по умолчанию.

## Вспомогательные классы данных

*   **`FindResultItem`**:
    *   Простой класс для хранения результата поиска одного похожего изображения.
    *   Атрибуты:
        *   `path` (str): Путь к найденному похожему изображению.
        *   `distance` (float): Расстояние (согласно метрике Annoy) между исходным и найденным изображением.
*   **`FindResultGroup`**:
    *   Класс для группировки результатов поиска для одного исходного изображения.
    *   Атрибуты:
        *   `path` (str): Путь к исходному изображению, для которого выполнялся поиск.
        *   `results` (list[`FindResultItem`]): Список найденных похожих изображений.
        *   `none_tensor` (bool): Флаг, указывающий, удалось ли получить эмбеддинг для исходного изображения (`True`, если не удалось).

## Класс `CNN_Dub_Finder`

*   **Назначение:** Основной класс для построения индекса эмбеддингов и поиска похожих изображений.
*   **Атрибуты:**
    *   `path_to_index` (dict): Словарь для отображения пути к файлу на его индекс в Annoy.
    *   `name` (str): Имя класса ("CNN_Encoded_Top_Finder").
    *   `encodingIndex` (dict): *Не используется в текущей реализации.*
    *   `annoy_index` (AnnoyIndex): Экземпляр индекса Annoy.
    *   `tensor_format` (str): Имя формата тензора (эмбеддинга), используемого для поиска. По умолчанию берется из `CNN_encoder_ModileNetv3_Small.format`.
    *   `metric` (str): Метрика расстояния для Annoy (по умолчанию "angular"). Допустимые значения: "angular", "euclidean", "manhattan", "hamming", "dot".
    *   `DbImageObjectItems` (list): Список путей к изображениям, соответствующий порядку добавления в индекс Annoy. Используется для преобразования индекса обратно в путь.
    *   `dub_find_neighbors` (int): Количество ближайших соседей, запрашиваемых у Annoy при поиске (по умолчанию 10).
    *   `threshold_map` (dict): Словарь с пороговыми значениями расстояний по умолчанию для разных форматов тензоров и метрик.
    *   `tensor_length` (int): Размерность (длина) используемых векторов эмбеддингов.
*   **Методы:**
    *   **`_BuildIndex_dusk(self, image_paths: list[str])`:**
        *   *Экспериментальный/устаревший метод.* Пытается построить индекс Annoy, используя `dask` для параллельного получения эмбеддингов. В комментариях указано, что это может быть неэффективно.
    *   **`BuildIndex(self, image_paths: list[str])`:**
        *   Основной метод для построения индекса Annoy.
        *   Сохраняет `image_paths` в `self.DbImageObjectItems`.
        *   Инициализирует `self.annoy_index` с нужной размерностью тензора (полученной из первого изображения) и метрикой.
        *   Итерирует по `image_paths`:
            *   Получает эмбеддинг для каждого изображения из `Embeddings_cache`, используя `self.tensor_format`.
            *   Обрабатывает ошибки (отсутствие тензора, неверная длина).
            *   Добавляет эмбеддинг в `self.annoy_index` с соответствующим индексом.
            *   Заполняет словарь `self.path_to_index`.
        *   Строит индекс Annoy (`self.annoy_index.build(100)`).
    *   **`FindTop(self, find_item_path: str, top_count=10, distance_threshold=0) -> FindResultGroup`:**
        *   Находит `top_count` наиболее похожих изображений для заданного `find_item_path`.
        *   Получает эмбеддинг для `find_item_path` из `Embeddings_cache`. Если эмбеддинг отсутствует, возвращает `FindResultGroup` с `none_tensor=True`.
        *   Запрашивает у `self.annoy_index` `top_count + 1` ближайших соседей по вектору (чтобы учесть возможное нахождение самого себя).
        *   Итерирует по результатам:
            *   Пропускает само изображение (`find_item_path`).
            *   Если расстояние меньше или равно `distance_threshold` (или `distance_threshold == 0`), создает `FindResultItem` и добавляет его в `FindResultGroup.results`.
        *   Возвращает `FindResultGroup`.
    *   **`FindDubs(self, image_paths: list[str], distance_threshold=0) -> list[FindResultGroup]`:**
        *   Основной метод для запуска поиска дубликатов/похожих изображений во всем списке `image_paths`.
        *   Позволяет установить `distance_threshold`. Если `distance_threshold == -1`, пытается использовать значение по умолчанию из `self.threshold_map`.
        *   Вызывает `self.BuildIndex(image_paths)` для построения индекса.
        *   Использует `ThreadPoolExecutor` для параллельного вызова `self.FindTop` для каждого изображения в `image_paths`.
        *   Собирает результаты (`FindResultGroup`) только для тех изображений, у которых нашлись соседи в пределах порога.
        *   Возвращает список `FindResultGroup`.

## Пример использования

```python
from Python.SLM.vision.imagetotensor.CNN_Finder import CNN_Dub_Finder
# Убедитесь, что Embeddings_cache настроен и содержит эмбеддинги 
# для формата 'modilenetv3_small_1_0_224_tf' (или какой используется)

image_paths = ["img1.jpg", "img2.png", "img_similar_to_1.jpg", "img3.jpg", ...] 

finder = CNN_Dub_Finder()
# Можно изменить метрику или формат тензора перед поиском, если нужно
# finder.metric = "euclidean"
# finder.tensor_format = "clip_ViT_B_32_tensor" # Если есть кэш для CLIP

# Установить порог расстояния (например, для angular)
# Меньшее значение означает большее сходство
distance_threshold = 0.1 

# Или использовать порог по умолчанию (-1)
# distance_threshold = -1 

print(f"Finding duplicates with threshold: {distance_threshold} ({finder.metric})")
results = finder.FindDubs(image_paths, distance_threshold=distance_threshold)

print(f"Found {len(results)} images with potential duplicates:")
for group in results:
    print(f"  Image: {group.path}")
    for item in group.results:
        print(f"    - Similar: {item.path} (Distance: {item.distance:.4f})")
