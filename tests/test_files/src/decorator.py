from __future__ import annotations

from typing import Any, Callable, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])


def idempotent(func: _F) -> _F:
    return func
