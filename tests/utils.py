from typing import NamedTuple


class Result(NamedTuple):
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    warnings: int = 0


DEFAULT_CONFTEST = "pytest_plugins = ['pytest_idempotent']"
CUSTOM_DECORATOR_CONFTEST = """
    pytest_plugins = ['pytest_idempotent']

    def pytest_idempotent_decorator():
        return 'tests.test_files.src.decorator.idempotent'
    """
RANDOM_ORDERING_CONFTEST = """
    import random

    pytest_plugins = ['pytest_idempotent']

    def pytest_collection_modifyitems(session, config, items):
        random.seed(0)
        random.shuffle(items)
    """
ENFORCE_TESTS_CONFTEST = """
    pytest_plugins = ['pytest_idempotent']

    def pytest_idempotent_enforce_tests():
        return False
    """

CONFTEST_MAP = {
    "default": DEFAULT_CONFTEST,
    "custom_decorator": CUSTOM_DECORATOR_CONFTEST,
    "random_ordering": RANDOM_ORDERING_CONFTEST,
    "enforce": ENFORCE_TESTS_CONFTEST,
}
