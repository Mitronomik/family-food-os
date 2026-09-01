"""Driver-independent transaction contracts for application services."""

from types import TracebackType
from typing import Protocol, Self


class UnitOfWork(Protocol):
    """Application-owned write scope with explicit transaction completion."""

    def __enter__(self) -> Self: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class ReadOnlyScope(Protocol):
    """Consistent application query scope that cannot be committed."""

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
