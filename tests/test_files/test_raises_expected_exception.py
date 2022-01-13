from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


class ExpectedException(Exception):
    message = "This is a known error for idempotency."


@idempotent(raises_exception=ExpectedException)
def my_function(x: list[int]) -> None:
    if x:
        raise ExpectedException
    x += [9]


@pytest.mark.idempotent
def test_case() -> None:
    x: list[int] = []

    my_function(x)

    assert x == [9]
