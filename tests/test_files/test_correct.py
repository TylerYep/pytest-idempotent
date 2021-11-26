from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def func(x: list[int]) -> None:
    if not x:
        x += [9]


@pytest.mark.test_idempotency
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
