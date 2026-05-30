"""Claude Code PostToolUse hook: run the paired test for an edited Python file.

Wired by `.claude/settings.json`. Reads the hook payload from stdin, derives
the matching `tests/test_<name>.py`, and runs only that file (so the loop is
seconds, not minutes). Silent when there is no paired test.

Exit codes:
  0  — tests passed, or no paired test exists (no-op).
  2  — tests failed; pytest output goes to stderr and is shown back to Claude.

Hook payload shape (from Claude Code docs):
  {
    "session_id": "...",
    "tool_name": "Edit" | "Write" | "MultiEdit",
    "tool_input": {"file_path": "<absolute path>", ...}
  }
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

# Files that should never trigger the test loop.
SKIP_PREFIXES: tuple[str, ...] = (
    "scratch_",   # exploration scripts at repo root
    "_",          # private helpers
)
SKIP_SUFFIXES: tuple[str, ...] = (
    "__init__.py",
    "conftest.py",
)


def _resolve_test_for(edited: Path) -> Path | None:
    """Map an edited .py file to its paired tests/test_<name>.py."""
    if edited.suffix != ".py":
        return None
    if edited.name in SKIP_SUFFIXES:
        return None
    if any(edited.name.startswith(p) for p in SKIP_PREFIXES):
        return None

    candidate = TESTS_DIR / f"test_{edited.stem}.py"
    return candidate if candidate.is_file() else None


def _run_pytest(test_file: Path) -> int:
    """Invoke pytest on a single file; return its exit code."""
    cmd = [
        "py", "-3.12", "-m", "pytest",
        str(test_file),
        "-x",
        "--tb=short",
        "--no-header",
        "-q",
    ]
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(
            f"\n[run_related_tests] {test_file.name} FAILED — Claude, fix before continuing:\n"
        )
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        return 2
    # Quiet on success — don't spam the chat with green dots.
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Hook fired with no/garbage stdin — fail open (do not block tool).
        return 0

    tool_input = payload.get("tool_input") or {}
    raw_path = tool_input.get("file_path")
    if not raw_path:
        return 0

    try:
        edited = Path(raw_path).resolve()
    except OSError:
        return 0

    # Only act on files inside this repo.
    try:
        edited.relative_to(REPO_ROOT)
    except ValueError:
        return 0

    test_file = _resolve_test_for(edited)
    if test_file is None:
        return 0

    return _run_pytest(test_file)


if __name__ == "__main__":
    sys.exit(main())
