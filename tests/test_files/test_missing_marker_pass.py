from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def idempotent_function(x: list[int]) -> None:
    if not x:
        x += [9]


@pytest.mark.idempotent(enabled=False)
def test_case() -> None:
    x: list[int] = []

    idempotent_function(x)

    assert x == [9]
