# Factory Pattern Implementations (`factory.py`)

Этот модуль предоставляет базовые классы и утилиты для реализации паттерна проектирования "Фабрика" (Factory) и связанных с ним концепций, таких как репозиторий фабрик. Паттерн Фабрика используется для инкапсуляции логики создания объектов, позволяя создавать объекты без указания их конкретных классов.

## Класс `Factory`

*   **Назначение:** Простой базовый класс для реализации паттерна Фабричный Метод или Абстрактная Фабрика. Определяет общий интерфейс для создания продуктов.
*   **Методы:**
    *   **`build(self, **kwargs)`:** Метод, предназначенный для создания и возврата "продукта" (объекта). В базовом классе возвращает `None`. Подклассы должны переопределить этот метод для реализации конкретной логики создания. `**kwargs` позволяют передавать параметры, необходимые для создания объекта.
    *   **`is_supported(self, **kwargs)`:** Метод для проверки, может ли данная фабрика создать продукт с указанными параметрами `**kwargs`. В базовом классе всегда возвращает `True`. Подклассы могут переопределить этот метод для более сложной логики проверки.

## Класс `StaticFactoryRepo`

*   **Назначение:** Реализует статический репозиторий (хранилище) для экземпляров `Factory`. Позволяет регистрировать фабрики по строковому ключу (пути) и получать продукты от них.
*   **Статический атрибут:**
    *   `factories` (dict[str, `Factory`]): Словарь, где ключи - это строки (пути/идентификаторы), а значения - экземпляры классов, реализующих интерфейс `Factory`.
*   **Статические методы:**
    *   **`add_factory(path, factory)`:** Регистрирует экземпляр `factory` в репозитории под ключом `path`.
    *   **`get_product(path, **kwargs)`:** Находит фабрику по ключу `path` в репозитории и, если найдена, вызывает ее метод `build(**kwargs)` для получения продукта. Возвращает продукт или `None`, если фабрика не найдена.
    *   **`get_factoriesList(self, prefix)`:** *(Примечание: метод объявлен как статический, но принимает `self`, что некорректно. Вероятно, должен быть статическим или методом класса)*. Возвращает список ключей из `factories`, которые начинаются с указанного `prefix`.

## Класс `StaticFactory`

*   **Назначение:** Еще один базовый класс для фабрик. В отличие от `Factory`, он не имеет метода `is_supported`, но добавляет статический метод-хелпер для валидации аргументов. Этот класс используется как база для `DataConverterFactory` и `BindFactoryBase` в других модулях (`DAL.py`, `binding/bind.py`), предполагая, возможно, использование фабрик как утилит или синглтонов без необходимости явного хранения экземпляров в `StaticFactoryRepo`.
*   **Методы:**
    *   **`build(self, **kwargs)`:** Аналогично `Factory.build`, предназначен для создания продукта. Возвращает `None` в базовом классе.
    *   **`is_kwargs_valid(self, **kwargs)`:** Метод для проверки валидности переданных аргументов `**kwargs`. В базовом классе всегда возвращает `True`.
*   **Статический метод:**
    *   **`arg_valid_by_type(prop_name, prop_type: type, default=None, **kwargs)`:** Вспомогательный метод для извлечения аргумента по имени (`prop_name`) из `**kwargs`. Проверяет, соответствует ли тип извлеченного аргумента ожидаемому `prop_type`. Если аргумент отсутствует или имеет неверный тип, возвращает значение `default`.

## Примеры использования

Классы `Factory` и `StaticFactory` служат основой для создания более конкретных фабрик в других частях приложения. `StaticFactoryRepo` может использоваться для централизованного управления различными фабриками.

```python
from SLM.appGlue.DesignPaterns.factory import Factory, StaticFactoryRepo, StaticFactory

# --- Пример использования Factory ---
class ConcreteProductA:
    def __str__(self): return "Product A"

class ConcreteProductB:
    def __str__(self): return "Product B"

class SimpleFactory(Factory):
    def build(self, **kwargs):
        product_type = kwargs.get("type")
        if product_type == "A":
            return ConcreteProductA()
        elif product_type == "B":
            return ConcreteProductB()
        return None # Или выбросить исключение

    def is_supported(self, **kwargs):
        return kwargs.get("type") in ["A", "B"]

factory_instance = SimpleFactory()
if factory_instance.is_supported(type="A"):
    product_a = factory_instance.build(type="A")
    print(product_a) # Output: Product A

# --- Пример использования StaticFactoryRepo ---
StaticFactoryRepo.add_factory("simple/main", factory_instance)

product_a_repo = StaticFactoryRepo.get_product("simple/main", type="A")
print(product_a_repo) # Output: Product A

product_c_repo = StaticFactoryRepo.get_product("simple/main", type="C")
print(product_c_repo) # Output: None

# --- Пример использования StaticFactory ---
class ConfigurableProduct:
    def __init__(self, name="Default"):
        self.name = name
    def __str__(self): return f"ConfigurableProduct(name='{self.name}')"

class ConfigurableFactory(StaticFactory):
    def build(self, **kwargs):
        # Используем хелпер для получения аргумента
        name = self.arg_valid_by_type("name", str, default="Unnamed", **kwargs)
        if self.is_kwargs_valid(**kwargs): # Проверка валидности (здесь простая)
             return ConfigurableProduct(name=name)
        return None
        
    def is_kwargs_valid(self, **kwargs):
        # Пример проверки - имя не должно быть пустым
        name = kwargs.get("name")
        return name is not None and name != ""

config_factory = ConfigurableFactory()
product1 = config_factory.build(name="MyProduct")
print(product1) # Output: ConfigurableProduct(name='MyProduct')

product2 = config_factory.build() # Имя не передано
print(product2) # Output: ConfigurableProduct(name='Unnamed')

product3 = config_factory.build(name="") # Невалидное имя
print(product3) # Output: None 
```

Эти классы предоставляют гибкие инструменты для реализации различных вариаций паттерна Фабрика.
