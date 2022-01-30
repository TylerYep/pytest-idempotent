import pytest
from _pytest.pytester import Pytester

from tests.utils import CONFTEST_MAP, Result

# Maps conftest_type -> test cases
TEST_MAPPING = {
    "default": (
        ("test_class.py", Result(passed=7)),
        ("test_correct_behavior.py", Result(passed=2)),
        ("test_equal_return_fail.py", Result(passed=1, failed=1)),
        ("test_equal_return_pass.py", Result(passed=2)),
        ("test_first_failed_skip_second.py", Result(skipped=1, failed=1)),
        ("test_first_missing_skip_second.py", Result(skipped=1, failed=1, warnings=1)),
        ("test_incorrect_but_idempotent.py", Result(failed=1, skipped=1)),
        ("test_missing_marker_fail.py", Result(failed=1)),
        ("test_missing_marker_ignore.py", Result(passed=1)),
        ("test_missing_marker_pass.py", Result(passed=1)),
        ("test_missing_marker_in_try_except.py", Result(failed=1)),
        ("test_not_idempotent.py", Result(passed=1, failed=1)),
        ("test_raises_expected_exception.py", Result(passed=2)),
        ("test_raises_expected_exception_missing.py", Result(passed=1, failed=1)),
        ("test_raises_unexpected_exception.py", Result(passed=1, failed=1)),
        ("test_warn_unnecessary_marker.py", Result(passed=5, skipped=4, warnings=4)),
    ),
    "custom_decorator": (("test_custom_decorator.py", Result(passed=1, failed=1)),),
    "random_ordering": (
        ("test_class.py", Result(passed=7, warnings=2)),
        ("test_warn_unnecessary_marker.py", Result(passed=8, skipped=1, warnings=7)),
    ),
    "enforce": (
        ("test_missing_marker_fail.py", Result(passed=1, warnings=1)),
        ("test_missing_marker_ignore.py", Result(passed=1)),
        ("test_missing_marker_pass.py", Result(passed=1)),
        ("test_missing_marker_method_override.py", Result(failed=1)),
        ("test_missing_marker_in_try_except.py", Result(passed=1, warnings=1)),
    ),
}
TEST_SUITE = [
    (conftest, *tup) for conftest, tuples in TEST_MAPPING.items() for tup in tuples
]


@pytest.mark.parametrize("conftest,filename,expected", TEST_SUITE)
def test_plugin(
    pytester: Pytester, conftest: str, filename: str, expected: Result
) -> None:
    pytester.makeconftest(CONFTEST_MAP[conftest])
    pytester.copy_example(f"tests/test_files/{filename}")

    result = pytester.runpytest("-W", "ignore::pytest.PytestAssertRewriteWarning")

    # In Pytest 7, warnings is included in assert_outcomes()
    expected_result = expected._asdict()
    assert result.parseoutcomes().get("warnings", 0) == expected_result.pop("warnings")
    result.assert_outcomes(**expected_result)
