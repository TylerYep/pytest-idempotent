from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def func(x: list[int]) -> None:
    """Not idempotent."""
    x += [9]


@pytest.mark.test_idempotency
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]


def test_func_without_idempotency_check() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
