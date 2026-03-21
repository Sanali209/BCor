# Window Capture (`window_capture.py`)

Этот файл содержит класс `WindowCapture`, который позволяет захватывать изображение (скриншот) клиентской области окна приложения в Windows по его заголовку. Он использует библиотеку `pywin32` для взаимодействия с Windows API.

**Важно:** Этот модуль является **специфичным для Windows**.

## Зависимости

*   `numpy`: Для преобразования данных изображения в массив (`pip install numpy`).
*   `pywin32`: Для доступа к Windows API (`pip install pywin32`). Импортирует `win32gui`, `win32ui`, `win32con`.

## Класс `WindowCapture`

*   **Назначение:** Захват изображения окна по его имени.
*   **Атрибуты:**
    *   `w`, `h` (int): Ширина и высота захватываемой клиентской области окна (за вычетом рамок и заголовка).
    *   `hwnd` (int): Дескриптор (handle) окна.
    *   `cropped_x`, `cropped_y` (int): Смещение в пикселях для обрезки рамок и заголовка окна.
    *   `offset_x`, `offset_y` (int): Смещение окна на экране (координаты верхнего левого угла клиентской области).
*   **`__init__(self, window_name)`:**
    *   Находит дескриптор окна (`hwnd`) по его имени (`window_name`) с помощью `win32gui.FindWindow`. Вызывает исключение, если окно не найдено.
    *   Получает размеры окна (`win32gui.GetWindowRect`).
    *   Вычисляет размеры клиентской области (`w`, `h`), вычитая предполагаемые размеры рамок (`border_pixels = 8`) и заголовка (`titlebar_pixels = 30`).
    *   Сохраняет смещения для обрезки (`cropped_x`, `cropped_y`) и абсолютные координаты клиентской области на экране (`offset_x`, `offset_y`).
*   **`get_screenshot(self)`:**
    *   Получает контекст устройства (DC) окна (`win32gui.GetWindowDC`).
    *   Создает совместимый DC в памяти (`win32ui.CreateDCFromHandle`, `CreateCompatibleDC`).
    *   Создает совместимый битмап (`win32ui.CreateBitmap`, `CreateCompatibleBitmap`).
    *   Копирует изображение из DC окна в битмап в памяти (`cDC.BitBlt`), используя вычисленные смещения (`cropped_x`, `cropped_y`) и размеры (`w`, `h`).
    *   Получает биты битмапа (`dataBitMap.GetBitmapBits(True)`).
    *   Преобразует сырые данные в NumPy массив (`np.fromstring`), придавая ему форму `(h, w, 4)` (BGRA).
    *   Освобождает ресурсы DC и битмапа (`DeleteDC`, `ReleaseDC`, `DeleteObject`).
    *   **Удаляет альфа-канал**, оставляя массив в формате BGR (`img = img[...,:3]`).
    *   Делает массив **C-contiguous** (`np.ascontiguousarray(img)`) для совместимости с некоторыми функциями OpenCV.
    *   Возвращает захваченное изображение в виде NumPy массива (BGR, uint8).
*   **`list_window_names(self)`:**
    *   Вспомогательный метод для вывода списка видимых окон и их дескрипторов (hex). Использует `win32gui.EnumWindows`. Полезен для определения точного имени окна для передачи в конструктор.
*   **`get_screen_position(self, pos)`:**
    *   Преобразует координаты `pos = (x, y)` из системы координат захваченного изображения (относительно верхнего левого угла клиентской области) в абсолютные координаты на экране.
    *   **Предупреждение:** Возвращает неверные координаты, если окно было перемещено после создания экземпляра `WindowCapture`, так как `offset_x` и `offset_y` вычисляются только в `__init__`.

## Пример использования

```python
import cv2 # Для отображения (pip install opencv-python)
import time
from Python.SLM.vision.window_capture import WindowCapture

# Укажите точное имя окна (можно найти с помощью list_window_names)
# window_name = "Calculator" 
window_name = "Untitled - Notepad" # Пример

try:
    wincap = WindowCapture(window_name)

    # Пример вывода списка окон
    # print("Visible windows:")
    # wincap.list_window_names() 
    
    print(f"Capturing window: '{window_name}' (HWND: {wincap.hwnd})")
    print(f"Client area size: {wincap.w}x{wincap.h}")
    print(f"Screen offset: ({wincap.offset_x}, {wincap.offset_y})")

    loop_time = time.time()
    while(True):
        # Получить скриншот
        screenshot = wincap.get_screenshot()

        # Отобразить скриншот (используя OpenCV)
        cv2.imshow('Window Capture', screenshot)

        # Вывести FPS
        print('FPS {}'.format(1 / (time.time() - loop_time)))
        loop_time = time.time()

        # Нажмите 'q' для выхода
        if cv2.waitKey(1) == ord('q'):
            cv2.destroyAllWindows()
            break

except Exception as e:
    print(f"Error: {e}")

print('Done.')
```
