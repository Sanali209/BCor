# Tree Data View (`treedata.py`)

Этот модуль предоставляет класс `TreeDataView`, который позволяет создать фильтруемое и наблюдаемое представление ("view") над древовидной структурой данных. Он использует объекты `Specification` для фильтрации и уведомляет подписчиков об изменениях в видимой структуре.

## Зависимости

*   `SLM.appGlue.DesignPaterns.specification.Specification`: Используется для фильтрации элементов дерева.

## Класс `TreeDataView`

*   **Назначение:** Представляет собой фильтруемый и наблюдаемый вид над древовидной структурой. Позволяет итерировать по видимым узлам (как на верхнем уровне, так и для конкретного родителя), применять фильтры и получать уведомления об изменениях.
*   **Механизм хранения дерева:**
    *   **Статический атрибут `dict_child_list` (dict):** Это **ключевая особенность** данного класса. Он использует статический (на уровне класса) словарь для хранения связей "родитель -> список детей". Ключами словаря являются объекты-родители, а значениями - списки их дочерних объектов.
    *   **Статический метод `get_child_list(data_item)`:** Вспомогательный метод для получения (или создания пустого списка, если отсутствует) списка дочерних элементов для `data_item` из `dict_child_list`.
    *   **Предупреждение:** Использование статического словаря для хранения структуры всего дерева может привести к проблемам:
        *   **Глобальное состояние:** Все экземпляры `TreeDataView` будут работать с одним и тем же базовым деревом, хранящимся в `dict_child_list`. Это может быть неочевидным и привести к неожиданным побочным эффектам, если предполагается работа с независимыми деревьями.
        *   **Управление памятью:** Если объекты удаляются из дерева с помощью `remove`, но остаются ключами или значениями в `dict_child_list` (например, если у удаленного узла были дети), это может привести к утечкам памяти, так как ссылки на эти объекты будут сохраняться в статическом словаре. Требуется аккуратное управление жизненным циклом объектов и очистка словаря.
*   **Атрибуты экземпляра:**
    *   `source_tree_ref` (object): Объект, представляющий корень или точку отсчета для данного вида дерева (по умолчанию новый пустой объект). Итерация по умолчанию (`__iter__`) начинается с детей этого объекта.
    *   `specification` (`Specification` | None): Объект спецификации, используемый для фильтрации узлов. Если `None`, все узлы считаются видимыми.
    *   `_view_changed_call_backs` (list): Список функций обратного вызова, которые будут вызваны при изменении видимой структуры дерева (добавление/удаление видимого узла, изменение спецификации).
    *   `get_child_list` (Callable): Ссылка на статический метод `TreeDataView.get_child_list`.
    *   `suspend_view_changed` (bool): Флаг для временного отключения вызова колбэков `_fire_view_changed`.
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует атрибуты экземпляра.
    *   **`__iter__(self)`:** Позволяет итерировать по дочерним элементам `source_tree_ref`, которые удовлетворяют текущей `specification`.
    *   **`iter(self, data_item)`:** Позволяет итерировать по дочерним элементам указанного `data_item`, которые удовлетворяют текущей `specification`.
    *   **`_is_satisfied(self, data_item)`:** Проверяет, удовлетворяет ли `data_item` текущей `specification`.
    *   **`set_specification(self, spec: Specification)`:** Устанавливает новую спецификацию фильтрации и вызывает `_fire_view_changed()`.
    *   **`_fire_view_changed(self)`:** Вызывает все зарегистрированные колбэки, если `suspend_view_changed` равно `False`.
    *   **`add_view_changed_callback(self, callback)`:** Регистрирует функцию обратного вызова для уведомлений об изменениях.
    *   **`add_to_tree(self, item, parent=None)`:** Добавляет `item` в список дочерних элементов `parent` (или `source_tree_ref`) в статическом словаре `dict_child_list`. Уведомляет подписчиков, если добавленный `item` видим (удовлетворяет спецификации).
    *   **`remove(self, item, parent=None)`:** Удаляет `item` из списка дочерних элементов `parent` в статическом словаре `dict_child_list`. Уведомляет подписчиков, если удаленный `item` был видим.
    *   **`set_source(self, sorce_list)`:** Добавляет список элементов `sorce_list` как дочерние к `source_tree_ref`. Уведомления временно отключаются и вызываются один раз в конце.

