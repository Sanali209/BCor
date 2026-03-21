# Selection Manager (`selectionManager.py`)

Этот модуль предоставляет систему для управления выбором (selection) объектов в приложении. Это полезно, например, в GUI, где пользователь может выбирать один или несколько элементов в списке, таблице или графе. Система позволяет отслеживать выбранные элементы, получать связанные с ними данные и уведомлять другие части приложения об изменениях в выборе.

## Класс `SelectionManager`

*   **Назначение:** Центральный менеджер, который отслеживает все зарегистрированные `SelectionManagerUser` и их состояние выбора.
*   **Атрибуты:**
    *   `selectionUsers` (list): Список всех зарегистрированных объектов `SelectionManagerUser`.
    *   `on_selection_changed` (list): Список callback-функций, которые будут вызваны при изменении выбора. Каждая функция будет вызвана с экземпляром `SelectionManager` в качестве аргумента.
    *   `last_selection` (`SelectionItemData` | None): Ссылка на данные последнего выбранного элемента.
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует списки `selectionUsers` и `on_selection_changed`.
    *   **`fire_selection_changed(self)`:** Вызывает все callback-функции из списка `on_selection_changed`.
    *   **`register_user(self, user: SelectionManagerUser)`:**
        *   Регистрирует `SelectionManagerUser` в менеджере.
        *   **Логика замены:** Пытается найти уже зарегистрированного пользователя с таким же хэшем (основанным на `selection_data`). Если найден, удаляет старого пользователя и добавляет нового, копируя состояние `selected` от старого к новому. *Примечание: В коде есть комментарий `todo debug this`, указывающий на возможные проблемы в этой логике.*
        *   Устанавливает `parent_manager` у пользователя на себя.
    *   **`unregister_user(self, user: SelectionManagerUser)`:** Удаляет пользователя из списка `selectionUsers` и сбрасывает его `parent_manager`.
    *   **`get_selection_data(self) -> list[SelectionItemData]`:** Возвращает список объектов `SelectionItemData` для всех **выбранных** пользователей.
    *   **`get_selection_as(self, type=None) -> list:`**
        *   Итерирует по всем **выбранным** пользователям.
        *   Для каждого вызывает метод `get_selection_as(type)` у его `selection_data`.
        *   Возвращает список результатов (исходных данных или конвертированных).
    *   **`clear_selection(self)`:** Снимает выбор со всех зарегистрированных пользователей (`set_selected(False)`) и вызывает `fire_selection_changed()`.

## Класс `SelectionManagerUser`

*   **Назначение:** Представляет объект, который может быть выбран. Обычно это обертка вокруг реального объекта данных или элемента GUI.
*   **Атрибуты:**
    *   `selected` (bool): Флаг, указывающий, выбран ли данный пользователь (по умолчанию `False`).
    *   `parent_manager` (`SelectionManager` | None): Ссылка на менеджер, в котором зарегистрирован этот пользователь.
    *   `selection_data` (`SelectionItemData`): Экземпляр `SelectionItemData`, хранящий фактические данные, связанные с этим выбором.
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует атрибуты по умолчанию и создает экземпляр `SelectionItemData`.
    *   **`set_selected(self, selected: bool)`:**
        *   Устанавливает состояние `selected`.
        *   Если `parent_manager` установлен, обновляет `last_selection` у менеджера и вызывает `parent_manager.fire_selection_changed()`.
    *   **`__hash__(self)`:**
        *   Определяет хэш пользователя на основе хэша объекта `self.selection_data.selection`. Если `selection` равен `None`, возвращает 0. Используется в `SelectionManager.register_user` для поиска дубликатов.

## Класс `SelectionItemData`

*   **Назначение:** Контейнер для данных, связанных с конкретным `SelectionManagerUser`. Позволяет хранить сам объект выбора и предоставлять его в различных форматах через конвертеры.
*   **Атрибуты:**
    *   `selection` (any): Фактический объект данных, который представляет выбор (например, объект модели, ID, путь к файлу и т.д.). По умолчанию `None`.
    *   `selection_converters` (dict): Словарь, где ключи - это типы (или строки-идентификаторы типов), а значения - функции-конвертеры. Конвертер принимает `self.selection` в качестве аргумента и возвращает его представление в запрошенном типе.
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует `selection` и `selection_converters`.
    *   **`get_selection_as(self, type)`:**
        *   Проверяет, есть ли конвертер для запрошенного `type` в `selection_converters`.
        *   Если есть, вызывает конвертер с `self.selection` и возвращает результат.
        *   Если конвертера нет, возвращает сам `self.selection`.

## Принцип работы и использование

1.  **Создание менеджера:** Создается экземпляр `SelectionManager`. Он может быть глобальным или специфичным для определенной части UI.
    ```python
    selection_manager = SelectionManager()
    ```
2.  **Подписка на изменения:** Компоненты, которым нужно реагировать на изменение выбора, подписываются на событие.
    ```python
    def handle_selection_change(manager: SelectionManager):
        selected_items_data = manager.get_selection_data()
        print(f"Selection changed! Selected count: {len(selected_items_data)}")
        # Обновить UI, активировать/деактивировать кнопки и т.д.
        
    selection_manager.on_selection_changed.append(handle_selection_change)
    # или selection_manager.on_selection_changed += handle_selection_change (если Event используется)
    ```
3.  **Создание и регистрация пользователей:** Для каждого элемента, который может быть выбран (например, строка в таблице, узел в графе), создается `SelectionManagerUser`.
    ```python
    # Предположим, my_data_object - это объект, который мы хотим сделать выбираемым
    my_data_object = {"id": 1, "name": "Item 1"} 
    
    user = SelectionManagerUser()
    user.selection_data.selection = my_data_object 
    
    # Добавление конвертера (опционально)
    def get_id(data):
        return data.get("id") if isinstance(data, dict) else None
    user.selection_data.selection_converters["id"] = get_id
    
    # Регистрация пользователя в менеджере
    selection_manager.register_user(user) 
    
    # Обычно 'user' ассоциируется с элементом GUI
    # gui_element.selection_user = user 
    ```
4.  **Обработка выбора/снятия выбора:** Когда пользователь взаимодействует с GUI (например, кликает на элемент), вызывается метод `set_selected` у соответствующего `SelectionManagerUser`.
    ```python
    # При клике на gui_element
    # current_state = gui_element.is_checked() # или другое состояние выбора
    # gui_element.selection_user.set_selected(current_state) 
    
    # Пример: выбрать первого пользователя
    if selection_manager.selectionUsers:
       selection_manager.selectionUsers[0].set_selected(True) 
    ```
    Вызов `set_selected` автоматически уведомляет менеджера, который затем вызывает всех подписчиков (`handle_selection_change`).
5.  **Получение выбранных данных:** Подписчики или другие части кода могут получить данные о выбранных элементах.
    ```python
    # Получить список всех SelectionItemData для выбранных
    selected_data_items = selection_manager.get_selection_data() 
    
    # Получить список ID выбранных элементов (используя конвертер)
    selected_ids = selection_manager.get_selection_as("id") 
    print(f"Selected IDs: {selected_ids}")
    
    # Получить список исходных объектов выбора
    selected_raw_objects = selection_manager.get_selection_as(None) # или просто get_selection_as()
    print(f"Selected raw objects: {selected_raw_objects}")
    ```
6.  **Очистка выбора:**
    ```python
    selection_manager.clear_selection() 
    ```

Эта система обеспечивает централизованное управление состоянием выбора и позволяет разным компонентам легко взаимодействовать с ним.
