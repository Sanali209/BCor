# LLM Backend (`LLMBackend.py`)

Этот файл определяет абстрактный базовый класс `LLMBackend`, который служит интерфейсом для различных бэкендов больших языковых моделей (LLM), способных выполнять мультимодальные задачи (обработка изображений и текста). Он также включает базовую реализацию кэширования результатов с использованием `diskcache`.

## Зависимости

*   `PIL` (Pillow): Для работы с изображениями (`pip install Pillow`).
*   `diskcache`: Для кэширования на диске (`pip install diskcache`).
*   `SLM.Allocator`: Для доступа к конфигурации.
*   `SLM.appGlue.core`: Содержит базовые классы `ServiceBackend` и `BackendProvider`.
*   `SLM.files_data_cache`: Модули для кэширования данных изображений (`ImageDataCacheManager`, `PILPool`, `ImageThumbCache`).
*   `hashlib`, `os`, `abc`.

## Класс `LLMBackend`

*   **Наследование:** `SLM.appGlue.core.ServiceBackend`, `abc.ABC` (неявно через `ServiceBackend`, если он ABC).
*   **Назначение:** Определяет общий интерфейс и базовую функциональность для бэкендов мультимодальных LLM. Конкретные реализации должны наследоваться от этого класса и реализовывать абстрактные методы.
*   **Атрибуты класса:**
    *   `format` (str): Идентификатор формата бэкенда ("LLMBackend").
    *   `vector_size` (int): Размерность векторов, если бэкенд их генерирует (по умолчанию 0).
    *   `version` (str): Версия бэкенда (используется для инвалидации кэша).
    *   `threshold_default` (dict): Пороговые значения по умолчанию для различных метрик расстояния.
    *   `image_datacache_manager`: Экземпляр `ImageDataCacheManager`.
    *   `image_tumb_manager`: Экземпляр `ImageThumbCache`.
*   **`__init__(self, *args, **kwargs)`:**
    *   Инициализирует `self.index` как `None`.
*   **`get_curent_version(self)`:** Возвращает текущую версию бэкенда (`self.version`).
*   **`load(self)`:**
    *   Вызывается для инициализации бэкенда.
    *   Создает директорию для кэша, если она не существует (`llm_data` и `embeddings/LLMBackend` внутри пути, указанного в `Allocator.config.fileDataManager.path`).
    *   Инициализирует `diskcache.Index` (`self.index`) для хранения кэшированных данных.
    *   Проверяет версию в кэше; если она отличается от текущей `self.version`, очищает кэш и записывает новую версию.
    *   Получает экземпляры `ImageDataCacheManager` и `ImageThumbCache`.
*   **`get_PIL_image_tumb_and_md5(self, image_path: str, thumb_name="medium")`:**
    *   Вспомогательный метод для получения миниатюры изображения (`PIL.Image`) и его MD5 хэша по пути к файлу. Использует `ImageThumbCache` и `ImageDataCacheManager`.
*   **`kwargs_to_key(self, **kwargs)`:**
    *   Создает строку-ключ (MD5 хэш) из переданных именованных аргументов для использования в кэшировании.
*   **`set_cached(self, key: str, data)`:** Записывает данные в кэш `diskcache` по ключу.
*   **`get_cached(self, key)`:** Читает данные из кэша `diskcache` по ключу.
*   **`cache(self, key, data=None, **kwargs)`:**
    *   Универсальный метод для работы с кэшем.
    *   Генерирует дополнительный ключ на основе `kwargs`.
    *   Если `data` не `None`, записывает данные в кэш (`set_cached`).
    *   Если `data` равно `None`, пытается прочитать данные из кэша (`get_cached`).
*   **Абстрактные методы (`@abc.abstractmethod` или просто `raise NotImplementedError`):**
    *   `get_image_tensor(self, image: Image)`: Получить векторное представление изображения.
    *   `get_text_tensor(self, text: str)`: Получить векторное представление текста.
    *   `get_text_mach(self, Image: Image, texts: list[str]) -> (str, list[float])`: Найти наиболее подходящий текст из списка `texts` для данного изображения (например, CLIP zero-shot classification). Возвращает лучший текст и оценки для всех текстов.
    *   `get_image_classification(self, Image: Image, single_label: bool = True) -> list`: Выполнить классификацию изображения.
    *   `get_image_description(self, image: Image) -> str`: Сгенерировать текстовое описание изображения (image captioning).
    *   `get_image_qa(self, image: Image)`: Ответить на вопросы по изображению (Visual Question Answering - VQA). *Сигнатура неполная, должен принимать и вопрос.*
    *   `get_image_detection(self, image: Image) -> list`: Обнаружить объекты на изображении.
    *   `get_image_data(self, image: Image)`: Извлечь структурированные данные из изображения (например, OCR).
    *   `get_image_data_from_path(self, image_path: str)`: То же, что `get_image_data`, но принимает путь к файлу.
    *   `text_inference(self, question: str) -> str`: Выполнить текстовый вывод (ответ на вопрос, генерация текста).
    *   `multimodal_inference(self, image: Image, question: str) -> str`: Выполнить мультимодальный вывод (ответ на вопрос по изображению).
    *   `generate_image(self, text: str) -> Image`: Сгенерировать изображение по текстовому описанию.

## Класс `LLMBackendProvider`

*   **Наследование:** `SLM.appGlue.core.BackendProvider`
*   **Назначение:** Служит провайдером для различных реализаций `LLMBackend` в рамках системы `appGlue`. Позволяет регистрировать и получать доступ к конкретным бэкендам LLM.
*   **Атрибуты класса:**
    *   `name` (str): Имя провайдера ("LLMBackendProvider").

## Использование

Класс `LLMBackend` не используется напрямую. Вместо этого создаются его конкретные подклассы (например, `CLIPBackend`, `BLIPBackend`, `GPT4VBackend`), которые реализуют абстрактные методы, используя соответствующие модели и API. Экземпляры этих подклассов затем регистрируются в `LLMBackendProvider`, который, в свою очередь, регистрируется в `Allocator`, делая бэкенды доступными для других частей приложения.
