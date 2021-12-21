from __future__ import annotations

from pytest_idempotent import idempotent


@idempotent
def func(x: list[int]) -> None:
    """Correctly Idempotent."""
    if not x:
        x += [9]


def test_func_without_idempotency_check() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
