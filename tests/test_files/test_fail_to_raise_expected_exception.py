from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent(raises_exception=RuntimeError)
def incorrect_function(x: list[int]) -> None:
    x += [9]


@idempotent(raises_exception=RuntimeError)
def correct_function(x: list[int]) -> None:
    if x:
        raise RuntimeError("This is an expected idempotency error.")
    x += [9]


@pytest.mark.idempotent
def test_case_fails() -> None:
    x: list[int] = []

    incorrect_function(x)

    assert x == [9]


@pytest.mark.idempotent
def test_case_passes() -> None:
    x: list[int] = []

    correct_function(x)

    assert x == [9]
