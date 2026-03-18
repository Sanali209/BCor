from sqlalchemy import MetaData
from sqlalchemy.orm import registry

metadata = MetaData()
mapper_registry = registry(metadata=metadata)


def start_mappers() -> None:
    """Registers imperative mappings between Domain Models and SQL Tables.

    This function should be called during application startup to link
    plain Python domain classes with SQLAlchemy table definitions without
    using the declarative base (Imperative Mapping).
    """
    pass
