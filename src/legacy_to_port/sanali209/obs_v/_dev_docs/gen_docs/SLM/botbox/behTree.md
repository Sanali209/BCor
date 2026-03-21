# Behavior Tree System (`behTree.py`)

Этот модуль реализует базовые компоненты для создания деревьев поведения (Behavior Trees), используемых для управления поведением агентов в игре.

## Компоненты

### Класс `Blackboard`

```python
class Blackboard:
    def __init__(self):
        self.data = {}
```

**Назначение:** Хранилище данных, используемое узлами дерева поведения для обмена информацией.

**Методы:**
- `set_value(key, value)`: Сохраняет значение по ключу
- `get_value(key)`: Получает значение по ключу
- `clear()`: Очищает все данные

### Базовые узлы

#### `Node`
```python
class Node:
    def run(self, blackboard):
        raise NotImplementedError("This method should be overridden by subclasses.")
```
Базовый класс для всех узлов дерева поведения.

#### `ActionNode`
```python
class ActionNode(Node):
    def __init__(self, action):
        self.action = action
```
Узел, выполняющий конкретное действие. Принимает функцию действия в конструкторе.

#### `CompositeNode`
```python
class CompositeNode(Node):
    def __init__(self):
        self.children = []
```
Базовый класс для узлов, имеющих дочерние узлы.

### Составные узлы

#### `Selector`
```python
class Selector(CompositeNode):
    def run(self, blackboard):
        # ... реализация ...
```
- **Назначение:** Выполняет дочерние узлы, пока один из них не вернет "success"
- **Поведение:** Как логическое ИЛИ - успешен, если хотя бы один дочерний узел успешен
- **Возвращает:**
  - "success": если любой дочерний узел вернул "success"
  - "failure": если все дочерние узлы вернули "failure"

#### `Sequence`
```python
class Sequence(CompositeNode):
    def __init__(self):
        super().__init__()
        self.cur_child = None
```
- **Назначение:** Выполняет дочерние узлы последовательно
- **Поведение:** Как логическое И - успешен, только если все дочерние узлы успешны
- **Состояние:** Отслеживает текущий выполняемый узел через `cur_child`
- **Возвращает:**
  - "running": если текущий узел еще выполняется или есть следующие узлы
  - "success": если все узлы успешно выполнены
  - "failure": если любой узел вернул "failure"

### Декораторы

#### `Inverter`
```python
class Inverter(ActionNode):
    def __init__(self, node):
        self.node = node
```
Инвертирует результат узла: успех → неудача, неудача → успех.

#### `ForceSuccess`
```python
class ForceSuccess(ActionNode):
    def __init__(self, node):
        self.node = node
```
Всегда возвращает "success", независимо от результата узла.

#### `ForceFailure`
```python
class ForceFailure(ActionNode):
    def __init__(self, node):
        self.node = node
```
Всегда возвращает "failure", независимо от результата узла.

## Использование

### Создание простого дерева поведения

```python
# Создание доски для обмена данными
blackboard = Blackboard()

# Определение действий
def move_to_target(bb):
    target = bb.get_value("target")
    # ... логика движения ...
    return "success"

def attack_target(bb):
    target = bb.get_value("target")
    # ... логика атаки ...
    return "success"

# Создание дерева
sequence = Sequence()
sequence.add_child(ActionNode(move_to_target))
sequence.add_child(ActionNode(attack_target))

# Выполнение дерева
while True:
    result = sequence.run(blackboard)
    if result != "running":
        break
```

### Создание сложного поведения

```python
# Создание селектора с несколькими возможными действиями
selector = Selector()

# Последовательность для атаки
attack_sequence = Sequence()
attack_sequence.add_child(ActionNode(find_target))
attack_sequence.add_child(ActionNode(move_to_target))
attack_sequence.add_child(ActionNode(attack_target))

# Последовательность для патрулирования
patrol_sequence = Sequence()
patrol_sequence.add_child(ActionNode(get_patrol_point))
patrol_sequence.add_child(ActionNode(move_to_point))

# Добавление последовательностей в селектор
selector.add_child(attack_sequence)
selector.add_child(patrol_sequence)
```

## Особенности реализации

1. **Состояния узлов:**
   - "success": успешное выполнение
   - "failure": неудача
   - "running": выполнение продолжается

2. **Сохранение состояния:**
   - `Sequence` сохраняет индекс текущего дочернего узла
   - `Blackboard` позволяет хранить общие данные

3. **Компонуемость:**
   - Узлы могут быть вложены друг в друга
   - Декораторы модифицируют поведение узлов

## Ограничения

1. **Отсутствуют:**
   - Параллельные узлы
   - Условные декораторы
   - Ограничения по времени
   - Обработка ошибок

2. **Простота состояний:**
   - Только три базовых состояния
   - Нет приоритетов
   - Нет условий прерывания

## Возможные улучшения

1. **Функциональность:**
   - Добавление параллельных узлов
   - Реализация условных декораторов
   - Добавление таймаутов

2. **Отладка:**
   - Логирование выполнения
   - Визуализация дерева
   - Инструменты отладки

3. **Производительность:**
   - Пулинг узлов
   - Оптимизация обхода
   - Кэширование состояний
