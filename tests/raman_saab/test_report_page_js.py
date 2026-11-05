"""Syntax gate for the interactive report page's inline JavaScript.

The page (`app/medini/templates/report.html`) carries ~2,000 lines of inline
script with no build step and, until this gate, nothing that would catch a
syntax error before a user's browser did. Each ``<script>`` body must parse
under ``node --check``. Skipped where node is absent.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

_PAGE = Path(__file__).resolve().parents[2] / "app" / "medini" / "templates" / "report.html"
_NODE = shutil.which("node")


@pytest.mark.skipif(_NODE is None, reason="node not available on this machine")
def test_every_inline_script_parses(tmp_path):
    """node --check accepts every <script> body on the interactive report page."""
    html = _PAGE.read_text(encoding="utf-8")
    bodies = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert bodies, "no inline scripts found — page structure changed?"
    for i, body in enumerate(bodies):
        f = tmp_path / f"page_script_{i}.js"
        f.write_text(body, encoding="utf-8")
        r = subprocess.run([_NODE, "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, f"script {i} fails node --check:\n{r.stderr[:2000]}"
