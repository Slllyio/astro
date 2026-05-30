"""Emit the JSON Schema for `ReadingOutput` to `docs/reading/json-schema.json`.

Usage:
    py -3.12 -m scripts.generate_schema_json
    # or
    py -3.12 scripts/generate_schema_json.py

This is a one-shot regeneration helper. Run it whenever
`app/reading/schema.py` changes so that downstream JSON-Schema consumers
(IDE tooling, contract tests, language-binding generators) stay in sync
with the Pydantic source of truth.

The generated file is **committed** alongside the source schema so
consumers can `git pull` it without needing a working Python environment.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow `py -3.12 scripts/generate_schema_json.py` from the repo root
# without an installed package. (Running via `-m scripts.generate_schema_json`
# from the repo root works without this dance.)
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.reading.schema import ReadingOutput  # noqa: E402  (sys.path patched above)


def main() -> None:
    """Write the JSON Schema for `ReadingOutput` to disk."""
    out = (
        Path(__file__).resolve().parent.parent
        / "docs"
        / "reading"
        / "json-schema.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(ReadingOutput.model_json_schema(), indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
