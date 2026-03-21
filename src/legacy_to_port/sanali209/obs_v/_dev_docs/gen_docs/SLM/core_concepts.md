# Core Concepts in SLM

В этом документе описаны фундаментальные концепции и терминология, используемые в модуле SLM.

## Основные понятия

### 1. Действия (Actions)
- **Определение**: Атомарные операции, выполняющие конкретные задачи
- **Характеристики**:
  - Независимость выполнения
  - Идемпотентность
  - Возможность отмены
- **Пример**:
```python
class ResizeImageAction(BaseAction):
    def execute(self, context):
        image = context.get_image()
        return image.resize(self.target_size)
```
[Подробнее об Actions](actions/index.md)

### 2. Цепочки (Chains)
- **Определение**: Последовательности действий для решения сложных задач
- **Возможности**:
  - Параллельное выполнение
  - Условное ветвление
  - Обработка ошибок
- **Пример**:
```python
chain = Chain()
chain.add(LoadImage())
chain.add(DetectObjects())
chain.add(ExtractMetadata())
```
[Подробнее о Chains](chains/index.md)

### 3. Метаданные (Metadata)
- **Определение**: Структурированная информация о файлах и объектах
- **Компоненты**:
  - Теги
  - Атрибуты
  - Связи
- **Пример**:
```python
metadata = {
    "filename": "image.jpg",
    "tags": ["nature", "landscape"],
    "dimensions": (1920, 1080)
}
```
[Подробнее о Metadata](metadata/index.md)

### 4. Векторные представления (Embeddings)
- **Определение**: Числовые представления данных для поиска по сходству
- **Применение**:
  - Семантический поиск
  - Кластеризация
  - Рекомендации
- **Пример**:
```python
embedding = model.encode(image)  # -> [0.1, 0.2, ..., 0.5]
similar = vector_db.find_similar(embedding)
```
[Подробнее о Vector DB](vector_db/index.md)

### 5. Графы (Graphs)
- **Определение**: Структуры данных для представления связей
- **Элементы**:
  - Узлы (сущности)
  - Рёбра (отношения)
  - Атрибуты
- **Пример**:
```python
graph.add_node("image1", type="image")
graph.add_node("image2", type="image")
graph.add_edge("image1", "image2", type="similar")
```
[Подробнее о Graph Module](Graph/index.md)

## Взаимодействие компонентов



### 2. Контекст выполнения
```python
context = ExecutionContext()
context.set_input(file_path)
context.set_metadata(metadata)
context.set_parameters(params)
```

### 3. Обработка событий
```python
@event_handler("file_changed")
def on_file_change(event):
    metadata.update(event.file_path)
    vector_db.reindex(event.file_path)
```

## Паттерны использования

### 1. Обработка файлов
```python
def process_file(file_path):
    # 1. Загрузка файла
    file = load_file(file_path)
    
    # 2. Извлечение метаданных
    metadata = extract_metadata(file)
    
    # 3. Создание эмбеддингов
    embedding = create_embedding(file)
    
    # 4. Обновление графа
    update_graph(file_path, metadata)
    
    # 5. Индексация
    index_file(file_path, embedding)
```

### 2. Поиск и анализ
```python
def find_similar(query):
    # 1. Создание эмбеддинга запроса
    query_embedding = encode_query(query)
    
    # 2. Поиск похожих
    similar = vector_db.search(query_embedding)
    
    # 3. Анализ связей
    related = graph.find_connected(similar)
    
    # 4. Фильтрация по метаданным
    filtered = metadata.filter(related)
    
    return filtered
```

## Расширение системы

### 1. Создание нового действия
```python
class CustomAction(BaseAction):
    def validate(self, context):
        # Проверка входных данных
        pass
        
    def execute(self, context):
        # Выполнение действия
        pass
        
    def rollback(self, context):
        # Откат изменений
        pass
```

## Лучшие практики

1. **Атомарность действий**:
   - Одна задача - одно действие
   - Четкие входы и выходы
   - Возможность отката

2. **Управление состоянием**:
   - Использование контекста
   - Транзакционность
   - Обработка ошибок

3. **Производительность**:
   - Кэширование результатов
   - Ленивая загрузка
   - Пакетная обработка

4. **Расширяемость**:
   - Модульная структура
   - Слабая связность
   - Инверсия зависимостей
