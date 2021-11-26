# pytest-idempotent

[![Python 3.5+](https://img.shields.io/badge/python-3.5+-blue.svg)](https://www.python.org/downloads/release/python-350/)
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

Suppose we had the following function, that we (incorrectly) assumed is idempotent (AKA we should be able to run it more than once without any adverse effects).

```python
from pytest_idempotent import idempotent  # or use your own decorator!

@idempotent
def func(x: list[int]) -> None:
    x += [9]
```

Note: this function is _not_ idempotent because calling it on the same list `x` grows the size of `x` by 1 each time.

We can write an idempotency test for this function as follows:

```python
# idempotency_test.py
import pytest

@pytest.mark.test_idempotency
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
```

Adding the `@pytest.mark.test_idempotency` mark automatically splits this test into two - one that tests the regular behavior and one that tests that the function can be called twice without adverse effects.

```
❯❯❯ pytest

================= test session starts ==================
platform darwin -- Python 3.9.2, pytest-6.2.5
collected 2 items

tests/idempotency_test.py .F                     [100%]

=====================  FAILURES ========================
------------- test_func[idempotency-check] -------------

    @pytest.mark.test_idempotency
    def test_func() -> None:
        x: list[int] = []

        func(x)

>       assert x == [9]
E       assert [9, 9] == [9]
E         Left contains one more item: 9
E         Use -v to get the full diff

tests/idempotency_test.py:19: AssertionError
=============== short test summary info ================
FAILED tests/idempotency_test.py::test_func[idempotency-check]
  - assert [9, 9] == [9]
============= 1 failed, 1 passed in 0.16s ==============
```

## How It Works

Idempotency is a difficult pattern to enforce. To solve this issue, **pytest-idempotent** takes the following approach:

- Introduce a decorator, `@idempotent`, to functions.

  - This decorator serves as a visual aid. If this decorator is commonly used in the codebase, it is much easier to consider idempotency for new and existing functions.
  - At runtime, this decorator is a no-op.
  - At test-time, if the feature is enabled, we will run the decorated function twice with the same parameters in all test cases.

- For all tests marked with `@pytest.mark.test_idempotency`, we run each test twice: once normally, and once with the decorated function called twice.
  - Both runs need to pass all assertions.
  - We return the first result because the first run should complete the processing. The second will either return exact the same result or be a no-op.
  - We can also assert that the second run returns the same result as an additional parameter.

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
    """This links to my custom implementation of @idempotent."""
    return "src.utils.idempotent"
```
