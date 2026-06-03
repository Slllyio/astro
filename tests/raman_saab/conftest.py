"""Pytest config local to the Raman Saab test suite.

Registers custom markers so they don't warn as unknown. Hierarchical conftest:
this is merged with the repo-level tests/conftest.py, so both pytest_configure
hooks run — no need to touch the shared file.
"""
from __future__ import annotations


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "external_pin: test pinned to an external reference (drikpanchang.com / "
        "Jagannatha Hora); no-ops until the expected value is filled in.",
    )
