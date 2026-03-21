# Specification Pattern (`specification.py`)

Этот модуль реализует паттерн проектирования "Спецификация" (Specification). Он позволяет определять бизнес-правила или критерии выбора в виде отдельных объектов-спецификаций. Эти спецификации можно комбинировать с помощью логических операторов (И, ИЛИ, НЕ) для создания более сложных правил. Модуль также включает парсер для создания спецификаций из строковых запросов и строитель для их программного конструирования.

## Зависимости

*   `abc.ABC`, `abstractmethod`: Для определения абстрактного базового класса `Specification`.
*   `typing.Dict`: Для аннотации типов в `SpecificationBuilder`.

## Основные компоненты

### 1. Базовый класс `Specification(ABC)`

*   **Назначение:** Абстрактный базовый класс для всех спецификаций.
*   **Абстрактный метод:**
    *   `is_satisfied_by(self, candidate)`: Основной метод спецификации. Должен быть реализован в подклассах. Принимает объект-кандидат и возвращает `True`, если кандидат удовлетворяет правилу, инкапсулированному в спецификации, иначе `False`.
*   **Методы для комбинирования:**
    *   `and_specification(self, specification)`: Возвращает новую спецификацию `AndSpecification`, которая объединяет текущую спецификацию (`self`) и переданную `specification` с помощью логического "И".
    *   `or_specification(self, specification)`: Возвращает новую спецификацию `OrSpecification`, которая объединяет текущую спецификацию (`self`) и переданную `specification` с помощью логического "ИЛИ".
    *   *(Примечание: Метод для "НЕ" (`not_specification`) не реализован напрямую в базовом классе, но есть отдельный класс `NotSpecification`)*.

### 2. Композитные Спецификации

*   **`AllSpecification(Specification)`**:
    *   Спецификация, которая всегда удовлетворяется (`is_satisfied_by` всегда возвращает `True`). Полезна как нейтральный элемент или заглушка.
*   **`AndSpecification(Specification)`**:
    *   Принимает две спецификации (`spec1`, `spec2`) в конструкторе.
    *   `is_satisfied_by(candidate)` возвращает `True` только если **обе** вложенные спецификации удовлетворяются кандидатом.
*   **`OrSpecification(Specification)`**:
    *   Принимает две спецификации (`spec1`, `spec2`) в конструкторе.
    *   `is_satisfied_by(candidate)` возвращает `True` если **хотя бы одна** из вложенных спецификаций удовлетворяется кандидатом.
*   **`NotSpecification(Specification)`**:
    *   Принимает одну спецификацию (`spec1`) в конструкторе.
    *   `is_satisfied_by(candidate)` возвращает `True` если вложенная спецификация **не** удовлетворяется кандидатом (инвертирует результат `spec1.is_satisfied_by`).

### 3. Парсинг Строковых Запросов

*   **`NamedSpecificationSubParser`**:
    *   **Назначение:** Вспомогательный класс для парсинга именованных спецификаций внутри строки запроса.
    *   **Атрибуты:** `spec_name` (строка-префикс), `SpecInstance` (класс конкретной спецификации).
    *   **Метод `parse(self, query)`:** Проверяет, начинается ли `query` с `spec_name`. Если да, создает экземпляр `SpecInstance`, передавая ему оставшуюся часть строки `query` (после префикса) в качестве аргумента. Иначе возвращает `None`.
*   **`SpecificationQueryParser`**:
    *   **Назначение:** Парсит строку запроса, представляющую собой комбинацию спецификаций, и создает соответствующий объект `Specification`.
    *   **Атрибуты:** `named_spec_sub_parsers` (list[`NamedSpecificationSubParser`]): Список зарегистрированных суб-парсеров для конкретных именованных спецификаций.
    *   **Методы:**
        *   `parse(self, query)` / `parse_query(self, query)`: Рекурсивно разбирает строку запроса. Поддерживает скобки `()`, операторы `NOT `, `AND `, `OR `. Для базовых (некомпозитных) спецификаций использует зарегистрированные `named_spec_sub_parsers`.
        *   `parse_and_or_query(self, query, spec_type)`: Вспомогательный метод для парсинга `AND` и `OR` выражений. *(Примечание: Логика этого метода кажется избыточной и во многом повторяет `parse_query`. Возможно, его можно упростить или объединить с `parse_query`)*.
    *   **Ограничения парсера:** Парсер довольно простой и может быть не устойчив к сложным или некорректно отформатированным запросам. Он ожидает префиксную нотацию для операторов (`AND spec1 spec2` - не поддерживается, ожидается `AND (spec1) (spec2)` или использование суб-парсеров). Логика разбора `AND`/`OR` внутри `parse_and_or_query` выглядит неполной или некорректной для обработки нескольких операндов без явных скобок.

### 4. Строитель Спецификаций (`SpecificationBuilder`)

*   **Назначение:** Предоставляет текучий интерфейс (fluent interface) для программного создания сложных спецификаций.
*   **Атрибуты:**
    *   `named_spec` (Dict[str, type]): Словарь для регистрации классов именованных спецификаций по их именам.
    *   `current_specification`: Текущая построенная спецификация.
    *   `combination_specification`: Временное хранилище для `AndSpecification` или `OrSpecification` в процессе построения.
    *   `is_combination_step`: Флаг, указывающий, что ожидается вторая часть для `AND` или `OR`.
