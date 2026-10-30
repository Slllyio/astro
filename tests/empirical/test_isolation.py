"""The one-way isolation contract between ``app.empirical`` and the Raman engine.

``CLAUDE.md`` § MEASURED TRUTH makes the Raman engine's textbook-fidelity
ceiling a locked, ratcheted result. This subsystem asks a different question on
different ground, and must not be able to perturb that result — not by import
side effects, not by shared mutable state, not by a future refactor that
"helpfully" reuses an empirical helper inside a doctrine path.

The direction that matters is: **nothing under ``app/raman_saab`` or
``app/core`` may import ``app.empirical``.** The reverse is permitted in
principle but is currently unused, and this file records that too, so a future
coupling is a conscious decision rather than a drift.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_GUARDED_TREES = ("app/raman_saab", "app/core")


def _imported_modules(path: Path) -> set[str] | None:
    """Every module name imported by a source file, or ``None`` if unparseable.

    The project targets Python 3.12; a 3.11 interpreter cannot parse PEP 701
    f-strings that appear in some engine modules. Returning ``None`` lets the
    caller fall back to a text scan instead of silently exempting the file.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return None
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def _offenders(tree_root: str, forbidden_prefix: str) -> list[str]:
    """Files under ``tree_root`` that import ``forbidden_prefix``.

    Unparseable files are still checked, by text — a guard that skipped what it
    could not parse would be strongest exactly where it is least reliable.
    """
    out: list[str] = []
    for path in Path(tree_root).rglob("*.py"):
        names = _imported_modules(path)
        if names is None:
            source = path.read_text(encoding="utf-8")
            if f"import {forbidden_prefix}" in source or f"from {forbidden_prefix}" in source:
                out.append(f"{path} imports {forbidden_prefix} (text scan; file not parseable here)")
            continue
        for name in names:
            if name == forbidden_prefix or name.startswith(forbidden_prefix + "."):
                out.append(f"{path} imports {name}")
    return out


class TestRamanEngineIsolation:
    """The golden ratchet must be unreachable from here."""

    @pytest.mark.parametrize("tree_root", _GUARDED_TREES)
    def test_guarded_tree_does_not_import_app_empirical(self, tree_root: str):
        """No doctrine or core module may depend on the empirical subsystem."""
        if not Path(tree_root).is_dir():
            pytest.skip(f"{tree_root} absent in this checkout")
        assert _offenders(tree_root, "app.empirical") == []

    def test_empirical_does_not_import_the_raman_engine(self):
        """Recorded, not merely assumed: the coupling does not exist today.

        Importing Raman doctrine into an empirical feature bank would make the
        tournament a test of the engine rather than of the astrology, and would
        reintroduce the exact confound the subsystem exists to avoid.
        """
        assert _offenders("app/empirical", "app.raman_saab") == []


class TestPackageSurface:
    """The package advertises what it actually ships."""

    def test_western_package_exports_every_module_it_lists(self):
        """``__all__`` must not name a module that does not import."""
        import importlib

        from app.empirical import western

        for name in western.__all__:
            importlib.import_module(f"app.empirical.western.{name}")
