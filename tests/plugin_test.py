from typing import NamedTuple

import pytest
from _pytest.pytester import Pytester


class Result(NamedTuple):
    passed: int
    failed: int


@pytest.mark.parametrize(
    "filename,expected",
    (
        ("test_class.py", Result(passed=7, failed=0)),
        ("test_correct.py", Result(passed=3, failed=0)),
        ("test_equal_return.py", Result(passed=3, failed=1)),
        ("test_error.py", Result(passed=1, failed=1)),
        ("test_missing_check.py", Result(passed=0, failed=1)),
    ),
)
def test_plugin(pytester: Pytester, filename: str, expected: Result) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_idempotent']")
    pytester.copy_example(f"tests/test_files/{filename}")

    result = pytester.runpytest()

    result.assert_outcomes(**expected._asdict())


def test_plugin_configuration(pytester: Pytester) -> None:
    pytester.makeconftest(
        """
        pytest_plugins = ['pytest_idempotent']

        def pytest_idempotent_decorator():
            return 'tests.test_files.src.decorator.idempotent'
        """
    )
    pytester.copy_example("tests/test_files/test_config.py")

    result = pytester.runpytest()

    result.assert_outcomes(passed=1, failed=1)