## Пример использования

```python
from SLM.appGlue.DesignPaterns.specification import Specification
from SLM.appGlue.DAL.treedata import TreeDataView

# Пример спецификации (показывает только строки)
class IsStringSpec(Specification):
    def is_satisfied_by(self, item):
        return isinstance(item, str)

# Создаем узлы дерева (простые строки и числа)
root_item = "Root"
child1 = "Child 1"
child2 = 2 # Не строка
child1_1 = "Child 1.1"
child1_2 = "Child 1.2"

# Создаем представление дерева
tree_view = TreeDataView()

# Добавляем узлы в дерево (используя статический словарь через tree_view)
tree_view.add_to_tree(root_item) # Добавляем к source_tree_ref по умолчанию
tree_view.add_to_tree(child1, parent=root_item)
tree_view.add_to_tree(child2, parent=root_item)
tree_view.add_to_tree(child1_1, parent=child1)
tree_view.add_to_tree(child1_2, parent=child1)

# Функция-наблюдатель
def on_view_changed(view):
    print("\n--- Tree View Changed ---")
    print("Filtered Top Level:")
    for item in view: # Итерация по верхнему уровню (__iter__)
        print(f"- {item}")
    
    print("\nFiltered Children of 'Child 1':")
    # Итерация по детям конкретного узла
    for item in view.iter(child1): 
        print(f"- {item}")
    print("-------------------------\n")

# Регистрируем наблюдателя
tree_view.add_view_changed_callback(on_view_changed)

print("Initial state (no filter):")
on_view_changed(tree_view) # Вызываем вручную для показа начального состояния

print("Setting string filter...")
tree_view.set_specification(IsStringSpec())
# Output: (on_view_changed будет вызван автоматически)
# --- Tree View Changed ---
# Filtered Top Level:
# - Root 
# Filtered Children of 'Child 1':
# - Child 1.1
# - Child 1.2
# -------------------------

print("Adding a new string child...")
new_child = "Child 3 (String)"
tree_view.add_to_tree(new_child, parent=root_item)
# Output: (on_view_changed будет вызван автоматически, т.к. new_child удовлетворяет фильтру)
# --- Tree View Changed ---
# Filtered Top Level:
# - Root
# - Child 3 (String) 
# Filtered Children of 'Child 1':
# - Child 1.1
# - Child 1.2
# -------------------------

print("Removing 'Child 1.1'...")
tree_view.remove(child1_1, parent=child1)
# Output: (on_view_changed будет вызван автоматически)
# --- Tree View Changed ---
# Filtered Top Level:
# - Root
# - Child 3 (String) 
# Filtered Children of 'Child 1':
# - Child 1.2 
# -------------------------

print("Removing filter...")
tree_view.set_specification(None)
# Output: (on_view_changed будет вызван автоматически)
# --- Tree View Changed ---
# Filtered Top Level:
# - Root
# - Child 3 (String) 
# Filtered Children of 'Child 1':
# - Child 1.2 
# -------------------------
# Примечание: Хотя фильтр снят, удаленный 'Child 1.1' не вернется. 
#             on_view_changed показывает текущее состояние видимых узлов.
#             Чтобы увидеть Child 2, нужно итерировать по детям root_item.

print("\nChildren of root_item (no filter):")
for item in tree_view.iter(root_item):
    print(f"- {item}")
# Output:
# - Child 1
# - 2 
# - Child 3 (String)

# Важно: Очистка dict_child_list не предусмотрена в классе.
# Если объекты дерева удаляются из приложения, их нужно вручную удалять 
# из TreeDataView.dict_child_list, чтобы избежать утечек памяти.
# Например:
# del TreeDataView.dict_child_list[child1] # Удалить запись о детях child1
# del TreeDataView.dict_child_list[root_item] # Удалить запись о детях root_item
# и т.д.
```

Этот класс предоставляет удобный способ работы с фильтрованными представлениями деревьев, но требует осторожности из-за использования статического словаря для хранения структуры.
