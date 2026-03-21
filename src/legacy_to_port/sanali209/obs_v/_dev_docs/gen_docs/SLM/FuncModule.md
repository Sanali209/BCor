# FuncModule Documentation

Этот модуль (`FuncModule.py`) предоставляет набор общих утилитных функций, в основном для операций с файловой системой и обработки списков, используемых в различных частях модуля SLM.

## Классы

### `list_ext`
Статический класс с расширениями для стандартного типа `list`.
*   **`first_or_default(list_inst, default=None)`:** Возвращает первый элемент списка `list_inst`, если он не пуст, иначе возвращает значение `default`.

## Функции

*   **`unarchAll(folder)`:** Рекурсивно находит все архивы (`.zip`, `.rar`, `.7z`) в указанной папке `folder` и распаковывает их в ту же папку, где находится архив. Требует установленной библиотеки `patool`.
*   **`sanitize_file_path(file_path)`:** Очищает путь к файлу: удаляет кавычки (`'` или `"`) в начале и конце строки, заменяет все слеши (`/`) на обратные (`\`) и возвращает абсолютный путь.
*   **`getZipingFiles_and_folders(curZipDir, exclude="*.zip")`:** Возвращает список файлов и папок в директории `curZipDir`, исключая те, которые соответствуют маскам в строке `exclude` (маски разделяются точкой с запятой). По умолчанию исключает файлы `.zip`.
*   **`getDirectories(rootSerchPath)`:** Возвращает список поддиректорий (не рекурсивно) в указанной директории `rootSerchPath`. Если поддиректорий нет, возвращает список, содержащий только `rootSerchPath`.
*   **`human_readable_size(size, precision=2)`:** Преобразует размер в байтах `size` в человекочитаемый формат (KB, MB, GB, TB) с заданной точностью `precision`.
*   **`deleteFile_to_recycle_bin(file)`:** Перемещает указанный файл `file` в корзину. Требует установленной библиотеки `send2trash`.
*   **`getFolders(directory, include_masc="*")`:** Рекурсивно находит все папки в указанной директории `directory`, соответствующие маске `include_masc`, и возвращает список их путей.
*   **`flaten_directory(path)`:** "Выравнивает" директорию `path`, перемещая все файлы из поддиректорий в корневую директорию `path`, а затем удаляя исходные файлы из поддиректорий. *Внимание: Эта функция может привести к перезаписи файлов с одинаковыми именами.*
*   **`documenting_example(inimagepath, outhimagepath)`:** Пример функции с документацией в формате reStructuredText. Похоже, не выполняет реальной работы, а служит демонстрацией форматирования документации.

## Примеры использования

```python
from Python.SLM.FuncModule import sanitize_file_path, human_readable_size, deleteFile_to_recycle_bin, list_ext

# Очистка пути
clean_path = sanitize_file_path('"C:/Users/User/Documents/some file.txt"') 
# clean_path будет 'C:\\Users\\User\\Documents\\some file.txt'

# Получение размера файла
import os
file_size = os.path.getsize(clean_path)
readable_size = human_readable_size(file_size) 
# readable_size будет, например, "15.23KB"

# Получение первого элемента или None
my_list = [10, 20, 30]
first = list_ext.first_or_default(my_list) # first будет 10
empty_list = []
first_empty = list_ext.first_or_default(empty_list, default=-1) # first_empty будет -1

# Удаление в корзину (будьте осторожны!)
# if os.path.exists(clean_path):
#     deleteFile_to_recycle_bin(clean_path) 
```
