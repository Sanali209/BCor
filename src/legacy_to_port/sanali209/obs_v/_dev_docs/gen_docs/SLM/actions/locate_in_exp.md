# Locate In Explorer Action (`locate_in_exp.py`)

Этот файл определяет действие `AppActionLocateExpFile`, предназначенное для отображения указанного файла или папки в Проводнике Windows.

## Класс `AppActionLocateExpFile`

Наследуется от `AppAction`.

*   **`name`**: "show on associated editor" (Несмотря на имя, действие показывает файл в Проводнике, а не открывает в редакторе).
*   **`description`**: "show in associated editor"

### Метод `run(self, *args, **kwargs)`

*   **Назначение:** Пытается открыть Проводник Windows и выделить указанный файл или папку.
*   **Аргументы:** Ожидает путь к файлу/папке в качестве первого позиционного аргумента (`args[0]`).
*   **Логика:**
    1.  Получает путь из `args[0]`.
    2.  Проверяет, существует ли путь с помощью `os.path.exists()`.
    3.  **Если путь НЕ существует:**
        *   Показывает диалоговое окно ошибки с помощью `flet_dialog_alert` (из `SLM.flet.flet_ext`) с заголовком "Error" и текстом "path not exists".
        *   Получает абсолютный путь к (несуществующему) файлу.
        *   Выполняет команду `explorer /select,<absolute_path>` с помощью `subprocess.run`. *(Примечание: Из-за логики кода, команда `explorer` вызывается только если исходный путь не существует, что, вероятно, является ошибкой в исходном коде)*.
    4.  **Если путь существует:** Ничего не происходит (команда `explorer` не вызывается).
*   **Зависимости:** `os`, `subprocess`, `SLM.flet.flet_ext.flet_dialog_alert`, `SLM.actions.AppAction`.

## Пример использования

```python
from Python.SLM.actions.action_module import ActionManager
# Предполагается, что экземпляр action_manager уже создан и 
# AppActionLocateExpFile зарегистрирован с помощью @action_manager.register()

file_path = "C:\\path\\to\\your\\file.txt" 

# Вызов действия по имени
action_manager.run_action_by_name("show on associated editor", file_path) 
```

## Связанные концепции

*   [Action Module Base](_dev_docs/gen_docs/SLM/actions/index.md)
