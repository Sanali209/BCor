# Abstract Builder (`AbstractBuilder.py`)

Этот модуль предоставляет абстрактный базовый класс `Builder`, предназначенный для реализации паттерна проектирования "Строитель" (Builder).

## Зависимости

*   `abc.ABC`, `abstractmethod`: Для определения абстрактного базового класса.

## Класс `Builder(ABC)`

*   **Назначение:** Служит базовым классом для конкретных строителей. Паттерн Строитель используется для инкапсуляции процесса создания сложного объекта, позволяя создавать различные представления объекта с использованием одного и того же процесса конструирования.
*   **Атрибуты:**
    *   `_product`: Предполагается, что этот атрибут будет хранить создаваемый объект (продукт). Он может быть инициализирован в `__init__` или создан/модифицирован в методах конкретных подклассов-строителей.
*   **Методы:**
    *   **`__init__(self, product=None)`:** Конструктор. Позволяет опционально передать начальный объект `product`. Конкретные строители могут переопределить этот метод для создания или инициализации своего `_product`.
    *   **`build(self)`:** Возвращает готовый продукт (`_product`). Предполагается, что к моменту вызова этого метода продукт уже сконструирован (либо в `__init__`, либо через вызов других методов строителя).

## Принцип использования

1.  Создаются конкретные классы-строители, наследующие от `Builder`.
2.  В этих подклассах реализуются методы для построения различных частей сложного объекта (например, `build_part_a()`, `set_configuration()`, etc.). Эти методы обычно модифицируют атрибут `_product`.
3.  Клиентский код использует экземпляр конкретного строителя, вызывает его методы для конфигурации и построения объекта, а затем вызывает метод `build()` для получения финального результата.

```python
from SLM.appGlue.DesignPaterns.AbstractBuilder import Builder

# Пример сложного объекта
class Report:
    def __init__(self):
        self.title = ""
        self.content = ""
        self.footer = ""

    def __str__(self):
        return f"--- {self.title} ---\n{self.content}\n--- {self.footer} ---"

# Пример конкретного строителя
class SimpleReportBuilder(Builder):
    def __init__(self):
        # Создаем продукт в конструкторе строителя
        super().__init__(Report()) 

    def set_title(self, title):
        self._product.title = title
        return self # Возвращаем self для текучего интерфейса (fluent interface)

    def add_content(self, text):
        self._product.content += text + "\n"
        return self

    def set_footer(self, footer):
        self._product.footer = footer
        return self
        
    # Метод build() наследуется от базового класса

# Использование строителя
builder = SimpleReportBuilder()

report = builder.set_title("My Simple Report") \
                .add_content("This is the first line.") \
                .add_content("This is the second line.") \
                .set_footer("End of Report") \
                .build()

print(report)
# Output:
# --- My Simple Report ---
# This is the first line.
# This is the second line.
# 
# --- End of Report --- 
```

Этот базовый класс предоставляет простую основу для реализации паттерна Строитель.
