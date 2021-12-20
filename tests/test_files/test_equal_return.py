from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent(equal_return=True)
def func(x: list[int]) -> bool:
    """Correctly Idempotent."""
    if not x:
        x += [9]
    return True


@idempotent(equal_return=True)
def func_2(x: list[int]) -> bool:
    """Not Idempotent."""
    if not x:
        x += [9]
        return True
    return False


@pytest.mark.test_idempotency
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]


@pytest.mark.test_idempotency
def test_func_2() -> None:
    x: list[int] = []

    func_2(x)

    assert x == [9]


def test_funcs_without_idempotency_check() -> None:
    x: list[int] = []

    func(x)
    func_2(x)

    assert x == [9]
