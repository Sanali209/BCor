# Package Initializer (`__init__.py`)

Этот файл `__init__.py` находится в директории `annotation_tool`.

## Содержимое

Файл **пуст**.

## Назначение

Несмотря на отсутствие кода, наличие этого файла критически важно. Он указывает интерпретатору Python, что директория `annotation_tool` должна рассматриваться как **пакет**. Это позволяет импортировать модули из этой директории (например, `annotation.py`, `annotation_export.py`) с использованием стандартного синтаксиса импорта Python, например:

```python
from SLM.files_db.annotation_tool.annotation import AnnotationJob
from SLM.files_db.annotation_tool.annotation_export import DataSetExporterManager
```

Без этого файла попытка импорта модулей из `annotation_tool` привела бы к ошибке `ModuleNotFoundError`.
