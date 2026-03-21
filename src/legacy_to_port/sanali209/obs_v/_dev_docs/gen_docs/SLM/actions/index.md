# Actions Module

Этот модуль отвечает за определение, регистрацию и выполнение конкретных атомарных операций ("действий") в рамках SLM. Он обеспечивает базовую структуру для создания новых действий и централизованный механизм для их управления.

## Основные компоненты (`action_module.py`)

### `AppAction` (Базовый класс)
Абстрактный базовый класс, от которого должны наследоваться все конкретные действия.

*   **`__init__(self, **args)`:** Конструктор. Принимает именованные аргументы. Аргументы `name` и `description` обрабатываются особо, остальные сохраняются в `self.args`.
*   **`run(self, *args, **kwargs)`:** Основной метод, который должен быть переопределен в дочерних классах для выполнения логики действия.
*   **`run_with_delayed_args(self)`:** Запускает метод `run`, передавая ему аргументы, сохраненные в `self.args` при инициализации.
*   **`is_supported(self, context)`:** Метод для проверки, поддерживается ли действие в данном контексте (по умолчанию `True`). Должен быть переопределен при необходимости.
*   **`is_can_run(self, context)`:** Метод для проверки, может ли действие быть выполнено в данном контексте (по умолчанию `True`). Должен быть переопределен при необходимости.
*   `run_on_thread_queue(self)`: Заглушка, вероятно, для будущего асинхронного выполнения.

### `ActionManager`
Класс для управления (регистрации и выполнения) действиями.

*   **`actions: List[AppAction]`:** Список для хранения зарегистрированных экземпляров действий.
*   **`register(self)`:** Метод-декоратор для регистрации классов действий. При декорировании класса он создает экземпляр этого класса и добавляет его в список `actions`.
*   **`get_action_by_name(self, name: str)`:** Находит и возвращает зарегистрированное действие по его имени (`action.name`).
*   **`run_action_by_name(self, name: str, *args, **kwargs)`:** Находит действие по имени и выполняет его метод `run`.
*   **`run_action(self, action: type, *args, **kwargs)`:** Создает экземпляр указанного класса действия (проверяя, что это подкласс `AppAction`) и выполняет его метод `run`.

## Конкретные действия

Конкретные действия определяются в других файлах этого модуля (например, `locate_in_exp.py`) или в поддиректориях (например, `appActions/`). Они должны наследоваться от `AppAction` и реализовывать метод `run`.

*   [Locate In Explorer Action](locate_in_exp.md)
*   [App Actions](appActions/index.md) *(Placeholder - need to document this subdirectory)*

## Пример использования (Регистрация и выполнение)

```python
# В файле определения действия (например, my_action.py)
from Python.SLM.actions.action_module import AppAction, ActionManager

action_manager = ActionManager() # Обычно создается один экземпляр менеджера

@action_manager.register()
class MyTestAction(AppAction):
    name = "test_action"
    description = "A simple test action."

    def run(self, message: str):
        print(f"Running test action with message: {message}")
        return True

# В другом месте кода для выполнения действия
# from my_action import action_manager # Импортируем менеджер

action_manager.run_action_by_name("test_action", message="Hello World!") 
# Или
# from my_action import MyTestAction
# action_manager.run_action(MyTestAction, message="Hello Again!")
```

## Связанные концепции

*   [Core Concepts](../core_concepts.md)
*   [Architecture](../architecture.md)
*   [Chains Module](../chains/index.md) (Цепочки могут состоять из последовательности действий)
