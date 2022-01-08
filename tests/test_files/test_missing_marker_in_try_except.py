from __future__ import annotations

from pytest_idempotent import idempotent


@idempotent
def my_function(x: list[int]) -> None:
    if not x:
        x += [9]


def test_without_marker() -> None:
    x: list[int] = []

    try:
        my_function(x)
    except Exception:  # pylint: disable=broad-except
        return

    assert x == [9]
