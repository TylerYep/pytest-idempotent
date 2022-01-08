from __future__ import annotations

from pytest_idempotent import idempotent


@idempotent
def my_function(x: list[int]) -> None:
    if not x:
        x += [9]


def test_without_marker() -> None:
    x: list[int] = []

    my_function(x)

    assert x == [9]
