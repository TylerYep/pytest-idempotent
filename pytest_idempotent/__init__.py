from __future__ import annotations

import warnings
from functools import wraps
from typing import Any, Callable, Iterator, TypeVar, cast, overload
from unittest.mock import patch

import pytest
from _pytest.config import Config, PytestPluginManager
from _pytest.fixtures import SubRequest
from _pytest.python import Function, Metafunc
from _pytest.runner import CallInfo

_F = TypeVar("_F", bound=Callable[..., Any])
NO_IDEMPOTENCY_ID = "no_idempotency"
CHECK_IDEMPOTENCY_ID = "check_idempotency"
MISSING_PYTEST_MARKER = (
    "Test contains a call to the @idempotent decorated function: '{}',\n"
    "but the test does not have the @pytest.mark.idempotent marker. "
    "Please add this marker to your test function or test class.\n"
    "To skip idempotency testing, add the marker with enabled=False: "
    "@pytest.mark.idempotent(enabled=False)"
)
IDEMPOTENCY_TEST_OUT_OF_ORDER = (
    "Idempotency tests are not in the correct sorted order.\n"
    "Running this idempotency test regardless, but for best results "
    "it is recommended that you disable random ordering of your tests."
)
SKIPPING_IDEMPOTENCY_CHECK = (
    "The first run of this test either failed or did not contain "
    "an @idempotent function call, so skipping idempotency test."
)
MISSING_IDEMPOTENT_FUNCTION = (
    "Test is marked with @pytest.mark.idempotent but does not contain "
    "an @idempotent decorated function.\nEither remove the marker or use "
    "@pytest.mark.idempotent(enabled=False)."
)

# ------------------- Exceptions -------------------


class MissingPytestIdempotentMarker(BaseException):
    """
    This exception should fail the test immediately. To capture most cases,
    we inherit BaseException in order to force exit the test.
    Ideally, we could use pytest.fail(), but that hangs in tests with multiple threads.
    """

    message = (
        "All tests containing @idempotent decorated functions "
        "must use the @pytest.mark.idempotent marker."
    )


class ReturnValuesNotEqual(Exception):
    message = "Return values of idempotent functions must be equal."


# ------------------- GlobalState -------------------


class GlobalState:
    """
    Store essential metadata needed during the test runs.

    - should_run_twice: used to toggle the idempotency patch on/off.
    - current_test_item: a reference to the current pytest test context.
    - contains_idempotent_function: True if an @idempotent decorated function called.
    - all_test_runs: dict mapping item.nodeid to bool(NO_IDEMPOTENCY_ID test passed
        and test contained at least 1 @idempotent decorated function)
    """

    should_run_twice: bool = False
    current_test_item: Function | None = None
    contains_idempotent_function: bool = True  # default True until test begins
    all_test_runs: dict[str, bool] = {}


_global_state = GlobalState()  # global variable needed for idempotency checking


# ------------------- User-facing imports -------------------


@overload
def idempotent(func: _F | None) -> _F:
    ...  # pragma: no cover


@overload
def idempotent(
    *, equal_return: bool = False, enforce_tests: bool = True
) -> Callable[[_F], _F]:
    ...  # pragma: no cover


def idempotent(
    func: _F | None = None, equal_return: bool = False, enforce_tests: bool = True
) -> Any:  # pragma: no cover
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


# ------------------- Pytest Hooks -------------------


