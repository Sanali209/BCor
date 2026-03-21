# Image to Tensor Module

Эта поддиректория модуля `vision` отвечает за преобразование изображений в векторные представления (эмбеддинги или тензоры) с использованием различных моделей глубокого обучения, преимущественно сверточных нейронных сетей (CNN) и трансформеров (например, CLIP).

## Структура модуля

*   `__init__.py`: Инициализационный файл пакета. Может импортировать и регистрировать бэкенды.
*   [CNN Encoding (`CNN_Encoding.py`)](CNN_Encoding.md): Определяет базовый класс `CNN_Encoder` и фасад `ImageToCNNTensor` для управления бэкендами эмбеддингов.
*   `CNN_Finder.py`: Возможно, связан с поиском или управлением моделями CNN. *(Placeholder)*
*   `backends/`: Поддиректория, содержащая реализации конкретных моделей-энкодеров (например, CLIP, ResNet, MobileNet). *(Placeholder)*
*   `custom/`: Возможно, для пользовательских или модифицированных моделей. *(Placeholder)*
*   `custom_mobile_net/`: Вероятно, содержит реализацию или адаптацию MobileNet. *(Placeholder)*

## Основные возможности

*   Предоставление единого интерфейса (`ImageToCNNTensor`) для получения эмбеддингов изображений.
*   Поддержка различных моделей (бэкендов) для генерации эмбеддингов.
*   Ленивая загрузка моделей по мере необходимости.
*   Интеграция с пулом загрузки изображений (`PILPool`).

## Дальнейшая документация

*   [CNN Encoding (`CNN_Encoding.py`)](CNN_Encoding.md)
*   [CNN Finder (`CNN_Finder.py`)](CNN_Finder.md)
*   [Backends](backends/index.md) *(Placeholder)*
*   [Custom Models](custom/index.md) *(Placeholder)*
*   [Custom MobileNet](custom_mobile_net/index.md) *(Placeholder)*

## Связанные концепции

*   [Vision Module](../index.md)
*   [Core Concepts](../../core_concepts.md) (Embeddings)
*   [Vector DB Module](../../vector_db/index.md) (Использует сгенерированные здесь эмбеддинги)
*   [Files DB Module](../../files_db/index.md) (Может вызывать `ImageToCNNTensor` для векторизации)
