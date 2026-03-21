# Botbox Framework

Фреймворк для создания 2D игр и интерактивных приложений с поддержкой искусственного интеллекта.

## Основные компоненты

### Ядро системы

1. **[Environment System](Environment.md)**
   - Базовая архитектура приложения
   - Управление сущностями и контроллерами
   - Жизненный цикл приложения

2. **[Data Board](data_board.md)**
   - Система обмена данными
   - Отладочная информация
   - Мониторинг состояния

3. **[Behavior Trees](behTree.md)**
   - Система деревьев поведения
   - Компоненты ИИ
   - Управление действиями

### Графическая подсистема

1. **[Animation System](animation.md)**
   - Управление анимациями
   - Спрайтовые анимации
   - Временные интервалы

2. **[Tile Map](tileMap.md)**
   - Тайловые карты
   - Управление слоями
   - Оптимизация рендеринга

3. **[Renderers](pyglet_render.md)**
   - Pyglet рендерер
   - Система камеры
   - Управление окном

### Игровые компоненты

1. **[RPG Entities](rpg_ent.md)**
   - Базовые игровые сущности
   - Система характеристик
   - Взаимодействие объектов

## Примеры приложений

### 1. [RPG Demo](app/py_rpg/index.md)
- Демонстрация базового функционала
- Пример игровой механики
- Интеграция компонентов

### 2. [Cartographer](app/cartographer/index.md)
- Редактор тайловых карт
- Работа со слоями
- Управление ресурсами

### 3. [Fishing Simulator](ribalka/index.md)
- Физическая симуляция
- Поведение ИИ
- Пользовательский интерфейс

## Быстрый старт

### Установка
```bash
pip install SLM-botbox
```

### Простое приложение
```python
from SLM.botbox.Environment import Environment
from SLM.botbox.rpg_ent import Actor

# Создание окружения
env = Environment()

# Добавление сущности
actor = Actor()
env.AddChild(actor)

# Запуск
env.Start()
```

## Архитектура

### 1. Сущности и контроллеры
```python
# Создание сущности
class GameEntity(EnvironmentEntity):
    def __init__(self):
        super().__init__()
        self.AddController(MyController())

# Создание контроллера
class MyController(EntityController):
    def update(self):
        # Логика обновления
        pass
```

### 2. Компоненты поведения
```python
# Создание дерева поведения
behavior = BehaviorTree()
sequence = Sequence()
sequence.add_child(ActionNode(move_action))
sequence.add_child(ActionNode(attack_action))
```

### 3. Рендеринг
```python
# Настройка рендерера
renderer = PyGletRender()
renderer.game_screen_size = (800, 600)
env.AddController(renderer)
```

## Основные понятия

1. **Entity (Сущность)**
   - Базовый игровой объект
   - Контейнер для контроллеров
   - Часть иерархии сцены

2. **Controller (Контроллер)**
   - Компонент с логикой
   - Управление поведением
   - Обработка событий

3. **Behavior (Поведение)**
   - Деревья поведения
   - Искусственный интеллект
   - Реакция на события

## Инструменты разработки

1. **Отладка:**
   - DataBoard для мониторинга
   - Визуализация состояний
   - Логирование событий

2. **Редакторы:**
   - Cartographer для карт
   - Редактор поведения
   - Настройка сущностей

3. **Тестирование:**
   - Примеры приложений
   - Тестовые сценарии
   - Профилирование

## TODO

1. **Функциональность:**
   - 3D поддержка
   - Сетевая игра
   - Физический движок

2. **Инструменты:**
   - Визуальный редактор
   - Система сборки
   - Управление ресурсами

3. **Документация:**
   - Учебные материалы
   - API Reference
   - Примеры кода

## Ссылки

- [Исходный код](https://github.com/user/SLM-botbox)
- [Документация](https://botbox.readthedocs.io)
- [Примеры](https://github.com/user/SLM-botbox/examples)
