"""Source content-lock — freeze the sha256 of every CITED corpus file.

Citations are literal file line numbers into large OCR'd corpus files. A re-import / re-OCR
silently shifts those line numbers, rotting every downstream citation while `sources.verify`
(which only checks a line *exists*) stays green. This lock records each cited file's sha256 +
line_count; `tests/raman_saab/doctrine/test_source_lock.py` fails loudly if any cited file's
content changed, OR if a citation points at a file the lock does not cover.

`verify()` checks line EXISTENCE; this lock checks file IDENTITY — both are needed.

Re-lock deliberately, only via ``UPDATE_SOURCE_LOCK=1`` and ONLY in a commit that has also
re-validated the affected citations against the new text:

    UPDATE_SOURCE_LOCK=1 py -3.12 -m pytest tests/raman_saab/doctrine/test_source_lock.py -q
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterator

from app.raman_saab.doctrine import sources
from app.raman_saab.doctrine.sources import Citation, _CORPUS

# The lock is a COMMITTED integrity artifact, so it lives in the tracked doctrine tree — NOT under
# the (git-ignored) corpus dir. It hashes the local corpus the citations point at; a teammate's
# differing OCR will fail the lock test, which is the intended cross-machine corpus check.
LOCK_PATH: Path = Path(__file__).resolve().parent / "source_lock.json"


def iter_citations() -> Iterator[Citation]:
    """Every `Citation` the engine holds: rules, yogas, significations, and the lookup tables.
    (All resolve to HTJAH-I/II/3HC today; the enumeration is exhaustive so a NEW citation into a
    new file is caught by the lock test.)"""
    from app.raman_saab.doctrine.rule_sets import ALL_RULES
    from app.raman_saab.doctrine.synthesis_rules import SYNTHESIS_RULES
    from app.raman_saab.doctrine.yogas import YOGAS
    from app.raman_saab.doctrine.significations import SIGNIFICATIONS
    from app.raman_saab.doctrine.lookups.bhavartha_ratnakara import KARAKA_IN_12_INVERSIONS
    from app.raman_saab.doctrine.lookups.confinement_modes import CONFINEMENT_MODES
    from app.raman_saab.doctrine.lookups.decanate_cause import DECANATE_CAUSES
    from app.raman_saab.doctrine.lookups.disease_map import (
        PLANET_ORGANS, PLANET_SEASONS, PLANET_TRIDOSHAS)
    from app.raman_saab.doctrine.lookups.source_of_gains import (
        PLANET_IN_11TH_GAINS, SECOND_LORD_HOUSE_GAINS)

    for rule in ALL_RULES:
        yield rule.source
    for syn in SYNTHESIS_RULES:                 # cross-feature synthesis (raman band only cites)
        if syn.source is not None:
            yield syn.source
    for yoga in YOGAS:
        yield yoga.source
    for sigs in SIGNIFICATIONS.values():
        for sig in sigs:
            yield sig.source
    for registry in (DECANATE_CAUSES, PLANET_IN_11TH_GAINS, SECOND_LORD_HOUSE_GAINS,
                     KARAKA_IN_12_INVERSIONS, CONFINEMENT_MODES, PLANET_ORGANS,
                     PLANET_TRIDOSHAS, PLANET_SEASONS):
        for record in registry.values():
            for cit in getattr(record, "sources", ()):
                yield cit
    # Walled subsystems (post the 2026-08-03 firewall lift) enumerate their anchors so their
    # corpus lines are pinned exactly like the natal registries'.
    from app.raman_saab.electional import CITED_ANCHORS as _ELECTIONAL_ANCHORS
    from app.raman_saab.horary import CITED_ANCHORS as _HORARY_ANCHORS
    yield from _ELECTIONAL_ANCHORS
    yield from _HORARY_ANCHORS
    # The graha-chapter line-range tables (HPA-21/22/24/34) — verbatim-quote anchors.
    from app.raman_saab.doctrine.lookups.graha_chapters import (
        CITED_ANCHORS as _GRAHA_ANCHORS)
    from app.raman_saab.doctrine.medical_astrology import CITED_ANCHORS as _MEDICAL_ANCHORS
    from app.raman_saab.karmic_evolution import CITED_ANCHORS as _KARMIC_ANCHORS
    from app.raman_saab.monographs import CITED_ANCHORS as _MONOGRAPH_ANCHORS
    yield from _GRAHA_ANCHORS
    yield from _MONOGRAPH_ANCHORS
    yield from _KARMIC_ANCHORS
    yield from _MEDICAL_ANCHORS


def cited_files() -> dict[str, Path]:
    """{lock_key -> path} for every distinct file a citation resolves to (key = posix relpath
    under the corpus root)."""
    out: dict[str, Path] = {}
    for cit in iter_citations():
        path = sources._resolve_file(cit.work)
        if path is not None and path.is_file():
            out[path.relative_to(_CORPUS).as_posix()] = path
    return out


def _body_bytes(path: Path) -> bytes:
    """The file with its YAML front matter removed.

    The ETL stamps `scraped_at: <now>` into every chapter's front matter on every import
    (`app/medini/etl/import_archive_text.py`), so a whole-file sha256 changes on every
    re-import even when the text is byte-identical. That made this lock unable to survive an
    import it had no quarrel with, and buried the three files whose CONTENT really had moved
    among twenty-one whose timestamps had.

    Line offsets still matter — citations are line numbers into the whole file, front matter
    included — so `line_count` continues to cover the whole file and catches any shift the
    body hash cannot see.
    """
    raw = path.read_bytes()
    # Both delimiters must be a COMPLETE line. `startswith(b"---")` also matched a file
    # opening on a horizontal rule, and searching for b"\n---" also matched a content line
    # that merely began with three dashes — either way real corpus text fell out of the hash,
    # which is the one thing this function must never do quietly.
    lines = raw.splitlines(keepends=True)
    if not lines or lines[0].rstrip(b"\r\n") != b"---":
        return raw
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip(b"\r\n") == b"---":
            return b"".join(lines[index + 1:])
    return raw


def file_sha256(path: Path) -> str:
    """sha256 of the file's BODY — see `_body_bytes` for why the front matter is excluded."""
    return hashlib.sha256(_body_bytes(path)).hexdigest()


def _line_count(path: Path) -> int:
    with path.open(encoding="utf-8") as fh:
        return sum(1 for _ in fh)


def compute_lock(*, carry_absent: bool = True) -> dict[str, dict]:
    """The lock that SHOULD be on disk for the current citations + corpus.

    Entries for cited files this machine does NOT have are carried forward from the existing
    lock rather than dropped. A lock is a record of every cited file; regenerating it on a box
    that happens to be missing one book would delete that book's record permanently and hand
    the next machine — which does have it — a file with no locked hash to check against. ASP
    is the standing case: a local OCR of a user-supplied scan, unrecoverable by download.
    """
    fresh = {key: {"sha256": file_sha256(p), "line_count": _line_count(p)}
             for key, p in sorted(cited_files().items())}
    if carry_absent:
        for key, entry in load_lock().items():
            fresh.setdefault(key, entry)
    return dict(sorted(fresh.items()))


def load_lock() -> dict[str, dict]:
    if not LOCK_PATH.is_file():
        return {}
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def write_lock() -> dict[str, dict]:
    """Regenerate SOURCE_LOCK.json (deliberate, human-gated by UPDATE_SOURCE_LOCK=1 in the test)."""
    lock = compute_lock()
    LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return lock
