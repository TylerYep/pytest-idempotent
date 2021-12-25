from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent
def not_idempotent_function(x: list[int]) -> None:
    x += [9]


@pytest.mark.idempotent
def test_case() -> None:
    x: list[int] = []

    not_idempotent_function(x)

    assert x == [9]
