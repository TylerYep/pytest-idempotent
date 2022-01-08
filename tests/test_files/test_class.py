from __future__ import annotations

import pytest

from pytest_idempotent import idempotent


@idempotent()
def func(x: list[int]) -> None:
    if not x:
        x += [9]


@pytest.mark.idempotent
class TestVariousFunctions:
    @staticmethod
    def test_func() -> None:
        x: list[int] = []

        func(x)

        assert x == [9]

    @staticmethod
    @pytest.mark.idempotent(enabled=False)
    def test_func_without_idempotency_check() -> None:
        x: list[int] = []

        func(x)

        assert x == [9]

    @staticmethod
    @pytest.mark.idempotent
    def test_func_with_double_idempotency_check() -> None:
        x: list[int] = []

        func(x)

        assert x == [9]

    @staticmethod
    @pytest.mark.idempotent(enabled=True)
    def test_func_with_double_idempotency_enabled() -> None:
        x: list[int] = []

        func(x)

        assert x == [9]
