# pytest-idempotent

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![PyPI version](https://badge.fury.io/py/pytest-idempotent.svg)](https://badge.fury.io/py/pytest-idempotent)
[![Build Status](https://github.com/TylerYep/pytest-idempotent/actions/workflows/test.yml/badge.svg)](https://github.com/TylerYep/pytest-idempotent/actions/workflows/test.yml)
[![GitHub license](https://img.shields.io/github/license/TylerYep/pytest-idempotent)](https://github.com/TylerYep/pytest-idempotent/blob/main/LICENSE)
[![codecov](https://codecov.io/gh/TylerYep/pytest-idempotent/branch/main/graph/badge.svg)](https://codecov.io/gh/TylerYep/pytest-idempotent)
[![Downloads](https://pepy.tech/badge/pytest-idempotent)](https://pepy.tech/project/pytest-idempotent)

Pytest plugin for testing the idempotency of a function.

## Usage

```
pip install pytest-idempotent
```

## Documentation

Suppose we had the following function, that we (incorrectly) assumed was idempotent. How would we write a test for this?

First, we can label the function with a decorator:

```python
# abc.py
from pytest_idempotent import idempotent  # or use your own decorator! See below.

@idempotent
def func(x: list[int]) -> None:
    x += [9]
```

Note: this function is _not_ idempotent because calling it on the same list `x` grows the size of `x` by 1 each time. To be idempotent, we should be able to run `func` more than once without any adverse effects.

We can write an idempotency test for this function as follows:

```python
# tests/abc_test.py
import pytest

@pytest.mark.idempotent
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
```

Adding the `@pytest.mark.idempotent` mark automatically splits this test into two - one that tests the regular behavior, and one that tests that the function can be called twice without adverse effects.

```
❯❯❯ pytest

================= test session starts ==================
platform darwin -- Python 3.9.2, pytest-6.2.5
collected 2 items

tests/abc_test.py .F                     [100%]

=====================  FAILURES ========================
------------- test_func[idempotency-check] -------------

    @pytest.mark.idempotent
    def test_func() -> None:
        x: list[int] = []

        func(x)

>       assert x == [9]
E       assert [9, 9] == [9]
E         Left contains one more item: 9
E         Use -v to get the full diff

tests/abc_test.py:19: AssertionError
=============== short test summary info ================
FAILED tests/abc_test.py::test_func[idempotency-check]
  - assert [9, 9] == [9]
============= 1 failed, 1 passed in 0.16s ==============
```

## How It Works

Idempotency is a difficult pattern to enforce. To solve this issue, **pytest-idempotent** takes the following approach:

- Introduce a decorator, `@idempotent`, to functions.

  - This decorator serves as a visual aid. If this decorator is commonly used in the codebase, it is much easier to consider idempotency for new and existing functions.
  - At runtime, this decorator is a no-op.
  - At test-time, if the feature is enabled, we will run the decorated function twice with the same parameters in all test cases.
  - We can also assert that the second run returns the same result using an additional parameter to the function's decorator: `@idempotent(equal_return=True)`.

- For all tests marked using `@pytest.mark.idempotent`, we run each test twice: once normally, and once with the decorated function called twice.
  - Both runs need to pass all assertions.
  - We return the first result because the first run will complete the processing. The second will either return exact the same result or be a no-op.
  - To disable idempotency testing for a test or group of tests, add the Pytest marker:
    `@pytest.mark.idempotent(enabled=False)`

## Enforcing Tests Use `@pytest.mark.idempotent`

By default, any test that calls an `@idempotent` function must also be decorated with the marker `@pytest.mark.idempotent`.

To disable idempotency testing for a test or group of tests, use:
`@pytest.mark.idempotent(enabled=False)`, or add the following config to your project:

```python
def pytest_idempotent_enforce_tests() -> bool:
    return False
```

To disable enforced idempotency testing for a specific function, you can also pass the flag into the decorator:

```python
# abc.py
from pytest_idempotent import idempotent

@idempotent(enforce_tests=False)
def func() -> None:
    return
```

<!-- To automatically enable this marker for all tests, you can use a custom autouse fixture. (Warning: this will run ALL tests twice, regardless of whether they contain an idempotent function or not.) -->

Or, you can automatically add the marker based on the test name by adding to `conftest.py`:

```python
# conftest.py
def pytest_collection_modifyitems(items):
    for item in items:
        if "idempotent" in item.nodeid:
            item.add_marker(pytest.mark.idempotent)
```

## @idempotent decorator

By default, the `@idempotent` decorator does nothing during runtime. We do not want to add overhead to production code to run tests.

```python
from typing import Any, Callable, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])


def idempotent(func: _F) -> _F:
    """
    No-op during runtime.
    This marker allows pytest-idempotent to override the decorated function
    during test-time to verify the function is idempotent.
    """
    return func
```

To use your own `@idempotent` decorator, you can override the `pytest_idempotent_decorator` function in your `conftest.py` to return the module path to your implementation.

```python
# conftest.py
# Optional: you can define this to ensure the plugin is correctly installed
pytest_plugins = ["pytest_idempotent"]


def pytest_idempotent_decorator() -> str:
    # This links to my custom implementation of @idempotent.
    return "src.utils.idempotent"
```
