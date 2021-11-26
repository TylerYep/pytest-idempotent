from functools import wraps
from typing import Any, Callable, Iterator, TypeVar, cast
from unittest.mock import patch

import pytest
from _pytest.config import Config, PytestPluginManager
from _pytest.fixtures import SubRequest
from _pytest.python import Metafunc

_F = TypeVar("_F", bound=Callable[..., Any])
CHECK_IDEMPOTENCY = False  # global variable needed for idempotency check


def idempotent(func: _F) -> _F:
    """
    No-op during runtime.
    This marker allows Pytest to override the decorated function
    during test-time to verify the function is idempotent.
    """
    return func


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """
    If @pytest.mark.test_idempotency is added to a function or class, run all
    selected tests twice, one as normal and one with the idempotency check.
    """
    if metafunc.definition.get_closest_marker("test_idempotency"):
        metafunc.parametrize(
            "add_idempotency_check",
            (False, True),
            indirect=True,
            ids=("no-idempotency-check", "idempotency-check"),
        )


@pytest.fixture(autouse=True)
def add_idempotency_check(request: SubRequest) -> Iterator[Any]:
    """
    This fixture is added to all tests, but only patches CHECK_IDEMPOTENCY
    if this fixture is parametrized by the pytest_generate_tests metafunc.
    """
    if hasattr(request, "param"):
        with patch("pytest_idempotent.CHECK_IDEMPOTENCY", request.param):
            yield
    else:
        yield


def pytest_configure(config: Config) -> None:
    """Patch the @idempotent decorator for all tests."""
    config.addinivalue_line(
        "markers",
        "test_idempotency: mark test function or test class to run idempotency tests",
    )

    def _idempotent(func: _F) -> _F:
        """
        Runs the provided function twice, which allows the test to verify
        whether the provided function is idempotent.

        Returns the first run's result, which allows backwards-compatibility
        e.g. a function that returns True if updated and False otherwise
            is acceptably idempotent.
        """

        @wraps(func)
        def new_func(*args: Any, **kwargs: Any) -> Any:
            run_1 = func(*args, **kwargs)
            if CHECK_IDEMPOTENCY:
                _ = func(*args, **kwargs)
            return run_1

        return cast(_F, new_func)

    # We need to patch the decorator in this function because the decorator
    # is applied when the module is imported, and once that happens it is too
    # late to patch its functionality.
    patch(
        (
            config.pluginmanager.hook.pytest_idempotent_decorator()
            or "pytest_idempotent.idempotent"
        ),
        _idempotent,
    ).start()


class PytestIdempotentSpec:
    """Hook specification namespace for this plugin."""

    @pytest.hookspec(firstresult=True)  # type: ignore[misc]
    def pytest_idempotent_decorator(self) -> str:
        """
        Plugin users define this function in conftest.py to configure
        the default path for the @idempotent decorator.
        """


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    pluginmanager.add_hookspecs(PytestIdempotentSpec)
