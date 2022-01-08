from __future__ import annotations

import pytest


def undecorated_function(x: list[int]) -> None:
    if not x:
        x += [9]


@pytest.mark.idempotent
def test_case() -> None:
    x: list[int] = []

    undecorated_function(x)

    assert x == [9]


@pytest.mark.idempotent
class TestClass:
    @staticmethod
    def test_warning_inside_class() -> None:
        x: list[int] = []

        undecorated_function(x)

        assert x == [9]

    @staticmethod
    @pytest.mark.idempotent(enabled=False)
    def test_no_warnings() -> None:
        x: list[int] = []

        undecorated_function(x)

        assert x == [9]
