"""Функциональные типы и монады для обработки результатов выполнения операций."""

import typing

from returns.result import Failure, Result, Success

T = typing.TypeVar("T")
E = typing.TypeVar("E")

# Определение типа для результатов бизнес-операций
BusinessResult = Result[T, E]
"""Алиас для монады Result, используемой в бизнес-логике."""


def success(value: T) -> BusinessResult[T, typing.Any]:
    """Возвращает успешный результат."""
    return Success(value)


def failure(error: E) -> BusinessResult[typing.Any, E]:
    """Возвращает ошибку."""
    return Failure(error)