@pytest.fixture(autouse=True)
def add_idempotency_check(request: SubRequest) -> Iterator[None]:
    """
    This fixture is added to all tests, but only patches GlobalState.should_run_twice
    if this fixture is parametrized by the pytest_generate_tests metafunc.
    """
    if hasattr(request, "param"):
        with patch("pytest_idempotent.GlobalState.should_run_twice", request.param):
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
    enforce_test_setting = (
        session.config.pluginmanager.hook.pytest_idempotent_enforce_tests()
    )

    def _idempotent(
        func: _F | None = None,
        equal_return: bool = False,
        enforce_tests: bool | None = None,
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
            """Wrapper function used to handle the decorator with or without args."""

            def run_twice(*args: Any, **kwargs: Any) -> Any:
                """
                This function contains the new behavior of @idempotent.

                Runs the provided function twice, which allows the test to verify
                whether the provided function is idempotent.

                Returns the first run's result, which allows backwards-compatibility.
                e.g. a function that returns True if updated and False otherwise
                    is acceptably idempotent, unless equal_return = True.
                """
                _global_state.contains_idempotent_function = True
                assert _global_state.current_test_item is not None
                if (
                    _global_state.current_test_item.get_closest_marker("idempotent")
                    is None
                ):
                    message = MISSING_PYTEST_MARKER.format(user_func.__qualname__)
                    if enforce_tests is None:
                        if enforce_test_setting is None or enforce_test_setting:
                            raise MissingPytestIdempotentMarker(message)
                        warnings.warn(message)
                    elif enforce_tests:
                        raise MissingPytestIdempotentMarker(message)

                run_1 = user_func(*args, **kwargs)
                if _global_state.should_run_twice:
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


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """
    If @pytest.mark.idempotent is added to a function or class, run all
    selected tests twice, one as normal and one with the idempotency check.

    Allowed forms:
    @pytest.mark.idempotent
    @pytest.mark.idempotent(enabled=True)
    @pytest.mark.idempotent(enabled=False)
    """
    if is_idempotent_marker_enabled(metafunc.definition):
        metafunc.parametrize(
            "add_idempotency_check",
            (False, True),
            indirect=True,
            ids=(NO_IDEMPOTENCY_ID, CHECK_IDEMPOTENCY_ID),
        )


def pytest_runtest_call(item: Function) -> None:
    """
    Before the test begins, update the global state to
    point to the current test context.
    """
    if is_idempotency_test(item, CHECK_IDEMPOTENCY_ID):
        first_run_result = _global_state.all_test_runs.get(get_pair_nodeid(item))
        if first_run_result is None:
            warnings.warn(IDEMPOTENCY_TEST_OUT_OF_ORDER)
        elif not first_run_result:
            pytest.skip(SKIPPING_IDEMPOTENCY_CHECK)

    _global_state.current_test_item = item
    _global_state.contains_idempotent_function = False


def pytest_runtest_teardown(item: Function, nextitem: Function | None) -> None:
    """
    Warns if the finished test has the @pytest.mark.idempotent marker
    but did not call any function with the @idempotent decorator. This discourages
    users from running many tests twice unecessarily (the second is skipped).
    """
    del nextitem
    if not _global_state.contains_idempotent_function and is_idempotency_test(
        item, CHECK_IDEMPOTENCY_ID
    ):
        warnings.warn(MISSING_IDEMPOTENT_FUNCTION)


def pytest_runtest_makereport(item: Function, call: CallInfo[None]) -> None:
    """If a NO_IDEMPOTENCY_ID test passes, add the result to all_test_runs."""
    if call.when == "call" and is_idempotency_test(item, NO_IDEMPOTENCY_ID):
        # Store test result, or False if @idempotent function is missing.
        _global_state.all_test_runs[item.nodeid] = (
            not call.excinfo if _global_state.contains_idempotent_function else False
        )


class PytestIdempotentSpec:
    """Hook specification namespace for this plugin."""

    @pytest.hookspec(firstresult=True)  # type: ignore[misc]
    def pytest_idempotent_decorator(self) -> str:
        """
        Plugin users define this function in conftest.py to configure
        the default path for the @idempotent decorator.
        """

    @pytest.hookspec(firstresult=True)  # type: ignore[misc]
    def pytest_idempotent_enforce_tests(self) -> bool:
        """
        Plugin users define this function in conftest.py to enforce all tests
        with an @idempotent function use the @pytest.mark.idempotent marker.
        """


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    pluginmanager.add_hookspecs(PytestIdempotentSpec)


# ------------------- Util Functions -------------------


def is_idempotent_marker_enabled(item: Function) -> bool:
    """Returns True if the test item has the @pytest.mark.idempotent marker enabled."""
    marker = item.get_closest_marker("idempotent")
    return marker is not None and (
        "enabled" not in marker.kwargs or marker.kwargs["enabled"]
    )


def is_idempotency_test(item: Function, test_id: str) -> bool:
    """
    Returns True if the test item has the @pytest.mark.idempotent marker
    enabled and matches the given test_id.
    """
    return is_idempotent_marker_enabled(item) and test_id in item.callspec.id


def get_pair_nodeid(item: Function) -> str:
    return (
        f"{item.nodeid[:item.nodeid.index('[')]}"
        f"[{item.callspec.id.replace(CHECK_IDEMPOTENCY_ID, NO_IDEMPOTENCY_ID)}]"
    )
