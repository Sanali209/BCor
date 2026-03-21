# Simple Message System (`MessageSystem.py`)

Этот модуль предоставляет очень простую реализацию паттерна Издатель-Подписчик (Publish-Subscribe) или Шины событий (Event Bus) с использованием статических методов и словаря. Он позволяет различным частям приложения обмениваться сообщениями без необходимости прямого знания друг о друге.

## Класс `MessageSystem`

*   **Назначение:** Реализует централизованную систему для подписки на сообщения и их отправки. Все методы и данные являются статическими, что делает систему глобально доступной в рамках приложения.
*   **Статический атрибут:**
    *   `subscribers` (dict): Словарь, где ключами являются идентификаторы сообщений (любой хешируемый тип, обычно строки), а значениями - списки кортежей. Каждый кортеж содержит `(subscriber, callback)`, где `subscriber` - это объект-подписчик (используется для отписки), а `callback` - функция или метод, который будет вызван при отправке сообщения.
*   **Статические методы:**
    *   **`Subscribe(message, subscriber, callback)`:**
        *   Подписывает `subscriber` на получение сообщений типа `message`.
        *   При получении сообщения `message` будет вызвана функция `callback`.
        *   Добавляет кортеж `(subscriber, callback)` в список, соответствующий ключу `message` в словаре `subscribers`. Если ключ `message` не существует, он создается с пустым списком.
    *   **`Unsubscribe(message, subscriber)`:**
        *   Отписывает `subscriber` от сообщений типа `message`.
        *   Удаляет все кортежи `(sub, cb)` из списка для `message`, где `sub` совпадает с переданным `subscriber`.
    *   **`SendMessage(message, *args, **kwargs)`:**
        *   Отправляет (публикует) сообщение типа `message`.
        *   Находит всех подписчиков на это сообщение в словаре `subscribers`.
        *   Вызывает соответствующую `callback` функцию для каждого подписчика, передавая ей `*args` и `**kwargs`.

## Пример использования

```python
from SLM.appGlue.DesignPaterns.MessageSystem import MessageSystem

# Определяем идентификаторы сообщений
MSG_USER_LOGIN = "user_login"
MSG_DATA_UPDATED = "data_updated"

# Компонент 1: Отправляет сообщения
class UserManager:
    def login(self, username):
        print(f"[UserManager] User '{username}' is logging in...")
        # Какие-то действия по входу...
        print(f"[UserManager] Sending message: {MSG_USER_LOGIN}")
        MessageSystem.SendMessage(MSG_USER_LOGIN, username=username, timestamp="12:34:56")

    def update_data(self):
        print("[UserManager] Updating data...")
        # Какие-то действия по обновлению...
        print(f"[UserManager] Sending message: {MSG_DATA_UPDATED}")
        MessageSystem.SendMessage(MSG_DATA_UPDATED, source="UserManager")

# Компонент 2: Подписывается на вход пользователя
class AuditLogger:
    def __init__(self):
        # Подписываемся на сообщение MSG_USER_LOGIN
        # Передаем self как подписчика и self.log_user_login как callback
        MessageSystem.Subscribe(MSG_USER_LOGIN, self, self.log_user_login)
        print("[AuditLogger] Subscribed to user_login messages.")

    def log_user_login(self, username, timestamp):
        print(f"[AuditLogger] Received user_login: User '{username}' logged in at {timestamp}.")

    def stop_logging(self):
        # Отписываемся от сообщений
        MessageSystem.Unsubscribe(MSG_USER_LOGIN, self)
        print("[AuditLogger] Unsubscribed from user_login messages.")

# Компонент 3: Подписывается на обновление данных
class UIRefresher:
    def __init__(self):
        MessageSystem.Subscribe(MSG_DATA_UPDATED, self, self.refresh_ui)
        print("[UIRefresher] Subscribed to data_updated messages.")

    def refresh_ui(self, source):
        print(f"[UIRefresher] Received data_updated from '{source}'. Refreshing UI...")

    def close_ui(self):
        MessageSystem.Unsubscribe(MSG_DATA_UPDATED, self)
        print("[UIRefresher] Unsubscribed from data_updated messages.")

# --- Демонстрация работы ---
user_manager = UserManager()
logger = AuditLogger()
refresher = UIRefresher()

print("\n--- User logs in ---")
user_manager.login("Alice") 
# Output:
# [UserManager] User 'Alice' is logging in...
# [UserManager] Sending message: user_login
# [AuditLogger] Received user_login: User 'Alice' logged in at 12:34:56.

print("\n--- Data is updated ---")
user_manager.update_data()
# Output:
# [UserManager] Updating data...
# [UserManager] Sending message: data_updated
# [UIRefresher] Received data_updated from 'UserManager'. Refreshing UI...

print("\n--- Logger stops logging ---")
logger.stop_logging()

print("\n--- User logs in again ---")
user_manager.login("Bob") 
# Output: (AuditLogger больше не получает сообщение)
# [UserManager] User 'Bob' is logging in...
# [UserManager] Sending message: user_login

print("\n--- UI is closed ---")
refresher.close_ui()

print("\n--- Data is updated again ---")
user_manager.update_data()
# Output: (UIRefresher больше не получает сообщение)
# [UserManager] Updating data...
# [UserManager] Sending message: data_updated

```

**Преимущества:**

*   **Слабая связанность:** Компоненты не зависят друг от друга напрямую, только от `MessageSystem` и идентификаторов сообщений.
*   **Простота:** Легко понять и использовать.

**Недостатки:**

*   **Глобальное состояние:** Использование статического словаря делает систему глобальной, что может затруднить тестирование и управление зависимостями в больших приложениях.
*   **Отсутствие типизации сообщений:** Идентификаторы сообщений - это просто строки (или другие хешируемые объекты), нет встроенной проверки типов передаваемых данных (`*args`, `**kwargs`).
*   **Управление жизненным циклом:** Подписчики должны явно отписываться (`Unsubscribe`), чтобы избежать утечек памяти или вызова методов у уже не существующих объектов, если `callback` является методом экземпляра.
