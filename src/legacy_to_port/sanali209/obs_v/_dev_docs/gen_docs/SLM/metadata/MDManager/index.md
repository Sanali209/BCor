# Metadata Manager (`mdmanager.py`)

Этот файл определяет основной класс `MDManager` и его бэкенды для взаимодействия с метаданными файлов, преимущественно используя внешний инструмент `exiftool`.

## Зависимости

*   `pyexiftool`: Python-обертка для `exiftool` (`pip install pyexiftool`). Используется в `MDMManagerBackend`.
*   `exiftool`: Внешний исполняемый файл (`exiftool.exe`), который должен находиться в директории `Python/SLM/`.
*   `loguru`: Для логирования (`pip install loguru`).
*   `SLM`: Для доступа к пути `exiftool.exe`.

## Класс `MDManager`

*   **Назначение:** Предоставляет высокоуровневый интерфейс для чтения и записи метаданных конкретного файла.
*   **`__init__(self, path)`:**
    *   Принимает путь к файлу (`path`).
    *   Проверяет наличие `pyexiftool` (`exiftool_exists`).
    *   Инициализирует соответствующий бэкенд (`MDMManagerBackend` если `pyexiftool` доступен, иначе `None`). *Примечание: `MDMManagerColabBackend` не используется в конструкторе по умолчанию.*
    *   Хранит путь к файлу (`self.path`) и словарь для метаданных (`self.metadata`).
*   **`Read(self)`:**
    *   Вызывает метод бэкенда (`get_image_all_metadata`) для получения всех метаданных.
    *   Форматирует метаданные (в текущей реализации `formate_meta` ничего не делает).
    *   Сохраняет первый элемент результата (предполагается, что `get_metadata` возвращает список словарей) в `self.metadata`.
    *   Обрабатывает ошибки чтения.
    *   Возвращает `self.metadata` или `None` в случае ошибки.
*   **`Save(self)`:**
    *   Обновляет поле `XMP:ModifyDate` текущим временем.
    *   Вызывает метод бэкенда (`set_image_all_metadata`) для записи `self.metadata` в файл.
    *   Возвращает `True` в случае успеха, `False` при ошибке.
*   **`Clear(self)`:** Очищает `self.metadata`.
*   **`CleanUp(self)`:** Заглушка (ничего не делает).
*   **`is_meta_modified(self)`:** Проверяет, было ли поле `XMP:ModifyDate` изменено с момента последнего сохранения (сравнивает с текущим временем в формате `time_stamp_format`). *Примечание: Логика может быть неточной, так как сравнивает с текущим временем, а не с временем последнего чтения/сохранения.*

## Класс `MDMManagerBackend`

*   **Назначение:** Реализация бэкенда для `MDManager`, использующая библиотеку `pyexiftool`.
*   **`__init__(self)`:** Определяет путь к `exiftool.exe` и список кодировок для отката (`fall_buck_enc`).
*   **`formate_meta(self, meta)`:** Заглушка, возвращает метаданные без изменений.
*   **`get_image_all_metadata(self, path)`:** Обертка для `get_meta`.
*   **`get_meta(self, path, encoding=None, fall_back_enc=[])`:**
    *   Использует `exiftool.ExifToolHelper` для вызова `exiftool`.
    *   Пытается прочитать метаданные с указанной кодировкой (`encoding`).
    *   В случае ошибки декодирования рекурсивно пытается прочитать с кодировками из `fall_back_enc`.
    *   Логирует ошибки.
    *   Возвращает список словарей с метаданными или список с одним словарем, содержащим ошибку.
*   **`set_image_all_metadata(self, filepath, metadata)`:**
    *   Использует `exiftool.ExifToolHelper` для вызова `exiftool`.
    *   Вызывает `et.set_tags()` для записи метаданных.
    *   Проверяет результат выполнения `exiftool`.
    *   Удаляет временный файл `_original`, создаваемый `exiftool`.
    *   Логирует ошибки.
    *   Возвращает `True` в случае успеха, `False` при ошибке.
*   **`del_tag(self, filepath, tagkey)`:**
    *   Использует `exiftool.ExifToolHelper` для вызова `exiftool`.
    *   Выполняет команду `exiftool` для удаления тега (`-TAG=`).
    *   Удаляет временный файл `_original`.
    *   Возвращает результат выполнения команды `exiftool` или `False` при ошибке.

## Класс `MDMManagerColabBackend`

*   **Назначение:** Альтернативная реализация бэкенда, предназначенная для сред типа Google Colab, где `pyexiftool` может быть недоступен или неудобен. Использует прямые вызовы `exiftool` через `subprocess`.
*   **`__init__(self)`:** Заглушка (содержит закомментированную команду для установки `exiftool` в Colab).
*   **`get_image_all_metadata(self, path)`:** Выполняет `exiftool -j <path>` через `subprocess.check_output` и возвращает результат в виде строки JSON.
*   **`set_image_all_metadata(self, filepath, metadata)`:** Формирует команду `exiftool` с ключами и значениями из словаря `metadata` и выполняет ее через `subprocess.check_output`.

## Пример использования `MDManager`

```python
from Python.SLM.metadata.MDManager.mdmanager import MDManager

file_path = "path/to/your/image.jpg" # Убедитесь, что файл существует и exiftool.exe доступен

manager = MDManager(file_path)

# Чтение метаданных
meta = manager.Read()
if meta:
    print("Metadata read successfully:")
    # print(meta) # Раскомментируйте для вывода всех метаданных
    print(f"  Keywords: {meta.get('IPTC:Keywords', 'N/A')}")
    print(f"  Rating: {meta.get('XMP:Rating', 'N/A')}")
else:
    print("Failed to read metadata.")

# Изменение и сохранение метаданных
if meta:
    # Установка ключевых слов (если поддерживается типом файла)
    manager.metadata['IPTC:Keywords'] = ['test', 'python', 'metadata'] 
    # Установка рейтинга (XMP)
    manager.metadata['XMP:Rating'] = 4 
    
    if manager.Save():
        print("Metadata saved successfully.")
        
        # Проверка чтения после сохранения
        new_meta = manager.Read()
        if new_meta:
             print("Metadata after save:")
             print(f"  Keywords: {new_meta.get('IPTC:Keywords', 'N/A')}")
             print(f"  Rating: {new_meta.get('XMP:Rating', 'N/A')}")
             print(f"  ModifyDate: {new_meta.get('XMP:ModifyDate', 'N/A')}")

    else:
        print("Failed to save metadata.")
