"""Run directories and JSONL stage files."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Final

RUNS_ROOT: Final[Path] = Path("data/pipeline_runs")


def new_run_id() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def run_dir(run_id: str, root: Path = RUNS_ROOT) -> Path:
    d = root / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                    encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def load_goldens(path: Path) -> list[dict[str, Any]]:
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            out.append(json.loads(s))
    return out
