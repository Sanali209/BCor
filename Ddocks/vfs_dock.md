# Модуль VFS (Virtual File System)

## Обзор (Overview)
Модуль **VFS** — это абстрактный слой над файловыми системами, построенный на базе библиотеки `PyFilesystem2`. Он позволяет системе работать с файлами (чтение, запись, листинг) независимо от физического хранилища (локальный диск, S3, FTP).

---

## Конфигурация (Configuration)
Настройки модуля определяются в `src/modules/vfs/settings.py` через `VFSSettings`:
*   `base_dir`: Основной путь к хранилищу активов.
*   `protocol`: Поддерживаемый протокол (`osfs`, `s3`, `ftp` и т.д.).

---

## Техническая спецификация (Technical Reference)

### Integration & Providers
The VFS is managed by the `VfsProvider` in `src/modules/vfs/module.py`. 
When injected via DI, it provides an `FS` instance (e.g., `OSFS` for local disks).

```python
@provide
def provide_fs(self, settings: VFSSettings) -> FS:
    return open_fs(settings.base_dir)
```

### Known Technical Debt (TD-0004)
Currently, some legacy and experimental services (including `AssetIngestionService`) still use native `os` and `pathlib` calls for directory walking. 

> [!WARNING]
> **Refactoring Required**: All modules SHOULD be refactored to use the injected `VFS` instance instead of native `os.walk` to ensure future cloud compatibility (S3/Azure).

---
*Note: Code reference: [src/modules/vfs/](file:///d:/github/BCor/src/modules/vfs/)*
