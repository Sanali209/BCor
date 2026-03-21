"""Прокси-модуль для обратной совместимости. Перенесен в src.common.monads."""

from src.common.monads import BusinessResult, failure, success

__all__ = ["BusinessResult", "success", "failure"]
