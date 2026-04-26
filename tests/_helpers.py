"""Shared test helpers (importable by tests; not auto-loaded by pytest)."""
from __future__ import annotations

from typing import Any


def sample_profile_payload(name: str = "Test User", **birth_overrides: Any) -> dict[str, Any]:
    """Stable POST /profiles body used across persistence and daemon tests."""
    payload: dict[str, Any] = {
        "name": name,
        "birth_data": {
            "year": 1990,
            "month": 7,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "latitude": 12.97,
            "longitude": 77.59,
            "tz_offset": 5.5,
        },
    }
    if birth_overrides:
        payload["birth_data"].update(birth_overrides)
    return payload