*   **Методы:**
    *   `add_specification(self, name, value)`: Добавляет именованную спецификацию. Если `is_combination_step` установлен, эта спецификация становится вторым операндом для `AND`/`OR`. Иначе она становится `current_specification`.
    *   `add_and(self)`: Начинает операцию `AND`. Текущая спецификация становится первым операндом.
    *   `add_or(self)`: Начинает операцию `OR`. Текущая спецификация становится первым операндом.
    *   `add_not(self)`: Применяет `NOT` к текущей спецификации.
    *   `build(self)`: Возвращает финальную построенную спецификацию (`current_specification`).

## Примеры использования

```python
from SLM.appGlue.DesignPaterns.specification import (
    Specification, AndSpecification, OrSpecification, NotSpecification, AllSpecification,
    SpecificationBuilder, NamedSpecificationSubParser, SpecificationQueryParser
)

# --- Пример конкретных спецификаций ---
class IsPositive(Specification):
    def is_satisfied_by(self, candidate):
        return isinstance(candidate, (int, float)) and candidate > 0

class IsEven(Specification):
    def is_satisfied_by(self, candidate):
        return isinstance(candidate, int) and candidate % 2 == 0

class HasLength(Specification):
    def __init__(self, length):
        self.length = int(length) # Парсер передает строку
    def is_satisfied_by(self, candidate):
        return hasattr(candidate, '__len__') and len(candidate) == self.length

# --- Прямое использование ---
spec1 = IsPositive()
spec2 = IsEven()

positive_and_even = spec1.and_specification(spec2) # или AndSpecification(spec1, spec2)
positive_or_even = spec1.or_specification(spec2)   # или OrSpecification(spec1, spec2)
not_positive = NotSpecification(spec1)

print(f" 5 is positive_and_even: {positive_and_even.is_satisfied_by(5)}") # False
print(f" 6 is positive_and_even: {positive_and_even.is_satisfied_by(6)}") # True
print(f"-2 is positive_or_even: {positive_or_even.is_satisfied_by(-2)}") # True (т.к. четное)
print(f" 7 is not_positive: {not_positive.is_satisfied_by(7)}")         # False
print(f"-3 is not_positive: {not_positive.is_satisfied_by(-3)}")         # True

# --- Использование Строителя ---
builder = SpecificationBuilder()
builder.named_spec = { # Регистрация классов спецификаций
    "positive": IsPositive,
    "even": IsEven,
    "length": HasLength 
}

# Строим: (positive AND even) OR length(5)
spec_built = builder.add_specification("positive", None) \
                    .add_and() \
                    .add_specification("even", None) \
                    .add_or() \
                    .add_specification("length", 5) \
                    .build()

print(f"\nBuilder test:")
print(f" 6 satisfies built spec: {spec_built.is_satisfied_by(6)}")       # True (positive and even)
print(f" 7 satisfies built spec: {spec_built.is_satisfied_by(7)}")       # False
print(f"'hello' satisfies built spec: {spec_built.is_satisfied_by('hello')}") # True (length 5)
print(f"'world' satisfies built spec: {spec_built.is_satisfied_by('world')}") # True (length 5)

# --- Использование Парсера ---
parser = SpecificationQueryParser()
# Регистрация суб-парсеров
parser.named_spec_sub_parsers.append(NamedSpecificationSubParser("positive", IsPositive))
parser.named_spec_sub_parsers.append(NamedSpecificationSubParser("even", IsEven))
parser.named_spec_sub_parsers.append(NamedSpecificationSubParser("length:", HasLength)) # С двоеточием для отделения значения

# Запрос: "OR (AND positive even) (length:5)" - примерная структура, которую парсер может ожидать
# Замечание: Текущий парсер может иметь проблемы с таким синтаксисом.
# Протестируем более простую структуру, которую он точно должен обработать:
query1 = "positive"
query2 = "NOT even"
# query3 = "AND positive even" # Может не сработать без скобок или другой структуры

try:
    spec_parsed1 = parser.parse(query1)
    print(f"\nParser test:")
    print(f" 4 satisfies '{query1}': {spec_parsed1.is_satisfied_by(4)}") # True
    
    spec_parsed2 = parser.parse(query2)
    print(f" 4 satisfies '{query2}': {spec_parsed2.is_satisfied_by(4)}") # False
    print(f" 3 satisfies '{query2}': {spec_parsed2.is_satisfied_by(3)}") # True

    # Пример с именованной спецификацией с параметром
    query_len = "length:4"
    spec_len = parser.parse(query_len)
    print(f"'test' satisfies '{query_len}': {spec_len.is_satisfied_by('test')}") # True
    print(f"'abc' satisfies '{query_len}': {spec_len.is_satisfied_by('abc')}")   # False

except Exception as e:
    print(f"Error parsing query: {e}")

```

Паттерн Спецификация очень полезен для создания гибких и переиспользуемых правил фильтрации или валидации данных. Строитель и парсер предоставляют удобные способы создания этих спецификаций.
