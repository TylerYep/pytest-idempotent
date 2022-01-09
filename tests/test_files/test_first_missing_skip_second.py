from __future__ import annotations

import pytest


@pytest.mark.idempotent
def test_case() -> None:
    raise Exception
