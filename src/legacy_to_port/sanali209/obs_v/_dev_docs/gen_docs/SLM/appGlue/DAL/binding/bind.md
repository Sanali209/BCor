# Data Binding System (`bind.py`)

Этот модуль реализует систему связывания данных (Data Binding), позволяющую устанавливать связь между свойствами объектов. Когда значение одного свойства изменяется, связанное с ним свойство автоматически обновляется. Система поддерживает одностороннее и двустороннее связывание, преобразование типов данных с помощью конвертеров и (потенциально) валидацию.

## Зависимости

*   `SLM.appGlue.DAL.DAL.ForwardConverter`, `DataConverterFactory`, `GlueDataConverter`: Используются для преобразования данных между связанными свойствами.
*   `SLM.appGlue.DesignPaterns.factory.StaticFactory`: Базовый класс для `BindFactoryBase`.

## Основные компоненты

### 1. `BindingProperty`

*   **Назначение:** Представляет собой "наблюдаемое" свойство. Хранит значение и уведомляет зарегистрированных наблюдателей (`BindingObserver`) и слушателей (`call_backs`) при изменении этого значения.
*   **Атрибуты:**
    *   `observers` (list[`BindingObserver`]): Список зарегистрированных наблюдателей связывания.
    *   `_cached_value`: Внутреннее хранилище для значения свойства.
    *   `call_backs` (list[Callable]): Список простых функций обратного вызова, вызываемых при изменении значения.
*   **Методы:**
    *   **`__init__(self, default=None)`:** Инициализирует свойство значением по умолчанию.
    *   **`register(self, observer: BindingObserver)`:** Регистрирует наблюдателя, устанавливает ему ссылку на это свойство (`source_property`) и вызывает `observer.on_registered()`.
    *   **`bind(self, bind_target=None, **kwargs)`:** Упрощенный метод для создания и регистрации связывания. Использует `BindFactoryBase` для создания `BindingObserver` на основе `bind_target` и других параметров.
    *   **`fire_prop_changed(self, sender=None)`:** Уведомляет всех наблюдателей (кроме `sender`, если указан) и вызывает все `call_backs`.
    *   **`val` (property):** Геттер и сеттер для доступа к значению свойства. Сеттер вызывает `set_value`.
    *   **`set_value(self, value, sender=None)`:** Устанавливает новое значение и инициирует уведомление через `fire_prop_changed`. Параметр `sender` используется для предотвращения циклического обновления в двусторонних связываниях.
    *   **`add_listener(self, delegate)`:** Добавляет простую функцию обратного вызова в `call_backs`.

### 2. `BindingObserver`

*   **Назначение:** Базовый класс для объектов, которые "наблюдают" за `BindingProperty` и реагируют на его изменения. Может преобразовывать и валидировать значения.
*   **Атрибуты:**
    *   `source_property` (`BindingProperty`): Ссылка на свойство-источник.
    *   `converter` (`GlueDataConverter`): Конвертер для преобразования значения из `source_property` (по умолчанию `ForwardConverter`).
    *   `validator` (`damValidator`): Валидатор значения (по умолчанию фиктивный `damValidator`). *(Опечатка в имени класса: "dam" вместо "dummy")*
    *   `callback` (Callable | None): Опциональный callback, вызываемый при изменении свойства с уже конвертированным значением.
*   **Методы:**
    *   **`on_registered(self)`:** Вызывается при регистрации наблюдателя у `BindingProperty`. По умолчанию вызывает `callback` с начальным конвертированным значением.
    *   **`on_prop_changed(self, prop, val)`:** Метод для переопределения в подклассах. Вызывается, когда `source_property` изменяется. `val` - это уже конвертированное значение.
    *   **`prop_changed(self, prop)`:** Вызывается `BindingProperty`. Конвертирует новое значение, вызывает `on_prop_changed` и `callback`.
    *   **`set_prop_val(self, value)`:** Устанавливает значение в `source_property`, предварительно применив обратное преобразование (`ConvertBack`). Используется для двустороннего связывания.
    *   **`get_prop_val(self)`:** Получает текущее значение из `source_property` и применяет к нему преобразование (`Convert`).

### 3. `PropBinding(BindingObserver)`

*   **Назначение:** Конкретный наблюдатель, реализующий связывание одного `BindingProperty` (источника) с другим (`target_property`).
*   **Атрибуты:**
    *   `target_property` (`BindingProperty`): Свойство-цель, которое будет обновляться.
    *   `listener` (Callable): Ссылка на метод `target_changed`, используется для двустороннего связывания.
*   **Методы:**
    *   **`__init__(self, target_prop, converter=None, one_way=False)`:** Инициализирует связывание. Если `one_way=False` (двустороннее связывание), подписывается на изменения `target_property` через `add_listener`.
    *   **`target_changed(self, value)`:** Вызывается при изменении `target_property` (в режиме двустороннего связывания). Вызывает `set_prop_val`, чтобы обновить `source_property`.
    *   **`on_registered(self)`:** При регистрации устанавливает начальное значение `target_property` из `source_property`.
    *   **`on_prop_changed(self, prop, val)`:** При изменении `source_property` обновляет `target_property`.

