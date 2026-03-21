# File Record Wrapper (`File_record_wraper.py`)

Этот модуль определяет класс `FileRecord`, который является ключевой моделью данных для представления **файлов, хранящихся в локальной файловой системе**, в базе данных SLM. Он наследуется от `CollectionRecord` и добавляет специфичные для файлов атрибуты и методы управления.

## Зависимости

*   `os`, `fnmatch`, `re`
*   `concurrent.futures.ThreadPoolExecutor`
*   `tqdm`
*   `loguru`
*   `SLM.appGlue.core.Allocator`
*   `SLM.files_data_cache.imagedatacache.ImageDataCacheManager`
*   `SLM.files_data_cache.thumbnail.ImageThumbCache`
*   `SLM.iterable.bach_builder.BatchBuilder`
*   `SLM.mongoext.MongoClientEXT_f.MongoClientExt` (не используется напрямую, но подразумевается `MongoRecordWrapper`)
*   `SLM.vision.imagetotext.ImageToLabel.ImageToLabel`
*   `SLM.FuncModule.sanitize_file_path`
*   `SLM.files_db.components.collectionItem.CollectionRecord`
*   `SLM.appGlue.iotools.pathtools.get_files`
*   `SLM.appGlue.progress_visualize.ProgressManager`
*   `SLM.mongoext.wraper.MongoRecordWrapper`, `SLM.mongoext.wraper.FieldPropInfo`
*   `SLM.files_db.components.CollectionRecordScheme.FileTypeRouter` (импортируется внутри `create_record_data`)

## Класс `FileRecord`

Наследуется от `CollectionRecord`.

### Назначение

*   Представлять файл из файловой системы как документ в MongoDB.
*   Предоставлять методы для управления файлом (поиск, добавление, удаление, перемещение).
*   Интегрироваться с системами кэширования (миниатюры, MD5).
*   Интегрироваться с AI-сервисами для анализа файлов.

### Атрибуты и Поля (`FieldPropInfo`)

*   **`itemType: str`**: Переопределено значением по умолчанию `'FileRecord'`.
*   **`name: str`**: Имя файла с расширением (например, `photo.jpg`).
*   **`local_path: str`**: Абсолютный или относительный путь к директории, содержащей файл.
*   **`file_type: str`**: Тип файла, определенный `FileTypeRouter` (например, `"Image:JPG"`).
*   **`source: str`**: Информация об источнике файла (например, URL загрузки).
*   *(Наследует также все поля от `CollectionRecord`: `favorite`, `hidden`, `rating`, `title`, `description`, `notes`, `ai_expertise`, `file_content_md5` и т.д.)*

### Ключевые Методы

#### Управление AI Expertise

*   **`get_ai_expertise(self, expertise_type, expertise_name, **kwargs)`**:
    *   Получает или генерирует данные анализа ИИ для файла.
    *   Проверяет наличие актуальных данных в поле `ai_expertise` (список словарей), сравнивая `expertise_type`, `expertise_name`, версию модели (полученную из соответствующего сервиса, например `ImageToLabel`) и хэш параметров `kwargs`.
    *   Если актуальных данных нет, вызывает соответствующий AI-сервис (например, `ImageToLabel().get_label_from_path`) для генерации данных.
    *   Сохраняет/обновляет результат в поле `ai_expertise` и возвращает его.
*   **`kwargs_to_md(kwargs)` (static)**: Вспомогательный метод для хэширования словаря параметров `kwargs`, используемый для кэширования результатов `get_ai_expertise`.

#### Управление Миниатюрами

*   **`get_thumb(self, size="medium")`**: Возвращает путь к миниатюре указанного размера (`small`, `medium`, `large`), используя `ImageThumbCache`.
*   **`refresh_thumb(self)`**: Запускает принудительное пересоздание миниатюр для этого файла в `ImageThumbCache`.

#### Операции с Файлами и Базой Данных (Экземпляр)

*   **`move_to_folder(self, new_folder)`**: Перемещает физический файл в `new_folder` и обновляет `local_path` в документе MongoDB.
*   **`delete(self)`**: Удаляет документ из MongoDB (`self.delete_rec()`) и пытается удалить файл с диска. Генерирует событие `onDelete`.

#### Операции с Базой Данных (Статические/Классовые)

*   **`get_record_by_path(path)` (static)**: Находит и возвращает один экземпляр `FileRecord` по полному пути к файлу.
*   **`add_file_record_from_path(path)` (static)**: *Некорректное имя.* Фактически, **ищет** существующий `FileRecord` по пути. Не добавляет новый.
*   **`add_file_records_from_folder(folder_path, black_list=None)` (static)**:
    *   Сканирует папку `folder_path`.
    *   Для каждого файла, не соответствующего `black_list` и отсутствующего в БД (проверка по `local_path` и `name`), создает словарь данных с помощью `create_record_data`.
    *   Выполняет массовую вставку (`insert_many`) подготовленных данных в MongoDB.
    *   Использует `ProgressManager` для отслеживания прогресса.
*   **`delete_all_file_records()` (static)**: Удаляет все документы с `item_type='FileRecord'` из коллекции.
*   **`create_record_data(cls, **kwargs)` (classmethod)**:
    *   Основной метод для подготовки данных документа MongoDB перед вставкой.
    *   Принимает `file_path` в `kwargs`.
    *   Извлекает `name`, `local_path`, `extension`.
    *   Определяет `file_type` с помощью `FileTypeRouter`.
    *   Получает `size` файла (обрабатывает ошибки).
    *   Вычисляет `file_content_md5` с помощью `ImageDataCacheManager`.
    *   Объединяет эти данные с данными из базового класса `CollectionRecord.create_record_data`.
    *   Возвращает готовый словарь данных для документа.

### Свойства

*   **`full_path`**:
    *   `getter`: Возвращает полный путь к файлу, комбинируя `local_path` и `name`.
    *   `setter`: Принимает полный путь, разбирает его на `local_path` и `name` и обновляет соответствующие поля в документе.

## Модульные Функции

*   **`get_file_record_by_folder(folder_path, recurse=False, filters=None)`**: Ищет и возвращает список `FileRecord` в указанной папке. Поддерживает рекурсию (с использованием MongoDB regex) и дополнительные фильтры.
*   **`refind_exist_files(path)`**: Помогает "перепривязать" записи в БД к файлам на диске после их возможного перемещения. Сканирует `path`, для каждого файла находит запись в БД по MD5 хэшу и обновляет `local_path`/`name` в записи. Использует `ThreadPoolExecutor` для параллелизма.
*   **`remove_files_record_by_mach_pattern(path, regex_mach_pathern)`**: Удаляет записи `FileRecord` из БД, соответствующие префиксу пути и регулярному выражению для имени файла.

## Использование

Класс `FileRecord` является центральным элементом для работы с файлами в SLM. Он используется для добавления новых файлов в базу данных, поиска существующих, получения метаданных, миниатюр, AI-анализа и выполнения файловых операций. Статические методы и модульные функции предоставляют утилиты для массовой обработки файлов.
