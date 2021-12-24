from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def func(x: list[int]) -> None:
    """Not idempotent."""
    x += [9]


@pytest.mark.idempotent
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
