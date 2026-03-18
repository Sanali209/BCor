import typing

from returns.result import Result, Success, Failure

T = typing.TypeVar("T")
E = typing.TypeVar("E")

# We create type aliases for our business flows
# Any business logic operation that can fail should return a BusinessResult
BusinessResult = Result[T, E]
"""Type alias for a Result monad used in business logic."""


def success(value: T) -> BusinessResult[T, typing.Any]:
    """Helper to return a success monad.

    Args:
        value: The successful result value.

    Returns:
        A Success monad wrapping the value.
    """
    return Success(value)


def failure(error: E) -> BusinessResult[typing.Any, E]:
    """Helper to return a failure monad.

    Args:
        error: The error or failure information.

    Returns:
        A Failure monad wrapping the error.
    """
    return Failure(error)
