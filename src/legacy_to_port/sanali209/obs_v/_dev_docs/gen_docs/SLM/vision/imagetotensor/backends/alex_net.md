# AlexNet Embedding Backend (`alex_net.py`)

Этот файл предоставляет бэкенд для генерации эмбеддингов изображений с использованием предобученной модели AlexNet из библиотеки `torchvision`. Эмбеддинги извлекаются из слоя признаков (features) модели.

## Зависимости

*   `torch`: Основная библиотека PyTorch (`pip install torch`).
*   `torchvision`: Содержит модели и трансформации для компьютерного зрения (`pip install torchvision`).
*   `PIL` (Pillow): Для работы с изображениями (`pip install Pillow`).
*   `SLM.vision.LLMBackend.LLMBackend`: Базовый класс (используется в `AlexNetLLMBackend`).
*   `SLM.vision.imagetotensor.CNN_Encoding.CNN_Encoder`: Базовый класс для энкодеров.
*   `SLM.vision.imagetotensor.CNN_Encoding.ImageToCNNTensor`: Фасад для регистрации и доступа к энкодерам.

## Класс `AlexNetLLMBackend`

*   **Наследование:** `SLM.vision.LLMBackend.LLMBackend`
*   **Назначение:** Представляет собой частичную реализацию `LLMBackend` на основе AlexNet.
*   **Атрибуты класса:**
    *   `format` (str): Имя формата ("AlexNet").
*   **Методы:**
    *   **`load(self)`:**
        *   Вызывает `super().load()`.
        *   Загружает предобученную модель `alexnet` из `torchvision.models`.
        *   **Извлекает только слои признаков** (`self.model.features`), отбрасывая классификатор.
        *   Переводит модель в режим оценки (`self.model.eval()`).
        *   Определяет шаги предобработки изображения (`self.preprocess`) с использованием `torchvision.transforms` (изменение размера до 256, центральное кадрирование до 224x224, преобразование в тензор, нормализация).
*   **Статус:** Реализован только метод `load`. Другие методы, требуемые `LLMBackend` (например, `get_image_tensor`, `get_text_tensor` и т.д.), не реализованы.

## Класс `CNN_Encoder_ImageSearch_AlexNet`

*   **Наследование:** `SLM.vision.imagetotensor.CNN_Encoding.CNN_Encoder`
*   **Назначение:** Основной класс для генерации эмбеддингов изображений с использованием AlexNet. Регистрируется в `ImageToCNNTensor`.
*   **Атрибуты класса:**
    *   `format` (str): Имя формата для регистрации ("AlexNet").
*   **Методы:**
    *   **`__init__(self)`:**
        *   Вызывает `super().__init__()`.
        *   Выполняет те же действия по загрузке модели и определению предобработки, что и `AlexNetLLMBackend.load()`.
    *   **`GetEncoding_by_path(self, image_path)`:**
        *   **Не реализован.** Возвращает `None`.
    *   **`GetEncoding_from_PilImage(self, image: Image)`:**
        1.  Конвертирует входное изображение `PIL.Image` в формат RGB.
        2.  Применяет шаги предобработки (`self.preprocess`) для получения тензора.
        3.  Добавляет измерение батча (`unsqueeze(0)`).
        4.  Выполняет прямой проход через модель (`self.model`) в режиме `torch.no_grad()`.
        5.  Удаляет измерение батча (`squeeze()`).
        6.  Преобразует выходной тензор признаков в NumPy массив (`numpy()`).
        7.  **Выравнивает (flatten)** многомерный массив признаков в одномерный вектор.
        8.  Возвращает полученный NumPy вектор (эмбеддинг).

## Регистрация бэкенда

*   Функция `module_load()` вызывается при импорте этого файла.
*   Она регистрирует класс `CNN_Encoder_ImageSearch_AlexNet` в словаре `ImageToCNNTensor.all_backends` под ключом `"AlexNet"`.
*   Это делает бэкенд AlexNet доступным через фасад `ImageToCNNTensor`.

## Пример использования (через фасад)

```python
from PIL import Image
from Python.SLM.vision.imagetotensor.CNN_Encoding import ImageToCNNTensor
# Убедитесь, что этот модуль (alex_net.py) импортирован где-то в вашем проекте, 
# чтобы бэкенд был зарегистрирован.

# Пример загрузки изображения
try:
    img = Image.open("path/to/your/image.jpg")
    
    # Получение эмбеддинга с использованием AlexNet
    embedding = ImageToCNNTensor.get_tensor_from_image(img, backend="AlexNet")
    
    if embedding is not None:
        print(f"AlexNet embedding obtained, shape: {embedding.shape}")
        # embedding - это numpy массив
    else:
        print("Failed to get AlexNet embedding.")

except FileNotFoundError:
    print("Image file not found.")
except Exception as e:
    print(f"An error occurred: {e}")

# Получение эмбеддинга по пути (если бы GetEncoding_by_path был реализован в CNN_Encoder)
# embedding_path = ImageToCNNTensor.get_tensor_from_path("path/to/your/image.jpg", backend="AlexNet")
