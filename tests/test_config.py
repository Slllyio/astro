"""Tests for app.core.config.Settings — production-secret enforcement.

The dev-only SECRET_KEY shipped in .env.example must NEVER be active in
staging/prod. This catches the most common deploy mistake: copying
.env.example to .env without rotating the secret.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, _DEV_PLACEHOLDER_SECRET


def _build(**overrides):
    """Instantiate Settings WITHOUT loading .env so tests are hermetic.

    We can't disable env_file via constructor in pydantic-settings v2, but
    we can pass overrides that take priority over .env values. For each
    field we care about, pass an explicit value.
    """
    defaults = {
        "ENVIRONMENT": "dev",
        "SECRET_KEY": _DEV_PLACEHOLDER_SECRET,
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestSecretKeyEnforcement:
    """Production must not run on the dev placeholder secret."""

    def test_dev_env_allows_placeholder_secret(self):
        """The whole point of the placeholder is to let local dev boot."""
        s = _build(ENVIRONMENT="dev", SECRET_KEY=_DEV_PLACEHOLDER_SECRET)
        assert s.SECRET_KEY == _DEV_PLACEHOLDER_SECRET

    def test_staging_env_rejects_placeholder_secret(self):
        """A staging deploy that forgot to rotate the secret must fail fast."""
        with pytest.raises(ValidationError) as exc_info:
            _build(ENVIRONMENT="staging", SECRET_KEY=_DEV_PLACEHOLDER_SECRET)
        assert "SECRET_KEY is the dev placeholder" in str(exc_info.value)

    def test_prod_env_rejects_placeholder_secret(self):
        """Same protection in prod."""
        with pytest.raises(ValidationError) as exc_info:
            _build(ENVIRONMENT="prod", SECRET_KEY=_DEV_PLACEHOLDER_SECRET)
        assert "SECRET_KEY is the dev placeholder" in str(exc_info.value)

    def test_staging_env_accepts_rotated_secret(self):
        """A rotated secret in staging is fine."""
        s = _build(ENVIRONMENT="staging", SECRET_KEY="x" * 64)
        assert s.SECRET_KEY == "x" * 64

    def test_prod_env_accepts_rotated_secret(self):
        """A rotated secret in prod is fine."""
        s = _build(ENVIRONMENT="prod", SECRET_KEY="y" * 64)
        assert s.SECRET_KEY == "y" * 64

    def test_dev_env_accepts_rotated_secret(self):
        """Devs who want to rotate locally are not blocked."""
        s = _build(ENVIRONMENT="dev", SECRET_KEY="z" * 64)
        assert s.SECRET_KEY == "z" * 64
