# CNN Helper (`cnnhelper.py`)

Этот файл содержит класс `CNN_Helper` с набором статических и классовых методов, предоставляющих утилиты для работы с изображениями (PIL, OpenCV), NumPy массивами и вычислениями расстояний между векторами, часто используемыми в задачах компьютерного зрения и работы с эмбеддингами.

## Зависимости

*   `numpy`: Для работы с массивами (`pip install numpy`).
*   `Pillow` (PIL): Для работы с изображениями (`pip install Pillow`).
*   `opencv-python` (cv2): Требуется для метода `PilImage_to_OpenCV_image` (`pip install opencv-python`).

## Класс `CNN_Helper`

Содержит только статические (`@staticmethod`) и классовые (`@classmethod`) методы.

### Методы конвертации типов

*   **`NPArrayToList(array: np.array) -> list`**:
    *   Преобразует NumPy массив (`np.array`) в стандартный список Python (`list`).
*   **`ListToNPArray(data_list: list) -> np.array`**:
    *   Преобразует список Python (`list`) в NumPy массив (`np.array`).
*   **`DF_image_toPilImage(image)`**:
    *   Преобразует изображение в формате "DF_image" (предположительно NumPy массив float32 в диапазоне [0, 1]) в объект `PIL.Image`.
    *   Масштабирует значения к [0, 255].
    *   *Примечание: Закомментированная строка `image = image[:, :, ::-1]` предполагает, что формат "DF_image" может быть BGR, но в текущей реализации порядок каналов не меняется.*
*   **`PilImage_to_DF_image(pil_image)`**:
    *   Преобразует объект `PIL.Image` в формат "DF_image" (NumPy массив float32 в диапазоне [0, 1]).
*   **`PilImage_to_OpenCV_image(cls, image)`**:
    *   Преобразует объект `PIL.Image` (предположительно RGB) в формат OpenCV (NumPy массив uint8, BGR).

### Методы вычисления расстояний и нормализации

*   **`findCosineDistance(source_representation, test_representation)`**:
    *   Вычисляет косинусное расстояние между двумя векторами (`source_representation` и `test_representation`).
    *   Входные данные могут быть NumPy массивами.
    *   Возвращает скалярное значение расстояния (1 - косинусное сходство).
*   **`findEuclideanDistance(source_representation, test_representation)`**:
    *   Вычисляет евклидово расстояние между двумя векторами.
    *   Автоматически преобразует входные списки Python в NumPy массивы при необходимости.
    *   Возвращает скалярное значение расстояния.
*   **`l2_normalize(x)`**:
    *   Нормализует входной вектор `x` с использованием L2-нормы (деление каждого элемента на корень из суммы квадратов всех элементов).
    *   Возвращает нормализованный NumPy массив.

### Методы обработки изображений

*   **`image_resize(cls, image, target_size)`**:
    *   Изменяет размер объекта `PIL.Image` до `target_size` (кортеж `(width, height)`).
    *   Использует `Image.BOX` для увеличения изображения (если оно меньше `target_size`).
    *   Использует `Image.ANTIALIAS` (может быть устаревшим, современные версии Pillow используют `Image.Resampling.LANCZOS` или `Image.Resampling.BILINEAR`) для уменьшения изображения.
    *   Возвращает измененный объект `PIL.Image`.

## Пример использования

```python
import numpy as np
from PIL import Image
from Python.SLM.vision.cnnhelper import CNN_Helper

# Пример векторов
vec1 = np.array([1.0, 0.5, -0.2])
vec2 = np.array([0.8, 0.6, 0.1])
vec1_list = vec1.tolist()

# Конвертация
vec1_np = CNN_Helper.ListToNPArray(vec1_list)
print(f"List to NP: {vec1_np}")

# Нормализация
norm_vec1 = CNN_Helper.l2_normalize(vec1)
norm_vec2 = CNN_Helper.l2_normalize(vec2)
print(f"Normalized Vec1: {norm_vec1}")

# Расстояния
cosine_dist = CNN_Helper.findCosineDistance(norm_vec1, norm_vec2)
euclidean_dist = CNN_Helper.findEuclideanDistance(vec1, vec2)
print(f"Cosine Distance (normalized): {cosine_dist:.4f}")
print(f"Euclidean Distance (original): {euclidean_dist:.4f}")

# Работа с изображениями (требуется Pillow)
try:
    # Создание простого изображения
    img_array = np.random.randint(0, 256, (100, 150, 3), dtype=np.uint8)
    pil_image = Image.fromarray(img_array)
    print(f"Original PIL image size: {pil_image.size}")

    # Изменение размера
    resized_image = CNN_Helper.image_resize(pil_image, (50, 50))
    print(f"Resized PIL image size: {resized_image.size}")

    # Конвертация в "DF_image" и обратно
    df_image = CNN_Helper.PilImage_to_DF_image(resized_image)
    print(f"DF image shape: {df_image.shape}, dtype: {df_image.dtype}, range: [{df_image.min()}, {df_image.max()}]")
    pil_image_restored = CNN_Helper.DF_image_toPilImage(df_image)
    print(f"Restored PIL image size: {pil_image_restored.size}")

    # Конвертация в OpenCV (требуется opencv-python)
    # ocv_image = CNN_Helper.PilImage_to_OpenCV_image(pil_image)
    # print(f"OpenCV image shape: {ocv_image.shape}")

except ImportError as e:
    print(f"PIL or OpenCV might not be installed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")

```
