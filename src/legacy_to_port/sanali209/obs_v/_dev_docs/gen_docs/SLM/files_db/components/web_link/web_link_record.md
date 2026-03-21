# Web Link Record and URI Decoder (`web_link_record.py`)

Этот модуль определяет класс `WebLinkRecord` для представления веб-ссылок (URI) в базе данных SLM, а также классы `uriDecoder` и `uriDecoderManager` для извлечения информации с веб-страниц.

## Зависимости

*   `os`, `uuid`
*   `html2image`: Для создания скриншотов веб-страниц.
*   `requests`: Для загрузки содержимого веб-страниц.
*   `bs4` (`BeautifulSoup`): Для парсинга HTML и извлечения текста.
*   `langchain.chains.llm.LLMChain`, `langchain_core.prompts.PromptTemplate`: Для взаимодействия с языковой моделью.
*   `SLM.LangChain.LangChainHelper.LLM_hugingface_model_inference`: Хелпер для запуска Hugging Face моделей через LangChain.
*   `SLM.appGlue.DesignPaterns.allocator`
*   `SLM.files_db.components.collectionItem.CollectionRecord`
*   `SLM.mongoext.MongoClientEXT_f.MongoClientExt`
*   `SLM.mongoext.wraper.MongoRecordWrapper`, `SLM.mongoext.wraper.FieldPropInfo`

## Класс `uriDecoderManager`

*   **Назначение:** Управляет настройками и регистрацией "декодеров" URI.
*   **Атрибуты/Методы:**
    *   `decoders` (dict): Статический словарь для хранения зарегистрированных экземпляров декодеров (ключ - имя класса декодера).
    *   `get_scrinshoth_path()` (staticmethod): Возвращает путь для сохранения скриншотов (`./screen_shot/`). *Todo: Переместить путь в глобальный кэш.*
    *   `get_scrinshoth_size()` (staticmethod): Возвращает размер скриншота (512, 512).
    *   `register_decoder(cls, decoder)` (classmethod): Регистрирует декодер в словаре `decoders`.

## Класс `uriDecoder`

*   **Назначение:** Предоставляет методы для извлечения данных с веб-страницы по URL.
*   **Методы:**
    *   `create_thumbnail(self, url)`:
        *   Создает скриншот страницы с помощью `html2image` (требует Edge).
        *   Сохраняет как JPG с UUID-именем в папку, указанную `uriDecoderManager`.
        *   *Todo: Устранить зависимость от Edge.*
        *   *Примечание: Возвращает `None`.*
    *   `get_page_text(self, url)`:
        *   Загружает страницу (`requests.get`).
        *   Извлекает весь текст с помощью `BeautifulSoup`.
        *   Возвращает строку с текстом.
    *   `get_summary(self, page_text)`:
        *   Генерирует краткое резюме текста страницы с помощью LLM (`mistralai/Mistral-7B-Instruct-v0.2` через LangChain).
        *   Ограничивает входной текст ~32k символов.
        *   Использует `PromptTemplate` для формирования запроса к модели.
        *   Извлекает результат из ответа модели.
        *   Возвращает строку с резюме.

## Класс `WebLinkRecord`

*   **Наследование:** `CollectionRecord` -> `MongoRecordWrapper`.
*   **Назначение:** Модель данных для представления веб-ссылки в MongoDB.
*   **Поля (`FieldPropInfo`):**
    *   `itemType: str`: Установлено в `"WebLinkRecord"`. Используется для полиморфизма в `CollectionRecord`.
    *   `uri: str`: Хранит URL веб-ссылки. *Примечание: В коде `FieldPropInfo` указано имя `'name'`, но используется как `uri`.*
*   **Методы:**
    *   `new_record(cls, uri, **kwargs)` (classmethod): Метод для создания новой записи. Должен принимать `uri` и передавать его в `super()`.

## Инициализация (`init` function)

*   Регистрируется в `allocator.Allocator`.
*   Выполняется при запуске приложения:
    *   Регистрирует `WebLinkRecord` в `CollectionRecord.itemTypeMap['WebLinkRecord'] = WebLinkRecord`.
    *   Регистрирует коллекцию `"WebLinkRecord"` (или общую коллекцию для `CollectionRecord`) в `MongoClientExt` для работы с классом `WebLinkRecord`.

## Использование

Этот модуль позволяет приложению:
1.  Сохранять веб-ссылки как записи `WebLinkRecord` в базе данных.
2.  Использовать `uriDecoder` для извлечения дополнительной информации о ссылке (текст, скриншот, резюме) по требованию или при создании записи. Эта информация может быть сохранена в полях `WebLinkRecord` или связанных записях.
