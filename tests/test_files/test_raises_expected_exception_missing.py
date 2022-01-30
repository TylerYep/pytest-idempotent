from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent(raises_exception=RuntimeError)
def incorrect_function(x: list[int]) -> None:
    x += [9]


@pytest.mark.idempotent
def test_case_fails() -> None:
    x: list[int] = []

    incorrect_function(x)

    assert x == [9]
