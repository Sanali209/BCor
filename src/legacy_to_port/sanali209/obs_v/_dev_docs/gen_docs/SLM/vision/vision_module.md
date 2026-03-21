# Vision Module Integration (`vision_module.py`)

Этот файл определяет класс `VisionModule`, который служит точкой входа для интеграции функциональности компьютерного зрения в общую архитектуру приложения SLM (`SLM.appGlue.core`).

## Класс `VisionModule`

*   **Наследование:** `SLM.appGlue.core.Module`
*   **`__init__(self)`:**
    *   Вызывает конструктор родительского класса `Module` с именем `"VisionModule"`.
*   **`init(self)`:**
    *   Этот метод вызывается при загрузке модуля через `appGlue`.
    *   **Инициализация и регистрация детекторов объектов:**
        1.  Импортирует необходимые классы:
            *   `ObjectDetectorProvider` из `SLM.vision.objectdetectors.object_detect`.
            *   Конкретные реализации детекторов: `object_detector_groundDino`, `FaceDetectorMTCNN`, `FaceDetectorYolov8HF`.
        2.  Создает экземпляр `ObjectDetectorProvider`.
        3.  Регистрирует этот провайдер в глобальном `Allocator` (`Allocator.res.register(object_detector_provider)`), делая его доступным для других частей приложения.
        4.  Создает и регистрирует экземпляры конкретных бэкендов детекторов в провайдере:
            *   `object_detector_groundDino()`
            *   `FaceDetectorMTCNN()`
            *   `FaceDetectorYolov8HF()`

## Назначение

Основная задача этого модуля при инициализации - подготовить и сделать доступным сервис для обнаружения объектов (`ObjectDetectorProvider`) с набором предварительно настроенных моделей (бэкендов). Другие части приложения могут затем получить доступ к этому провайдеру через `Allocator` и использовать его для детекции объектов на изображениях, выбирая нужный бэкенд.

## Связанные концепции

*   [SLM Application Glue (`appGlue`)](appGlue%20index.md) *(Placeholder)*
*   [Allocator (`SLM.Allocator`)](../Allocator.md) *(Placeholder - Need to document Allocator)*
*   [Object Detectors Module](objectdetectors/index.md)
*   [Architecture](../architecture.md)
