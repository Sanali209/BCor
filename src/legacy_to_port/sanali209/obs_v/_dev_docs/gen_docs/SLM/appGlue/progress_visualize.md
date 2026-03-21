# Progress Visualization (`progress_visualize.py`)

Этот модуль предоставляет простую систему для отслеживания и отображения прогресса выполнения длительных задач в приложении. Он состоит из сервиса `ProgressManager`, который управляет состоянием прогресса, и интерфейса `ProgressVisualizer` для компонентов, отображающих этот прогресс.

## Зависимости

*   `SLM.appGlue.core.Service`: Базовый класс для сервисов `appGlue`.

## Класс `ProgressManager`

*   **Наследование:** `SLM.appGlue.core.Service`
*   **Назначение:** Центральный сервис для управления состоянием прогресса задачи. Он хранит текущее значение, максимальное значение, сообщение и описание задачи, а также уведомляет зарегистрированные визуализаторы об изменениях.
*   **Атрибуты:**
    *   `visualizers` (list): Список зарегистрированных объектов `ProgressVisualizer`.
    *   `progress` (int): Текущее значение прогресса (по умолчанию 0).
    *   `max_progress` (int): Максимальное значение прогресса (по умолчанию 100). *Примечание: нет метода для его изменения.*
    *   `message` (str): Краткое сообщение о текущем шаге (по умолчанию "").
    *   `description` (str): Общее описание выполняемой задачи (по умолчанию "").
*   **Методы:**
    *   **`__init__(self)`:** Инициализирует атрибуты по умолчанию.
    *   **`add_visualizer(self, visualizer)`:** Регистрирует новый визуализатор (объект, наследующий `ProgressVisualizer`).
    *   **`set_description(self, description)`:** Устанавливает описание задачи и вызывает `update()`.
    *   **`step(self, message="")`:** Увеличивает `progress` на 1, устанавливает `message` и вызывает `update()`.
    *   **`reset(self)`:** Сбрасывает `progress`, `message` и `description` в исходное состояние и вызывает `update()`.
    *   **`update(self)`:** Итерирует по всем зарегистрированным `visualizers` и вызывает у каждого метод `update_progress()`.

## Класс `ProgressVisualizer`

*   **Назначение:** Базовый класс (интерфейс) для компонентов пользовательского интерфейса или других систем, которые должны отображать прогресс.
*   **Методы:**
    *   **`update_progress(self)`:**
        *   Этот метод должен быть переопределен в подклассах.
        *   Он вызывается `ProgressManager` при каждом изменении состояния прогресса.
        *   Внутри этого метода визуализатор должен получить актуальные данные (`progress`, `max_progress`, `message`, `description`) из экземпляра `ProgressManager` (обычно полученного через `Allocator` или переданного при инициализации) и обновить свое отображение (например, обновить ProgressBar в GUI).
        *   *Примечание: В коде есть TODO о замене этого метода на callback, что может быть более гибким подходом.*

## Принцип работы и использование

1.  **Регистрация сервиса:** Экземпляр `ProgressManager` должен быть зарегистрирован как сервис в `Allocator` (вероятно, в одном из модулей `appGlue` или основном модуле приложения).
    ```python
    # В методе init() какого-либо модуля
    from SLM.appGlue.core import Allocator
    from SLM.appGlue.progress_visualize import ProgressManager
    
    progress_manager = ProgressManager()
    Allocator.res.register(progress_manager) 
    ```
2.  **Создание и регистрация визуализатора:** Компонент UI (например, виджет с ProgressBar и метками) должен наследоваться от `ProgressVisualizer`, реализовать метод `update_progress` и зарегистрироваться в `ProgressManager`.
    ```python
    from SLM.appGlue.core import Allocator
    from SLM.appGlue.progress_visualize import ProgressVisualizer, ProgressManager
    # Предположим, есть класс виджета MyProgressWidget
    
    class MyProgressWidget(QWidget, ProgressVisualizer): # Пример с Qt
        def __init__(self, parent=None):
            super().__init__(parent)
            # ... инициализация UI элементов (progressBar, labelMessage, labelDescription) ...
            self.progress_manager = Allocator.get_instance(ProgressManager)
            self.progress_manager.add_visualizer(self)
            
        def update_progress(self):
            # Получаем данные из менеджера и обновляем UI
            progress = self.progress_manager.progress
            max_val = self.progress_manager.max_progress
            message = self.progress_manager.message
            description = self.progress_manager.description
            
            self.progressBar.setMaximum(max_val)
            self.progressBar.setValue(progress)
            self.labelMessage.setText(message)
            self.labelDescription.setText(description)
            # Возможно, QApplication.processEvents() если обновление из другого потока
            
        def closeEvent(self, event):
            # Важно: отписаться при уничтожении виджета, чтобы избежать ошибок
            # (хотя в текущей реализации ProgressManager нет метода remove_visualizer)
            # self.progress_manager.remove_visualizer(self) # Гипотетический метод
            super().closeEvent(event) 
    ```
3.  **Управление прогрессом:** Код, выполняющий длительную задачу, получает доступ к `ProgressManager` и вызывает его методы.
    ```python
    from SLM.appGlue.core import Allocator
    from SLM.appGlue.progress_visualize import ProgressManager
    import time
    
    def long_running_task():
        pm = Allocator.get_instance(ProgressManager)
        pm.reset() # Сбросить перед началом
        
        total_steps = 10
        # pm.max_progress = total_steps # Установить максимум (если бы был метод)
        pm.set_description("Processing items...")
        
        for i in range(total_steps):
            # ... выполнение части задачи ...
            time.sleep(0.5) 
            pm.step(f"Processed item {i+1}/{total_steps}")
            
        pm.set_description("Processing complete.")
        # pm.reset() # Можно сбросить в конце
        
    # Запуск задачи (возможно, в отдельном потоке)
    long_running_task()
    ```

Эта система позволяет отделить логику выполнения задачи от ее визуального представления.
