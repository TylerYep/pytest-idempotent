from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def outer_not_idempotent_function(x: list[int]) -> None:
    x.append(1)
    inner_idempotent_function(x)


@idempotent
def inner_idempotent_function(x: list[int]) -> None:
    x.append(2)


@pytest.mark.idempotent
def test_case() -> None:
    """
    This test llustrates what happens if we use nested @idempotent decorators.

    Only two test cases are run, but the second test has a compounding effect.
    """
    x: list[int] = []

    outer_not_idempotent_function(x)

    assert x in ([1, 2], [1, 2, 2, 1, 2, 2])
