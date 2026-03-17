from sqlalchemy import MetaData
from sqlalchemy.orm import registry

metadata = MetaData()
mapper_registry = registry(metadata=metadata)


def start_mappers() -> None:
    """
    Registers imperative mappings between Domain Models and SQLAlchemy Tables.
    Currently empty until concrete domain modules (e.g., Orders) are implemented.
    """
    pass
