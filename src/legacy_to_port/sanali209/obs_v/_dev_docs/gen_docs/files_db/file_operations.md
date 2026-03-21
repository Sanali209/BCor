# Файловые операции

Этот раздел описывает, как модуль `files_db` (в основном через класс `FileRecord`) взаимодействует с файловой системой: добавление, удаление, перемещение файлов и обновление записей в базе данных.

## Основные операции (реализованы в `FileRecord` и связанных функциях)

### Создание записей

*   **`FileRecord.add_file_records_from_folder(folder_path, black_list=None)`**:
    *   Сканирует указанную папку (`folder_path`) на наличие файлов (используя `get_files`).
    *   Применяет опциональный `black_list` шаблонов (`fnmatch`) для исключения файлов.
    *   Для каждого нового файла (проверяется по `local_path` и `name`):
        *   Вызывает `FileRecord.create_record_data(file_path=...)` для сбора базовой информации (имя, путь, расширение, тип файла, размер, **`file_content_md5`**).
        *   Обрабатывает ошибки доступа к файлу (устанавливает `file_corrupted=True`).
    *   Массово вставляет новые записи в MongoDB.
*   **`FileRecord.create_record_data(file_path)`**: Внутренний метод для сбора данных о файле перед созданием записи.

### Поиск записей

*   **`FileRecord.get_record_by_path(path)`**: Находит одну запись `FileRecord` по ее полному пути.
*   **`get_file_record_by_folder(folder_path, recurse=False, filters=None)`**: Находит записи `FileRecord` в указанной папке (или рекурсивно).

### Удаление записей и файлов

*   **`FileRecord.delete()`**:
    *   **Удаляет файл с диска (`os.remove`)**.
    *   Удаляет запись из MongoDB.
    *   Инициирует событие `onDelete` для каскадного удаления связанных данных (`RelationRecord`, `Detection`).
*   **`FileRecord.delete_all_file_records()`**:
    *   Удаляет **все** записи `FileRecord` из MongoDB.
    *   **Не удаляет файлы с диска**.
*   **`remove_files_record_by_mach_pattern(path, regex_mach_pathern)`**:
    *   Находит записи `FileRecord` по пути и regex-шаблону имени.
    *   Удаляет найденные записи из MongoDB.
    *   **Не удаляет файлы с диска**.

### Перемещение файлов

*   **`FileRecord.move_to_folder(new_folder)`**:
    *   **Перемещает физический файл (`os.rename`)** в новую папку.
    *   Обновляет поле `local_path` в записи MongoDB.

### Обновление путей (перепривязка)

*   **`refind_exist_files(path)`**:
    *   Сканирует папку (`path`).
    *   Для каждого файла вычисляет `file_content_md5`.
    *   Ищет запись `FileRecord` с таким же `file_content_md5`.
    *   Если найдена, **обновляет `local_path` и `name`** в записи MongoDB, чтобы они соответствовали текущему расположению файла.
    *   Полезно для синхронизации БД после перемещения файлов вне приложения.

*Примечание: Функции сканирования папок, добавления, удаления и перемещения файлов реализованы как статические методы или методы экземпляра класса `FileRecord` (`Python/SLM/files_db/components/File_record_wraper.py`). Отдельные модули `delete_exist_file.py` и `index_folder.py`, упомянутые ранее, не найдены.*

[Назад к главной странице](./index.md)
