# Undo/Redo System (`undo_sustem.py`)

Этот модуль предоставляет простую реализацию механизма Отмены/Повтора (Undo/Redo), основанную на двух стеках: один для операций отмены (`undo_stack`) и один для операций повтора (`redo_stack`).

**Примечание:** Имя исходного файла `undo_sustem.py` содержит опечатку. В документации используется исправленное имя `undo_system.md`.

## Класс `UndoItem`

*   **Назначение:** Представляет одну атомарную операцию, которую можно отменить и повторить. Хранит ссылки на функции (или любые `callable`), выполняющие действия отмены и повтора.
*   **Атрибуты:**
    *   `undo` (callable): Функция или метод, выполняющий действие отмены.
    *   `redo` (callable): Функция или метод, выполняющий действие повтора (возвращающее состояние до отмены).
*   **Методы:**
    *   **`__init__(self, undo, redo)`:** Сохраняет переданные `undo` и `redo` callables.
    *   **`undo(self)`:** Вызывает сохраненную функцию `self.undo()`.
    *   **`redo(self)`:** Вызывает сохраненную функцию `self.redo()`.

## Класс `UndoSystem`

*   **Назначение:** Управляет стеками операций отмены и повтора. Предоставляет интерфейс для добавления новых операций, выполнения отмены и повтора.
*   **Атрибуты:**
    *   `undo_stack` (list): Стек (реализованный через список), хранящий экземпляры `UndoItem` для операций, которые можно отменить. Последняя добавленная операция находится в конце списка.
    *   `redo_stack` (list): Стек, хранящий экземпляры `UndoItem` для операций, которые были отменены и могут быть повторены.
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует пустые стеки `undo_stack` и `redo_stack`.
    *   **`add_undo_item(self, undo, redo)`:**
        1.  Создает новый экземпляр `UndoItem` с переданными функциями `undo` и `redo`.
        2.  Добавляет этот `UndoItem` в `undo_stack`.
        3.  **Очищает `redo_stack`**. Это стандартное поведение для систем Undo/Redo: если после отмены выполняется новая операция, возможность повторить отмененные ранее операции теряется.
    *   **`undo(self)`:**
        1.  Проверяет, не пуст ли `undo_stack`. Если пуст, ничего не делает.
        2.  Извлекает последний `UndoItem` из `undo_stack` (`pop()`).
        3.  Вызывает метод `undo()` у извлеченного `UndoItem`.
        4.  Добавляет этот `UndoItem` в `redo_stack`.
    *   **`redo(self)`:**
        1.  Проверяет, не пуст ли `redo_stack`. Если пуст, ничего не делает.
        2.  Извлекает последний `UndoItem` из `redo_stack` (`pop()`).
        3.  Вызывает метод `redo()` у извлеченного `UndoItem`.
        4.  Добавляет этот `UndoItem` обратно в `undo_stack`.
    *   **`clear(self)`:** Очищает оба стека (`undo_stack` и `redo_stack`).
    *   **`get_undo_stack(self)`:** Возвращает ссылку на `undo_stack` (для возможного отображения истории или отладки).
    *   **`get_redo_stack(self)`:** Возвращает ссылку на `redo_stack`.

## Пример использования

```python
from SLM.appGlue.undo_sustem import UndoSystem # Используем имя файла как есть

# --- Определяем функции, изменяющие состояние ---
value = 0

def set_value(new_value):
    global value
    old_value = value
    value = new_value
    print(f"Value set to: {value}")
    
    # Возвращаем функцию для отмены этого действия
    def undo_set_value():
        global value
        value = old_value
        print(f"Undo: Value restored to: {value}")
        
    # Возвращаем функцию для повтора этого действия
    def redo_set_value():
        global value
        value = new_value
        print(f"Redo: Value set back to: {value}")
        
    return undo_set_value, redo_set_value

def add_value(amount):
    global value
    value += amount
    print(f"Added {amount}. Value is now: {value}")
    
    def undo_add_value():
        global value
        value -= amount
        print(f"Undo Add: Value restored to: {value}")
        
    def redo_add_value():
        global value
        value += amount
        print(f"Redo Add: Value set back to: {value}")
        
    return undo_add_value, redo_add_value

# --- Используем UndoSystem ---
undo_manager = UndoSystem()

# Выполняем первое действие и добавляем его в UndoSystem
undo_func, redo_func = set_value(10)
undo_manager.add_undo_item(undo_func, redo_func) 
# Output: Value set to: 10

# Выполняем второе действие
undo_func, redo_func = add_value(5)
undo_manager.add_undo_item(undo_func, redo_func)
# Output: Added 5. Value is now: 15

print(f"Current Value: {value}") # Output: Current Value: 15
print(f"Undo stack size: {len(undo_manager.get_undo_stack())}") # Output: 2
print(f"Redo stack size: {len(undo_manager.get_redo_stack())}") # Output: 0

# Отменяем последнее действие (add_value)
undo_manager.undo()
# Output: Undo Add: Value restored to: 10
print(f"Current Value after undo: {value}") # Output: 10
print(f"Undo stack size: {len(undo_manager.get_undo_stack())}") # Output: 1
print(f"Redo stack size: {len(undo_manager.get_redo_stack())}") # Output: 1

# Отменяем еще одно действие (set_value)
undo_manager.undo()
# Output: Undo: Value restored to: 0
print(f"Current Value after second undo: {value}") # Output: 0
print(f"Undo stack size: {len(undo_manager.get_undo_stack())}") # Output: 0
print(f"Redo stack size: {len(undo_manager.get_redo_stack())}") # Output: 2

# Повторяем последнее отмененное действие (set_value)
undo_manager.redo()
# Output: Redo: Value set back to: 10
print(f"Current Value after redo: {value}") # Output: 10
print(f"Undo stack size: {len(undo_manager.get_undo_stack())}") # Output: 1
print(f"Redo stack size: {len(undo_manager.get_redo_stack())}") # Output: 1

# Выполняем новое действие - это очистит redo_stack
undo_func, redo_func = set_value(100)
undo_manager.add_undo_item(undo_func, redo_func)
# Output: Value set to: 100
print(f"Current Value after new action: {value}") # Output: 100
print(f"Undo stack size: {len(undo_manager.get_undo_stack())}") # Output: 2
print(f"Redo stack size: {len(undo_manager.get_redo_stack())}") # Output: 0 (очищен!)

# Попытка повторить уже невозможна
undo_manager.redo() # Ничего не произойдет
print(f"Current Value after failed redo: {value}") # Output: 100
```

Эта система проста в использовании и подходит для большинства стандартных сценариев Undo/Redo, где операции можно представить парами функций `undo` и `redo`.
