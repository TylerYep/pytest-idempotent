from typing import TypedDict

import pytest
from _pytest.pytester import Pytester


class Result(TypedDict):
    passed: int
    failed: int


@pytest.mark.parametrize(
    "filename,expected",
    (
        ("test_error.py", Result(passed=1, failed=1)),
        ("test_correct.py", Result(passed=2, failed=0)),
    ),
)
def test_plugin(pytester: Pytester, filename: str, expected: Result) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_idempotent']")
    pytester.copy_example(f"./tests/test_files/{filename}")

    result = pytester.runpytest()

    result.assert_outcomes(**expected)
