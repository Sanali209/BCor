# Relation Record (`relation.py`)

Этот модуль определяет класс `RelationRecord`, который служит моделью данных для представления **направленных связей (отношений)** между двумя записями в базе данных SLM. Этими записями могут быть любые наследники `CollectionRecord`, такие как `FileRecord` или `Detection`. Записи `RelationRecord` хранятся в отдельной коллекции MongoDB (вероятно, называемой `relations`).

## Зависимости

*   `SLM.appGlue.core.Allocator` (не используется напрямую, но подразумевается для `MongoClientExt`)
*   `SLM.files_db.components.File_record_wraper.FileRecord` (используется в аннотациях типов)
*   `SLM.files_db.components.collectionItem.CollectionRecord`
*   `SLM.mongoext.MongoClientEXT_f.MongoClientExt` (не используется напрямую)
*   `SLM.mongoext.wraper.MongoRecordWrapper`, `SLM.mongoext.wraper.FieldPropInfo`

## Класс `RelationRecord`

Наследуется от `MongoRecordWrapper`.

### Назначение

*   Моделировать направленные бинарные отношения между любыми двумя записями в базе данных.
*   Хранить тип и подтип связи, а также ссылки на связанные объекты.
*   Предоставлять методы для создания, поиска и удаления связей.

### Атрибуты и Поля (`FieldPropInfo`)

*   **`type: str`**: Строка, определяющая основной тип связи. Примеры:
    *   `"similar_search"`: Связь, указывающая на визуальную схожесть между двумя файлами (`FileRecord`).
    *   `"similar_obj_search"`: Связь, указывающая на визуальную схожесть между двумя обнаруженными объектами (`Detection`).
    *   *(Возможны и другие типы: `"parent_child"`, `"contains"`, `"references"` и т.д.)*
*   **`sub_type: str`**: Строка, уточняющая основной тип связи. Примеры:
    *   Для `type="similar_search"` или `type="similar_obj_search"`: `"face"`, `"person"`, `"none"` (указывает, на основе чего установлена схожесть, или общая схожесть).
*   **`from_id: str`** (или `ObjectId`): Идентификатор (`_id`) исходного объекта ("хвост" стрелки) в направленной связи.
*   **`to_id: str`** (или `ObjectId`): Идентификатор (`_id`) целевого объекта ("наконечник" стрелки) в направленной связи.
*   **Другие поля:** При создании связи через `get_or_create` можно добавить дополнительные поля с помощью `**kwargs`. Например, модуль `dubsearch.py` добавляет поля `distance` (мера схожести) и `emb_type` (тип использованного эмбеддинга).

### Методы Класса

*   **`get_or_create(cls, from_: CollectionRecord, to_: CollectionRecord, type: str = "None", **kwargs)`**:
    *   **Основной метод для создания/получения связи.**
    *   Принимает исходный (`from_`) и целевой (`to_`) объекты.
    *   Извлекает их `_id` и ищет существующую запись `RelationRecord` с этими `from_id`, `to_id` и `type`.
    *   Если запись найдена, возвращает ее.
    *   Если не найдена, создает новую запись `RelationRecord`, используя `from_._id`, `to_._id`, `type` и данные из `**kwargs`.
*   **`set_relation(cls, from_: CollectionRecord, to_: CollectionRecord, type_: str = "None")`**:
    *   Псевдоним (alias) для `get_or_create`.
*   **`get_outgoing_relations(cls, from_CollectionRecord, type_: str = "None")`**:
    *   Находит и возвращает список всех записей `RelationRecord`, которые начинаются с объекта `from_CollectionRecord` (`from_id == from_CollectionRecord._id`) и имеют указанный `type`.
*   **`is_exist(cls, from_: CollectionRecord, to_: CollectionRecord, type_: str = "None")`**:
    *   Проверяет, существует ли **конкретная направленная связь** с заданным `type` от объекта `from_` к объекту `to_`.
    *   Возвращает `True`, если такая запись найдена, иначе `False`.
*   **`delete_all_relations(cls, obj: CollectionRecord)`**:
    *   Удаляет **все** записи `RelationRecord`, где `obj._id` указан в поле `from_id` **или** в поле `to_id`.
    *   Этот метод важен для поддержания целостности данных при удалении самого объекта `obj`.

## Использование

`RelationRecord` является универсальным инструментом для построения графов связей в SLM. Он используется для:
*   Хранения результатов поиска схожести (см. `dubsearch.py`).
*   Потенциально для моделирования иерархий, зависимостей или любых других типов отношений между элементами данных.
