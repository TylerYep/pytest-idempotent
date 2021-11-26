# pytest-idempotent

[![Python 3.5+](https://img.shields.io/badge/python-3.5+-blue.svg)](https://www.python.org/downloads/release/python-350/)
[![PyPI version](https://badge.fury.io/py/pytest-idempotent.svg)](https://badge.fury.io/py/pytest-idempotent)
[![Build Status](https://github.com/TylerYep/pytest-idempotent/actions/workflows/test.yml/badge.svg)](https://github.com/TylerYep/pytest-idempotent/actions/workflows/test.yml)
[![GitHub license](https://img.shields.io/github/license/TylerYep/pytest-idempotent)](https://github.com/TylerYep/pytest-idempotent/blob/main/LICENSE)
[![codecov](https://codecov.io/gh/TylerYep/pytest-idempotent/branch/main/graph/badge.svg)](https://codecov.io/gh/TylerYep/pytest-idempotent)
[![Downloads](https://pepy.tech/badge/pytest-idempotent)](https://pepy.tech/project/pytest-idempotent)

Pytest plugin for testing the idempotency of a function.


## Documentation

Suppose we had the following function, that we (incorrectly) declare is idempotent.

```python
from pytest_idempotent import idempotent

@idempotent
def func(x: list[int]) -> None:
    x += [9]
```


```python
import pytest

@pytest.mark.test_idempotency
def test_func() -> None:
    x: list[int] = []

    func(x)

    assert x == [9]
```