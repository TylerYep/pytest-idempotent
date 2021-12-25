from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent(equal_return=True)
def mismatched_return_values(x: list[int]) -> bool:
    if not x:
        x += [9]
        return True
    return False


@pytest.mark.idempotent
def test_case() -> None:
    x: list[int] = []

    mismatched_return_values(x)

    assert x == [9]
