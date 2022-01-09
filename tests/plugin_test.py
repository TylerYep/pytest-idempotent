from typing import NamedTuple

import pytest
from _pytest.pytester import Pytester


class Result(NamedTuple):
    passed: int
    failed: int
    warnings: int = 0


@pytest.mark.parametrize(
    "filename,expected",
    (
        ("test_class.py", Result(passed=7, failed=0)),
        ("test_correct_behavior.py", Result(passed=2, failed=0)),
        ("test_equal_return_fail.py", Result(passed=1, failed=1)),
        ("test_equal_return_pass.py", Result(passed=2, failed=0)),
        ("test_incorrect_but_idempotent.py", Result(passed=0, failed=2)),
        ("test_missing_marker_fail.py", Result(passed=0, failed=1)),
        ("test_missing_marker_ignore.py", Result(passed=1, failed=0)),
        ("test_missing_marker_pass.py", Result(passed=1, failed=0)),
        ("test_missing_marker_in_try_except.py", Result(passed=0, failed=1)),
        ("test_not_idempotent.py", Result(passed=1, failed=1)),
        ("test_warn_unnecessary_marker.py", Result(passed=9, failed=0, warnings=4)),
    ),
)
def test_plugin(pytester: Pytester, filename: str, expected: Result) -> None:
    pytester.makeconftest("pytest_plugins = ['pytest_idempotent']")
    pytester.copy_example(f"tests/test_files/{filename}")

    result = pytester.runpytest("-W", "ignore::pytest.PytestAssertRewriteWarning")

    # In Pytest 7, warnings is included in assert_outcomes()
    expected_result = expected._asdict()
    assert result.parseoutcomes().get("warnings", 0) == expected_result.pop("warnings")
    result.assert_outcomes(**expected_result)


def test_custom_decorator_config(pytester: Pytester) -> None:
    pytester.makeconftest(
        """
        pytest_plugins = ['pytest_idempotent']

        def pytest_idempotent_decorator():
            return 'tests.test_files.src.decorator.idempotent'
        """
    )
    pytester.copy_example("tests/test_files/test_custom_decorator.py")

    result = pytester.runpytest()

    result.assert_outcomes(passed=1, failed=1)
