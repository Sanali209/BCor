# ADR 0003: Реализация адаптеров инфраструктуры

## Статус
Принято (Accepted)

## Контекст
Слой Domain Core определил порты (`IImageScanner`, `IImageProcessor`, `IImageRepository`). Нам необходимо реализовать их, используя конкретные технологии (PIL, SQLite, Multiprocessing), при этом скрыв эти детали от бизнес-логики.

## Решение
1.  **PILScanner**: Реализация `IImageScanner`. Использует `concurrent.futures.ProcessPoolExecutor` для параллельного сканирования и `PIL` для извлечения метаданных. 
2.  **PILImageProcessor**: Реализация `IImageProcessor`. Использует `PIL` для операций `Convert` и `Scale`. Ожидает `ImageMetadata` на вход.
3.  **SQLiteImageRepository**: Реализация `IImageRepository`. Оборачивает работу с `sqlite3`.
4.  **DI (Dishka)**: Все адаптеры будут регистрироваться в `ImageAnalyzeLegacyModule` и внедряться в Use Cases через конструктор.

## Последствия
- **Положительные**: Инфраструктурные зависимости изолированы в слое `adapters/`. Легкая замена библиотеки (например, PIL на OpenCV) или базы данных.
- **Отрицательные**: Необходимость маппинга между доменными сущностями и форматами хранения (SQL/Dict).
