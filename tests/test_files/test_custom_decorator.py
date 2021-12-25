from __future__ import annotations

import pytest

from tests.test_files.src.decorator import idempotent


@idempotent
def use_decorator_from_config(x: list[int]) -> None:
    x += [9]


@pytest.mark.idempotent
def test_case() -> None:
    x: list[int] = []

    use_decorator_from_config(x)

    assert x == [9]
