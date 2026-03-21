# RPG Entities (`rpg_ent.py`)

Этот модуль реализует базовые игровые сущности и их контроллеры, используемые в RPG-подобных играх.

## Классы

### `Stats`
```python
class Stats:
    def __init__(self):
        self.hp = 100
        self.mp = 100
        # ... другие характеристики ...
```
Контейнер базовых RPG-характеристик персонажа:
- Здоровье (hp)
- Мана (mp)
- Выносливость (stamina)
- Сила (strength)
- Защита (defense)
- Магия (magic)
- Скорость (speed)
- Удача (luck)
- Дальность атаки (attack_range)

### `Actor`
```python
class Actor(Pawn):
    def __init__(self):
        super().__init__()
        self.actor_size = (64, 64)
        # ... другие поля ...
```

**Базовый класс для всех игровых сущностей.**

#### Атрибуты:
- `actor_size`: Размер спрайта (по умолчанию 64x64)
- `actor_sprite`: Pygame спрайт для визуализации
- `stats`: Характеристики персонажа
- `key_color`: Цвет для прозрачности
- `forward`: Вектор направления движения

#### Методы:
- `update()`: Обновляет позицию спрайта относительно камеры
- `load_sprite(sprite_path)`: Загружает спрайт из файла
- `loadSpriteFromSheet(sheet_path, position, size)`: Загружает спрайт из спрайтового листа

### `Player`
```python
class Player(Actor):
    def __init__(self):
        super().__init__()
        self.name = 'player'
        # ... инициализация ...
```

**Класс игрока с поддержкой управления.**

- Загружает спрайт из заданного файла
- Добавляет контроллер игрока
- Регистрируется в группе спрайтов 'player'

### `Obstacle`
```python
class Obstacle(Actor):
    def __init__(self):
        super().__init__()
        self.name = 'obstacle'
        # ... инициализация ...
```

**Класс препятствий в игровом мире.**

- Загружает спрайт препятствия
- Регистрируется в группе спрайтов 'obstacle'
- Участвует в обработке коллизий

### `PlayerController`
```python
class PlayerController(EntityController):
    def __init__(self):
        super().__init__()
```

**Контроллер для управления игроком.**

#### Функциональность:
1. **Управление камерой:**
   - Следует за игроком
   - Центрирует вид на игроке

2. **Обработка ввода:**
   - Клавиши стрелок для движения
   - Плавное перемещение с учетом скорости и времени

3. **Обработка коллизий:**
   - Проверка столкновений с препятствиями
   - Расчет вектора отталкивания
   - Плавное разрешение коллизий

## Система спрайтов

### Группы спрайтов:
- `'player'`: Спрайты игроков
- `'npc'`: Спрайты NPC
- `'obstacle'`: Спрайты препятствий

### Работа со спрайтами:
1. **Загрузка:**
   ```python
   def load_sprite(self, sprite_path):
       self.actor_sprite.image = pygame.image.load(sprite_path)
       self.actor_sprite.image = pygame.transform.scale(self.actor_sprite.image, self.actor_size)
       # ... дополнительная обработка ...
   ```

2. **Загрузка из листа:**
   ```python
   def loadSpriteFromSheet(self, sheet_path, position, size):
       sheet = pygame.image.load(sheet_path)
       self.actor_sprite.image = get_tile(sheet, position[0], position[1], size)
       # ... дополнительная обработка ...
   ```

## Управление движением

### Система координат:
- Позиция хранится в `transform.position`
- Направление движения в `forward`
- Все координаты в пикселях

### Обработка коллизий:
1. **Проверка:**
   ```python
   def check_obstacle_collision(self):
       obstacles = self.parentEntity.parentEntity.sprite_groups['obstacle']
       player_sprite = self.parentEntity.actor_sprite
       collide = pygame.sprite.spritecollideany(player_sprite, obstacles)
       # ... обработка результата ...
   ```

2. **Разрешение:**
   ```python
   def calc_separate_vector(self, obstacle):
       # Расчет вектора отталкивания на основе центров спрайтов
       # ... логика расчета ...
   ```

## Камера и отображение

1. **Следование за игроком:**
   ```python
   camera.position = [
       self.parentEntity.transform.position[0] - 320,
       self.parentEntity.transform.position[1] - 240
   ]
   ```

2. **Обновление позиции спрайта:**
   ```python
   self.actor_sprite.rect.x = transform.position[0] - camera.position[0]
   self.actor_sprite.rect.y = transform.position[1] - camera.position[1]
   ```

## Особенности реализации

1. **Производительность:**
   - Конвертация спрайтов при загрузке
   - Использование цветовых ключей для прозрачности
   - Оптимизированная проверка коллизий

2. **Расширяемость:**
   - Базовые классы для наследования
   - Система компонентов (контроллеры)
   - Гибкая система групп спрайтов

3. **Управляемость:**
   - Плавное движение
   - Корректная обработка коллизий
   - Настраиваемые параметры движения

## Возможные улучшения

1. **Функциональность:**
   - Поддержка анимаций
   - Система состояний
   - Расширенное управление камерой

2. **Физика:**
   - Улучшенное разрешение коллизий
   - Поддержка физических сил
   - Более сложные взаимодействия

3. **Графика:**
   - Поддержка эффектов частиц
   - Улучшенная система анимации
   - Динамическое освещение
