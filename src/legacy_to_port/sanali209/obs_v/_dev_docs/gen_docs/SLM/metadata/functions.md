# Metadata Functions (`functions.py`)

Этот файл содержит набор функций для чтения и записи метаданных изображений, используя библиотеки `iptcinfo3` и `PIL`.

## Зависимости

*   `iptcinfo3`: Для работы с IPTC метаданными (`pip install iptcinfo3`).
*   `Pillow` (PIL): Для работы с изображениями и их метаданными (`pip install Pillow`).

## Функции

*   **`IPTC_set_keywords(filename, keywords)`:**
    *   **Назначение:** Устанавливает или перезаписывает поле 'keywords' (ключевые слова) в IPTC метаданных указанного файла изображения.
    *   **Параметры:**
        *   `filename` (str): Путь к файлу изображения.
        *   `keywords` (list): Список строк, представляющих ключевые слова.
    *   **Действие:** Создает объект `IPTCInfo`, устанавливает значение для ключа `'keywords'` и сохраняет изменения в файле.

*   **`IPTC_get_keywords(filename)`:**
    *   **Назначение:** Читает поле 'keywords' из IPTC метаданных указанного файла изображения.
    *   **Параметры:**
        *   `filename` (str): Путь к файлу изображения.
    *   **Возвращает:** Список ключевых слов (list) или `None`, если поле отсутствует.

*   **`pil_read_metadata(filename)`:**
    *   **Назначение:** Читает общую информацию (метаданные), доступную через атрибут `info` объекта `Image` из библиотеки Pillow. Содержимое этого словаря зависит от формата файла.
    *   **Параметры:**
        *   `filename` (str): Путь к файлу изображения.
    *   **Возвращает:** Словарь (`dict`) с метаданными.

*   **`pil_read_xmp(filename)`:**
    *   **Назначение:** Читает XMP метаданные из файла изображения с помощью метода `getxmp()` объекта `Image` из библиотеки Pillow.
    *   **Параметры:**
        *   `filename` (str): Путь к файлу изображения.
    *   **Возвращает:** Словарь (`dict`), содержащий XMP данные, если они присутствуют.

## Пример использования

```python
from Python.SLM.metadata.functions import IPTC_set_keywords, IPTC_get_keywords, pil_read_metadata, pil_read_xmp

image_path = "path/to/your/image.jpg" # Убедитесь, что файл существует

# Установка IPTC ключевых слов
try:
    IPTC_set_keywords(image_path, ["nature", "landscape", "sunset"])
    print("IPTC keywords set successfully.")
except Exception as e:
    print(f"Error setting IPTC keywords: {e}")

# Чтение IPTC ключевых слов
try:
    keywords = IPTC_get_keywords(image_path)
    print(f"IPTC Keywords: {keywords}")
except Exception as e:
    print(f"Error getting IPTC keywords: {e}")

# Чтение общих метаданных PIL
try:
    metadata = pil_read_metadata(image_path)
    print(f"PIL Metadata Info: {metadata}")
except Exception as e:
    print(f"Error reading PIL metadata: {e}")

# Чтение XMP данных (если есть)
try:
    xmp_data = pil_read_xmp(image_path)
    if xmp_data:
        print(f"XMP Data found.") 
        # print(xmp_data) # Раскомментируйте, чтобы увидеть содержимое
    else:
        print("No XMP data found.")
except Exception as e:
    print(f"Error reading XMP data: {e}")
