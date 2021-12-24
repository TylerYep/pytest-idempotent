from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def func(x: list[int]) -> None:
    """Correctly Idempotent."""
    if not x:
        x += [9]


@pytest.mark.idempotent
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]


@pytest.mark.idempotent(run_twice=False)
def test_func_without_idempotency_check() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
