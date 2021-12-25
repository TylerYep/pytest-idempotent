from __future__ import annotations

from pytest_idempotent import idempotent


@idempotent(enforce_tests=False)
def idempotent_function(x: list[int]) -> None:
    if not x:
        x += [9]


def test_case() -> None:
    x: list[int] = []

    idempotent_function(x)

    assert x == [9]
