"""Claude Code PreToolUse hook: block edits to protected paths.

Wired by `.claude/settings.json`. Reads the hook payload from stdin and
blocks the Edit/Write/MultiEdit call (exit 2) if the target matches a
protected pattern: `.env`, generated parquet artifacts, or the source-of-
truth PDF.

Exit codes:
  0  — allow the tool call.
  2  — block the tool call. Stderr message is shown back to Claude.

Hook payload shape (from Claude Code docs):
  {
    "session_id": "...",
    "tool_name": "Edit" | "Write" | "MultiEdit",
    "tool_input": {"file_path": "<absolute path>", ...}
  }
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Each entry: (compiled pattern matched against the POSIX-style relative path,
# human-readable explanation shown to Claude when the edit is blocked).
PROTECTED: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"^\.env$"),
        ".env holds secrets. Edit .env.example instead and tell the user "
        "to copy/edit .env locally.",
    ),
    (
        re.compile(r"^data/ml_runs/.*\.parquet$"),
        "data/ml_runs/**/*.parquet are generated ML-run artifacts. "
        "Re-run the training pipeline rather than hand-editing.",
    ),
    (
        re.compile(r"^app/medini/data/.*\.parquet$"),
        "app/medini/data/*.parquet are generated ETL artifacts. "
        "Rebuild via the corresponding `python -m app.medini.etl.<stage>` "
        "rather than hand-editing.",
    ),
    (
        re.compile(r"^Geo-Astrological Planetary Intelligence Engine\.pdf$"),
        "The PDF is the canonical doctrine reference. Don't modify it.",
    ),
)


def _classify(rel_posix: str) -> str | None:
    """Return the deny reason if path is protected, else None."""
    for pattern, reason in PROTECTED:
        if pattern.match(rel_posix):
            return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Garbage stdin — fail open so we don't break the loop.
        return 0

    tool_input = payload.get("tool_input") or {}
    raw_path = tool_input.get("file_path")
    if not raw_path:
        return 0

    try:
        abs_path = Path(raw_path).resolve()
        rel = abs_path.relative_to(REPO_ROOT)
    except (OSError, ValueError):
        # File outside the repo, or unresolvable — not our concern.
        return 0

    rel_posix = rel.as_posix()
    reason = _classify(rel_posix)
    if reason is None:
        return 0

    sys.stderr.write(
        f"[block_protected_paths] BLOCKED edit to '{rel_posix}'.\n"
        f"Reason: {reason}\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
