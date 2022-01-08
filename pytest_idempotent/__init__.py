from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Iterator, TypeVar, cast, overload
from unittest.mock import patch

import pytest
from _pytest.config import Config, PytestPluginManager
from _pytest.fixtures import SubRequest
from _pytest.nodes import Item
from _pytest.python import Metafunc

_F = TypeVar("_F", bound=Callable[..., Any])


class ReturnValuesNotEqual(Exception):
    message = "Return values of idempotent functions must be equal."


class GlobalState:
    """
    Store essential metadata needed during the test runs.

    CHECK_IDEMPOTENCY: used to toggle the idempotency patch on/off
    current_test_item: a reference to the current pytest test context.
    """

    CHECK_IDEMPOTENCY: bool = False
    current_test_item: Item | None = None


_global_state = GlobalState()  # global variable needed for idempotency checking


@overload
def idempotent(func: _F | None) -> _F:
    ...


@overload
def idempotent(
    *, equal_return: bool = False, enforce_tests: bool = True
) -> Callable[[_F], _F]:
    ...


def idempotent(
    func: _F | None = None, equal_return: bool = False, enforce_tests: bool = True
) -> Any:
    """
    No-op during runtime.
    This marker allows Pytest to override the decorated function during
    test-time to verify the function is idempotent (e.g. no side effects).

    Use `equal_return=True` to specify that the function should always returns
    the same output when run multiple times.
    """
    del equal_return, enforce_tests

    @wraps(cast(_F, func))
    def _idempotent_inner(user_func: _F) -> _F:
        return user_func

    return _idempotent_inner if func is None else _idempotent_inner(func)


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """
    If @pytest.mark.idempotent is added to a function or class, run all
    selected tests twice, one as normal and one with the idempotency check.

    Allowed forms:
    @pytest.mark.idempotent
    @pytest.mark.idempotent(enabled=True)
    @pytest.mark.idempotent(enabled=False)
    """
    invalid_marker = metafunc.definition.get_closest_marker("test_idempotency")
    if invalid_marker is not None:
        raise RuntimeError("Use @pytest.mark.idempotent instead.")

    marker = metafunc.definition.get_closest_marker("idempotent")
    if marker is not None and (
        "enabled" not in marker.kwargs or marker.kwargs["enabled"]
    ):
        metafunc.parametrize(
            "add_idempotency_check",
            (False, True),
            indirect=True,
            ids=("no-idempotency-check", "idempotency-check"),
        )


@pytest.fixture(autouse=True)
def add_idempotency_check(request: SubRequest) -> Iterator[None]:
    """
    This fixture is added to all tests, but only patches CHECK_IDEMPOTENCY
    if this fixture is parametrized by the pytest_generate_tests metafunc.
    """
    if hasattr(request, "param"):
        with patch("pytest_idempotent.GlobalState.CHECK_IDEMPOTENCY", request.param):
            yield
    else:
        yield


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers",
        (
            "idempotent(enabled=True): mark test function or test class "
            "to run idempotency tests"
        ),
    )


def pytest_collection(session: pytest.Session) -> None:
    """Patch the @idempotent decorator for all tests."""
    decorator_path = (
        session.config.pluginmanager.hook.pytest_idempotent_decorator()
        or "pytest_idempotent.idempotent"
    )

    def _idempotent(
        func: _F | None = None, equal_return: bool = False, enforce_tests: bool = True
    ) -> Any:
        """
        Adds the `equal_return` parameter.

        The `func` pararmeter is only used to distinguish between different calls e.g.
            @idempotent
            @idempotent()
            @idempotent(equal_return=True)
        """

        @wraps(cast(_F, func))
        def _idempotent_inner(user_func: _F) -> _F:
            """Wrapper function used to handle the decorator with + without args."""

            def run_twice(*args: Any, **kwargs: Any) -> Any:
                """
                This function contains the new behavior of @idempotent.

                Runs the provided function twice, which allows the test to verify
                whether the provided function is idempotent.

                Returns the first run's result, which allows backwards-compatibility.
                e.g. a function that returns True if updated and False otherwise
                    is acceptably idempotent, unless equal_return = True.
                """
                assert _global_state.current_test_item is not None
                if (
                    enforce_tests
                    and _global_state.current_test_item.get_closest_marker("idempotent")
                    is None
                ):
                    pytest.fail(
                        "Test contains a call to the @idempotent decorated function: "
                        f"'{user_func.__qualname__}',\nbut the test does not use "
                        "the @pytest.mark.idempotent marker.\nPlease add this "
                        "marker to your test function or test class.\nTo skip "
                        "idempotency testing, add the marker with enabled=False: "
                        "@pytest.mark.idempotent(enabled=False)"
                    )

                run_1 = user_func(*args, **kwargs)
                if _global_state.CHECK_IDEMPOTENCY:
                    run_2 = user_func(*args, **kwargs)
                    if equal_return and run_1 != run_2:
                        raise ReturnValuesNotEqual(run_1, run_2)
                return run_1

            return cast(_F, run_twice)

        return _idempotent_inner if func is None else _idempotent_inner(func)

    # We need to patch the decorator in this function because the decorator
    # is applied when the module is imported, and once that happens it is too
    # late to patch its functionality.
    patch(decorator_path, _idempotent).start()


def pytest_runtest_call(item: Item) -> None:
    """
    Before the test begins, update the global state to
    point to the current test context.
    """
    _global_state.current_test_item = item


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
