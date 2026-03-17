import typing

from returns.result import Result, Success, Failure

T = typing.TypeVar("T")
E = typing.TypeVar("E")

# We create type aliases for our business flows
# Any business logic operation that can fail should return a BusinessResult
BusinessResult = Result[T, E]


def success(value: T) -> BusinessResult[T, typing.Any]:
    """Helper to return a success monad."""
    return Success(value)


def failure(error: E) -> BusinessResult[typing.Any, E]:
    """Helper to return a failure monad."""
    return Failure(error)
