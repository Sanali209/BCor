# Duplicate File Helper (`dubFileHelper.py`)

Этот файл содержит класс `DuplicateFindHelper`, который предоставляет методы для сортировки списка изображений на основе их визуального сходства. Идея состоит в том, чтобы расположить похожие изображения рядом друг с другом в списке, что может быть полезно для выявления дубликатов или группировки схожего контента.

**Примечание:** Название файла (`dubFileHelper.py`) и класса (`DuplicateFindHelper`) предполагает поиск дубликатов, но реализованные методы (`sort_images_by_futures`, `sort_images_by_futures_base`) фактически выполняют **сортировку** изображений по сходству, а не явный поиск дубликатов.

## Зависимости

*   `numpy`: Для работы с массивами (`pip install numpy`).
*   `annoy`: Для построения индекса и поиска ближайших соседей (`pip install annoy`).
*   `tqdm`: Для отображения прогресс-баров (`pip install tqdm`).
*   `loguru`: Для логирования (`pip install loguru`).
*   `time`: Для измерения времени выполнения.
*   `SLM.vision.imagetotensor.CNN_Encoding.ImageToCNNTensor`: Используется в `sort_images_by_futures_base` для получения эмбеддингов.
*   **Неопределенные зависимости:**
    *   `GetCNNEncoding`: Используется в `sort_images_by_futures`. Этот метод не определен в классе и должен быть предоставлен извне (возможно, через наследование или инъекцию).
    *   `solve_tsp_simulated_annealing`: Используется в `sort_images_by_futures`. Это функция для решения задачи коммивояжера методом имитации отжига, которая должна быть импортирована из внешней библиотеки или определена в другом месте проекта.

## Класс `DuplicateFindHelper`

*   **Назначение:** Предоставляет методы для сортировки списка путей к изображениям (`list[str]`) на основе сходства их эмбеддингов CNN.

*   **`sort_images_by_futures(self, images: list[str]) -> list[str]`:**
    *   **Алгоритм:**
        1.  Получает эмбеддинги CNN для каждого изображения из списка `images`, используя неопределенный метод `self.GetCNNEncoding()`.
        2.  Строит индекс `AnnoyIndex` на основе полученных эмбеддингов (используя евклидово расстояние).
        3.  Вычисляет полную матрицу расстояний между всеми парами изображений в индексе.
        4.  Решает задачу коммивояжера (TSP) для этой матрицы расстояний, используя неопределенную функцию `solve_tsp_simulated_annealing` (с ограничением по времени `minets * 60` секунд). Цель TSP здесь - найти такой порядок обхода всех "городов" (изображений), чтобы суммарное расстояние было минимальным, что приводит к сортировке, где соседние элементы максимально похожи.
        5.  Возвращает список путей к изображениям в порядке, определенном решением TSP.
    *   **Зависимости:** `GetCNNEncoding`, `AnnoyIndex`, `numpy`, `tqdm`, `loguru`, `time`, `solve_tsp_simulated_annealing`.

*   **`sort_images_by_futures_base(self, images: list[str]) -> list[str]`:**
    *   **Алгоритм:** Реализует жадный алгоритм сортировки по ближайшему соседу.
        1.  Получает эмбеддинги CNN для каждого изображения, используя `ImageToCNNTensor` из `SLM.vision.imagetotensor`.
        2.  Строит индекс `AnnoyIndex` на основе эмбеддингов (евклидово расстояние).
        3.  Начинает с первого изображения в исходном списке.
        4.  Итеративно находит в оставшемся наборе изображений то, которое находится на минимальном расстоянии (в пространстве эмбеддингов) от *последнего добавленного* в отсортированный список изображения.
        5.  Добавляет найденное ближайшее изображение в отсортированный список и удаляет его из набора оставшихся.
        6.  Повторяет шаги 4-5, пока все изображения не будут отсортированы.
        7.  Возвращает отсортированный список путей к изображениям.
    *   **Зависимости:** `SLM.vision.imagetotensor.CNN_Encoding.ImageToCNNTensor`, `AnnoyIndex`, `tqdm`.
    *   **Внимание:** Последняя строка `return len(sortet1.symmetric_difference(sortet2)) == 0` в этом методе выглядит ошибочной и не соответствует логике функции. Вероятно, это остаток отладки или другого кода. Метод должен возвращать `sorted_list`.

## Пример использования (Концептуальный)

```python
# Предполагается, что класс DuplicateFindHelper расширен или используется 
# таким образом, что GetCNNEncoding и solve_tsp_simulated_annealing доступны.
# Также требуется установка annoy, numpy, tqdm, loguru и наличие ImageToCNNTensor.

from Python.SLM.vision.dubFileHelper import DuplicateFindHelper 
# ... (импорты недостающих зависимостей)

# Примерный класс, предоставляющий недостающие методы
class MyDuplicateFinder(DuplicateFindHelper):
    def __init__(self):
        # Инициализация энкодера
        from SLM.vision.imagetotensor.CNN_Encoding import ImageToCNNTensor
        self.encoder = ImageToCNNTensor() 
        
    def GetCNNEncoding(self, image_path):
        # Реализация получения эмбеддинга
        return self.encoder.get_tensor_from_path(image_path)

# Заглушка для TSP солвера (требуется реальная реализация)
def solve_tsp_simulated_annealing(distances, max_processing_time):
    # ... (логика решения TSP) ...
    num_items = len(distances)
    # Просто возвращаем исходный порядок для примера
    return list(range(num_items)), 0 

# Список путей к изображениям
image_paths = ["img1.jpg", "img2.png", "img3.jpg", "img4.jpeg", ...] 

finder = MyDuplicateFinder()

# Сортировка с использованием TSP (если solve_tsp_simulated_annealing реализован)
try:
    sorted_images_tsp = finder.sort_images_by_futures(image_paths)
    print("Sorted images (TSP approach):", sorted_images_tsp)
except NameError as e:
    print(f"TSP solver not available: {e}")
except Exception as e:
    print(f"Error during TSP sort: {e}")


# Сортировка с использованием жадного алгоритма
try:
    sorted_images_greedy = finder.sort_images_by_futures_base(image_paths)
    print("Sorted images (Greedy approach):", sorted_images_greedy)
except Exception as e:
     print(f"Error during greedy sort: {e}")

```
