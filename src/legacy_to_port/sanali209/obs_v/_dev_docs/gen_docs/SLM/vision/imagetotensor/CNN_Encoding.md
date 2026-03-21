# CNN Encoding (`CNN_Encoding.py`)

Этот файл определяет базовый класс `CNN_Encoder` и класс-фасад `ImageToCNNTensor` для управления и использования различных моделей (бэкендов) с целью преобразования изображений в векторные представления (эмбеддинги/тензоры).

## Зависимости

*   `PIL` (Pillow): Для работы с изображениями (`pip install Pillow`).
*   `SLM.files_data_cache.pool.PILPool`: Для эффективной загрузки изображений PIL.

## Класс `CNN_Encoder`

*   **Назначение:** Служит базовым классом (интерфейсом) для всех конкретных реализаций моделей, генерирующих эмбеддинги изображений. Конкретные бэкенды (например, MobileNet, CLIP) должны наследоваться от этого класса.
*   **Атрибуты:**
    *   `vector_size` (int): Ожидаемый размер (размерность) вектора эмбеддинга, генерируемого этим энкодером. Должен быть переопределен в подклассах.
    *   `name` (str): Имя энкодера (по умолчанию "CNN_Encoder"). Должно быть переопределено.
*   **Методы (Предназначены для переопределения):**
    *   **`GetEncoding_by_path(self, image_path)`:**
        *   Принимает путь к файлу изображения (`image_path`).
        *   Должен загрузить изображение и вернуть его эмбеддинг.
        *   Базовая реализация возвращает `None`.
    *   **`GetEncoding_from_PilImage(self, image: Image)`:**
        *   Принимает объект `PIL.Image`.
        *   Должен обработать изображение и вернуть его эмбеддинг.
        *   Базовая реализация возвращает `None`.

## Класс `ImageToCNNTensor`

*   **Назначение:** Действует как фасад и менеджер для различных бэкендов `CNN_Encoder`. Предоставляет статические методы для получения эмбеддингов изображений, управляя жизненным циклом (ленивая инициализация) бэкендов.
*   **Атрибуты класса:**
    *   `all_backends` (dict): Словарь, регистрирующий доступные классы бэкендов. Ключ - строка с именем бэкенда (например, "ModileNetV3Small"), значение - сам класс бэкенда (например, `MobileNetV3SmallEncoder`). *Предполагается, что этот словарь заполняется где-то извне, например, при импорте модулей бэкендов.*
    *   `run_backends` (dict): Словарь для хранения уже созданных экземпляров бэкендов (ленивая инициализация). Ключ - имя бэкенда, значение - экземпляр бэкенда.
*   **Статические методы:**
    *   **`get_tensor_from_path(image_path: str, backend: str = 'ModileNetV3Small') -> any`:**
        1.  Проверяет, зарегистрирован ли запрошенный `backend` в `all_backends`. Если нет, возвращает строку "no backend".
        2.  Проверяет, был ли экземпляр этого бэкенда уже создан (`run_backends`). Если нет, создает его, вызывая конструктор класса из `all_backends`, и сохраняет в `run_backends`.
        3.  Получает экземпляр бэкенда.
        4.  Загружает изображение по `image_path` с помощью `PILPool.get_pil_image`. Обрабатывает возможные ошибки загрузки, возвращая `None`.
        5.  Вызывает метод `GetEncoding_from_PilImage` экземпляра бэкенда для получения эмбеддинга.
        6.  Возвращает полученный эмбеддинг (или `None` при ошибке загрузки).
    *   **`get_tensor_from_image(image: Image, backend: str = "ModileNetV3Small") -> any`:**
        1.  Аналогично `get_tensor_from_path`, получает или создает экземпляр запрошенного бэкенда.
        2.  Вызывает метод `GetEncoding_from_PilImage` экземпляра бэкенда, передавая ему предоставленный объект `PIL.Image`.
        3.  Возвращает полученный эмбеддинг.
    *   **`get_all_backends() -> list[str]`:**
        *   Возвращает список имен всех зарегистрированных бэкендов (ключи словаря `all_backends`).

## Принцип работы и использование

1.  **Регистрация бэкендов:** Различные модули, реализующие конкретные энкодеры (например, `MobileNetEncoder` наследующий `CNN_Encoder`), должны при импорте добавлять свой класс в словарь `ImageToCNNTensor.all_backends`.
    ```python
    # Пример в файле бэкенда (например, mobile_net_encoder.py)
    from .CNN_Encoding import CNN_Encoder, ImageToCNNTensor
    
    class MobileNetEncoder(CNN_Encoder):
        vector_size = 576 # Пример
        name = "ModileNetV3Small" # Имя для регистрации
        
        def __init__(self):
            super().__init__()
            # Загрузка модели и т.д.
            print(f"Initializing {self.name} backend...")
            # self.model = ... 
            
        def GetEncoding_from_PilImage(self, image: Image):
            # Предобработка изображения
            # Получение эмбеддинга с помощью self.model
            # Возврат эмбеддинга (например, как numpy array или list)
            # ... реализация ...
            pass 
            
    # Регистрация бэкенда при импорте модуля
    ImageToCNNTensor.all_backends[MobileNetEncoder.name] = MobileNetEncoder
    ```
2.  **Получение эмбеддинга:** Другие части приложения могут использовать статические методы `ImageToCNNTensor` для получения эмбеддингов.
    ```python
    from Python.SLM.vision.imagetotensor.CNN_Encoding import ImageToCNNTensor
    # Важно: Убедитесь, что модули с нужными бэкендами были импортированы где-то ранее
    
    image_path = "path/to/image.jpg"
    
    # Использовать бэкенд по умолчанию ('ModileNetV3Small')
    embedding_default = ImageToCNNTensor.get_tensor_from_path(image_path)
    
    # Использовать другой зарегистрированный бэкенд
    # embedding_clip = ImageToCNNTensor.get_tensor_from_path(image_path, backend='CLIP') 
    
    if embedding_default is not None and isinstance(embedding_default, str) and embedding_default == "no backend":
        print(f"Backend 'ModileNetV3Small' not registered.")
    elif embedding_default is not None:
        print(f"Got embedding (default backend), size: {len(embedding_default)}")
    else:
        print(f"Failed to get embedding for {image_path}")
        
    # Получить список доступных бэкендов
    available_backends = ImageToCNNTensor.get_all_backends()
    print(f"Available backends: {list(available_backends)}")
    ```

Этот дизайн позволяет легко добавлять новые модели для генерации эмбеддингов и использовать их через единый интерфейс, не заботясь о деталях загрузки и управления экземплярами моделей.
