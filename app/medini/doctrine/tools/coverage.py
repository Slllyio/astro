"""Coverage manifests — "complete" is auditable, not asserted.

Each extraction sweep records, per chapter, whether it was swept, skipped
(with a reason), or partially done. Manifests are merged across sweeps and
rendered to ``docs/raman_doctrine/COVERAGE.md`` so partial sweeps stay
durable and resumable across sessions.

Manifest file: ``data/raman_doctrine/coverage/<book>.json``::

    {"book": "hpa",
     "chapters": [{"label": "XVII", "title": "...", "status": "swept",
                   "rule_count": 12, "sweep_id": "s1", "notes": null}, ...]}
"""
from __future__ import annotations

import json
from pathlib import Path

COVERAGE_DIR = Path("data/raman_doctrine/coverage")

STATUSES = ("pending", "swept", "partial", "skipped")


def load_manifest(book: str, directory: Path = COVERAGE_DIR) -> dict:
    path = directory / f"{book}.json"
    if not path.exists():
        return {"book": book, "chapters": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(manifest: dict, directory: Path = COVERAGE_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{manifest['book']}.json"
    path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")


def init_chapters(book: str, chunks, directory: Path = COVERAGE_DIR) -> dict:
    """Seed a manifest with every chunk as ``pending`` (idempotent: existing
    chapter entries are kept, new chunks appended)."""
    manifest = load_manifest(book, directory)
    known = {c["label"] for c in manifest["chapters"]}
    for chunk in chunks:
        if chunk.label not in known:
            manifest["chapters"].append({
                "label": chunk.label,
                "title": chunk.title,
                "status": "pending",
                "rule_count": 0,
                "sweep_id": None,
                "notes": None,
            })
    return manifest


def mark(manifest: dict, label: str, status: str, *, rule_count: int = 0,
         sweep_id: str | None = None, notes: str | None = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"unknown status {status!r}")
    for ch in manifest["chapters"]:
        if ch["label"] == label:
            ch.update(status=status, rule_count=rule_count,
                      sweep_id=sweep_id, notes=notes)
            return
    raise KeyError(f"{manifest['book']}: no chapter {label!r} in manifest")


def render_coverage_md(directory: Path = COVERAGE_DIR) -> str:
    """Render every manifest into the COVERAGE.md body."""
    lines = [
        "# Raman Doctrine Compendium — Coverage",
        "",
        "Per-chapter extraction status, written by the sweep tooling —",
        "never edited by hand. `pending` chapters are un-swept; a book is",
        "complete only when nothing is pending and every skip has a reason.",
        "",
    ]
    for path in sorted(directory.glob("*.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        chapters = manifest["chapters"]
        done = sum(1 for c in chapters if c["status"] == "swept")
        lines.append(f"## {manifest['book']} — {done}/{len(chapters)} chapters swept")
        lines.append("")
        lines.append("| chapter | title | status | rules | sweep | notes |")
        lines.append("|---|---|---|---:|---|---|")
        for c in chapters:
            lines.append(
                f"| {c['label']} | {c['title'][:60]} | {c['status']} | "
                f"{c['rule_count']} | {c['sweep_id'] or ''} | {c['notes'] or ''} |"
            )
        lines.append("")
    return "\n".join(lines) + "\n"