### 4. Декларация Свойств (`PropInfo`, `PropUser`, `PropDispatcher`)

*   **`PropInfo`**:
    *   **Назначение:** Дескриптор Python, используемый для декларативного определения `BindingProperty` внутри класса.
    *   **Атрибуты:** `defaulth`, `prop_name`, `persist`.
    *   **Методы `__get__`, `__set__`:** Перенаправляют доступ к атрибуту на соответствующий `BindingProperty` в словаре `props` экземпляра.
*   **`PropUser`**:
    *   **Назначение:** Базовый класс или миксин для классов, использующих `PropInfo`.
    *   **Логика `__init__`:** При инициализации экземпляра автоматически находит все атрибуты типа `PropInfo`, создает для них соответствующие `BindingProperty` и сохраняет их в словаре `self.props`.
    *   **Атрибут `dispatcher` (`PropDispatcher`):** Предоставляет доступ к `BindingProperty` через точечную нотацию (например, `instance.dispatcher.my_prop`).
*   **`PropDispatcher`**:
    *   **Назначение:** Вспомогательный класс, позволяющий получить доступ к `BindingProperty` из словаря `props` через `__getattr__`.

### 5. Фабрика Связываний (`BindFactoryBase`)

*   **Назначение:** Статическая фабрика для создания экземпляров `BindingObserver` (например, `PropBinding`).
*   **Атрибут `bind_dict`:** Словарь, сопоставляющий типы целевых объектов (например, `BindingProperty`) с классами наблюдателей (`PropBinding`).
*   **Методы:**
    *   `build(**kwargs)`: Основной метод создания. Получает тип `bind_target`, находит соответствующий класс наблюдателя в `bind_dict`, преобразует параметры (например, создает экземпляр конвертера по имени с помощью `DataConverterFactory`) и создает экземпляр наблюдателя.
    *   `is_supported(**kwargs)`: Проверяет, поддерживается ли тип `bind_target`.

## Пример использования

```python
from SLM.appGlue.DAL.binding.bind import BindingProperty, PropUser, PropInfo, BindFactoryBase
from SLM.appGlue.DAL.DAL import GlueDataConverter, DataConverterFactory

# --- Регистрация конвертера (пример) ---
class OffsetConverter(GlueDataConverter):
    def Convert(self, data):
        return data + 10
    def ConvertBack(self, data):
        return data - 10

DataConverterFactory.converter_dict["offset"] = OffsetConverter() 
# Обычно регистрация происходит централизованно

# --- Класс с наблюдаемыми свойствами ---
class MyViewModel(PropUser):
    value1 = PropInfo(default=0)
    value2 = PropInfo(default="")
    value3 = PropInfo(default=100)

# --- Создание экземпляров ---
vm1 = MyViewModel()
vm2 = MyViewModel()

# --- Простое прослушивание изменений ---
def value1_changed(new_value):
    print(f"vm1.value1 changed to: {new_value}")
    
vm1.dispatcher.value1.add_listener(value1_changed)

vm1.value1 = 5 # Output: vm1.value1 changed to: 5

# --- Двустороннее связывание ---
# Связываем vm1.value1 и vm2.value1 напрямую
vm1.dispatcher.value1.bind(vm2.dispatcher.value1) 

print(f"Initial values: vm1.value1={vm1.value1}, vm2.value1={vm2.value1}") 
# Output: Initial values: vm1.value1=5, vm2.value1=5 (vm2 обновился при регистрации)

vm1.value1 = 10 # Output: vm1.value1 changed to: 10
print(f"After vm1 change: vm1.value1={vm1.value1}, vm2.value1={vm2.value1}") 
# Output: After vm1 change: vm1.value1=10, vm2.value1=10

vm2.value1 = 20
print(f"After vm2 change: vm1.value1={vm1.value1}, vm2.value1={vm2.value1}") 
# Output: vm1.value1 changed to: 20
# Output: After vm2 change: vm1.value1=20, vm2.value1=20

# --- Связывание с конвертером ---
# Связываем vm1.value3 и vm2.value3 с конвертером "offset"
vm1.dispatcher.value3.bind(vm2.dispatcher.value3, converter="offset")

print(f"\nInitial values with offset: vm1.value3={vm1.value3}, vm2.value3={vm2.value3}")
# Output: Initial values with offset: vm1.value3=100, vm2.value3=110 (vm2 = vm1 + 10)

vm1.value3 = 50
print(f"After vm1 change: vm1.value3={vm1.value3}, vm2.value3={vm2.value3}")
# Output: After vm1 change: vm1.value3=50, vm2.value3=60 (vm2 = vm1 + 10)

vm2.value3 = 90 # Устанавливаем значение в vm2
print(f"After vm2 change: vm1.value3={vm1.value3}, vm2.value3={vm2.value3}")
# Output: After vm2 change: vm1.value3=80, vm2.value3=90 (vm1 = vm2 - 10)

```

Эта система предоставляет мощный механизм для синхронизации данных между различными частями приложения, особенно полезный в архитектурах типа MVVM (Model-View-ViewModel) или MVC (Model-View-Controller).
