from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def my_function(x: list[int]) -> None:
    if not x:
        x += [9]


@pytest.mark.idempotent
def test_case() -> None:
    x: list[int] = []

    my_function(x)

    raise Exception
