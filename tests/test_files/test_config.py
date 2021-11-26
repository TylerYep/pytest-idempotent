from __future__ import annotations

import pytest

from tests.test_files.src.decorator import idempotent


@idempotent
def func(x: list[int]) -> None:
    x += [9]


@pytest.mark.test_idempotency
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
