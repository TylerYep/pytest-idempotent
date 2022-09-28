import pytest
from _pytest.pytester import Pytester

from tests.utils import CONFTEST_MAP, Result

# Maps conftest_type -> test cases
TEST_MAPPING = {
    "default": (
        ("test_class", Result(passed=7)),
        ("test_correct_behavior", Result(passed=2)),
        ("test_equal_return_fail", Result(passed=1, failed=1)),
        ("test_equal_return_pass", Result(passed=2)),
        ("test_first_failed_skip_second", Result(skipped=1, failed=1)),
        ("test_first_missing_skip_second", Result(skipped=1, failed=1, warnings=1)),
        ("test_incorrect_but_idempotent", Result(failed=1, skipped=1)),
        ("test_missing_marker_fail", Result(failed=1)),
        ("test_missing_marker_ignore", Result(passed=1)),
        ("test_missing_marker_pass", Result(passed=1)),
        ("test_missing_marker_in_try_except", Result(failed=1)),
        ("test_nested_idempotent_functions", Result(passed=2)),
        ("test_not_idempotent", Result(passed=1, failed=1)),
        ("test_raises_expected_exception", Result(passed=2)),
        ("test_raises_expected_exception_missing", Result(passed=1, failed=1)),
        ("test_raises_unexpected_exception", Result(passed=1, failed=1)),
        ("test_warn_unnecessary_marker", Result(passed=5, skipped=4, warnings=4)),
    ),
    "custom_decorator": (("test_custom_decorator", Result(passed=1, failed=1)),),
    "random_ordering": (
        ("test_class", Result(passed=7, warnings=2)),
        ("test_warn_unnecessary_marker", Result(passed=8, skipped=1, warnings=7)),
    ),
    "enforce": (
        ("test_missing_marker_fail", Result(passed=1, warnings=1)),
        ("test_missing_marker_ignore", Result(passed=1)),
        ("test_missing_marker_pass", Result(passed=1)),
        ("test_missing_marker_method_override", Result(failed=1)),
        ("test_missing_marker_in_try_except", Result(passed=1, warnings=1)),
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
    pytester.copy_example(f"tests/test_files/{filename}.py")

    result = pytester.runpytest("-W", "ignore::pytest.PytestAssertRewriteWarning")

    result.assert_outcomes(**expected._asdict())
