"""Source content-lock — freeze the sha256 of every CITED corpus file (BPHS + allied).

Parashara citations are literal file line numbers into large OCR'd corpus files. A re-import / re-OCR
silently shifts those line numbers, rotting every downstream citation while `sources.verify` (which
only checks a line *exists*) stays green. This lock records each cited file's sha256 + line_count;
`tests/parashara/doctrine/test_source_lock.py` fails loudly if any cited file's content changed, OR
if a citation points at a file the lock does not cover.

`verify()` checks line EXISTENCE; this lock checks file IDENTITY — both are needed. This is the
sha256 source-lock the package docstring advertises as part of the shared fidelity apparatus.

Re-lock deliberately, only via ``UPDATE_SOURCE_LOCK=1`` and ONLY in a commit that has also
re-validated the affected citations against the new text:

    UPDATE_SOURCE_LOCK=1 py -3.12 -m pytest tests/parashara/doctrine/test_source_lock.py -q
"""
from __future__ import annotations

import hashlib
import importlib
import json
import pkgutil
from pathlib import Path
from typing import Iterator

import app.parashara as _parashara_pkg
from app.parashara.doctrine import sources
from app.parashara.doctrine.sources import Citation, _CORPUS

LOCK_PATH: Path = Path(__file__).resolve().parent / "source_lock.json"


def _walk_module_citations() -> Iterator[Citation]:
    """Every `Citation` reachable as a module-level constant (scalar, in a dict, or in a tuple/list)
    across app.parashara.* — the same exhaustive walk the citation-resolution guard uses."""
    for mod_info in pkgutil.walk_packages(_parashara_pkg.__path__, _parashara_pkg.__name__ + "."):
        try:
            mod = importlib.import_module(mod_info.name)
        except Exception:
            continue
        for attr in dir(mod):
            val = getattr(mod, attr, None)
            if isinstance(val, Citation):
                yield val
            elif isinstance(val, dict):
                for v in val.values():
                    if isinstance(v, Citation):
                        yield v
            elif isinstance(val, (tuple, list)):
                for v in val:
                    if isinstance(v, Citation):
                        yield v


def _grid_citations() -> Iterator[Citation]:
    """Citations built at RUNTIME by the grid/catalogue readers (their `work` tags are not all
    module-level `Citation` constants). Enumerated explicitly so every cited file is covered."""
    from app.parashara.doctrine.saravali_grids import all_house_effects
    from app.parashara.doctrine.saravali_dignity import all_concentration_effects
    from app.parashara.doctrine.saravali_conjunctions import (
        all_conjunctions, all_triple_conjunctions)
    from app.parashara.doctrine.karakamsa_effects import sections as karakamsa_sections
    from app.parashara.doctrine.upagraha_effects import all_effects as upagraha_effects
    from app.parashara.doctrine.bhava_effects import all_bhava_effects
    from app.parashara.doctrine.bhava_lord_effects import all_effects as bhava_lord_effects
    from app.parashara.doctrine.nabhasa import catalogue as nabhasa_catalogue
    from app.parashara.doctrine.yoga_catalogue import catalogue as yoga_catalogue

    for s in all_house_effects().values():
        yield s.source
    for s in all_concentration_effects().values():
        yield s.source
    for s in all_conjunctions().values():
        yield s.source
    for s in all_triple_conjunctions().values():
        yield s.source
    for s in karakamsa_sections():
        yield s.source
    for s in upagraha_effects().values():
        yield s.source
    for slokas in all_bhava_effects().values():
        for s in slokas:
            yield s.source
    for eff in bhava_lord_effects().values():
        yield eff.source
    for s in nabhasa_catalogue():
        yield s.source
    for slokas in yoga_catalogue().values():
        for s in slokas:
            yield s.source


def iter_citations() -> Iterator[Citation]:
    """Every Citation the engine holds — module-level constants + the runtime-built grids."""
    yield from _walk_module_citations()
    yield from _grid_citations()


def cited_files() -> dict[str, Path]:
    """{lock_key -> path} for every distinct file a citation resolves to (key = posix relpath
    under the corpus root)."""
    out: dict[str, Path] = {}
    for cit in iter_citations():
        path = sources._resolve_file(cit.work)
        if path is not None and path.is_file():
            out[path.relative_to(_CORPUS).as_posix()] = path
    return out


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def compute_lock() -> dict[str, dict]:
    """The lock that SHOULD be on disk for the current citations + corpus."""
    return {key: {"sha256": file_sha256(p), "line_count": _line_count(p)}
            for key, p in sorted(cited_files().items())}


def load_lock() -> dict[str, dict]:
    if not LOCK_PATH.is_file():
        return {}
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def write_lock() -> dict[str, dict]:
    """Regenerate source_lock.json (deliberate, human-gated by UPDATE_SOURCE_LOCK=1 in the test)."""
    lock = compute_lock()
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock
