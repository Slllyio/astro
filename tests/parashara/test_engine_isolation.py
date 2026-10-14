"""Engine isolation — the wall that makes a multi-stream platform possible.

Each astrology stream is a SEPARATE engine with its own root authority. `raman_saab` answers "what
would Raman say" (Raman wins ties); `parashara` answers "what does Parashara say" (BPHS wins ties).
If one engine could reach into the other's doctrine, the answer would be neither.

Two directions, both required:

1. **raman_saab must not import parashara.** The Raman engine is FINISHED and ratcheted
   (259/293 exact). Nothing in this new work may reach it. This is the direction that protects
   completed, measured work — it is the more important of the two.
2. **parashara must not import raman_saab's doctrine or judging.** Sharing a rule corpus, a
   verdict vocabulary, or a `_decide` clause order would make the BPHS engine "Raman wearing a
   BPHS hat" — the precise failure this architecture exists to prevent.

**Stream-agnostic substrate is explicitly allowed** (and is the point of not duplicating work):
ephemeris arithmetic, varga sign maths, ashtakavarga tables. Those belong to no tradition — they
are astronomy and arithmetic. The allowlist below names exactly what may cross, so an accidental
import of doctrine is caught while a deliberate reuse of maths is not.
"""
from __future__ import annotations

import ast
from pathlib import Path

_APP = Path(__file__).resolve().parents[2] / "app"
_RAMAN = _APP / "raman_saab"
_PARASHARA = _APP / "parashara"

#: Modules from the Raman package that `parashara` MAY use: pure astronomy/arithmetic that encodes
#: no tradition's judgment. Add to this list only after confirming the module carries no doctrine,
#: no verdict vocabulary, and no rule corpus.
#: `from app.raman_saab.chart import varga` records the module as `app.raman_saab.chart`, so the
#: package path is listed alongside the dotted module path. Keeping the package itself on the list
#: is acceptable ONLY because `chart/` is casting arithmetic end to end; never list a package that
#: contains doctrine.
_SUBSTRATE_ALLOWLIST: frozenset[str] = frozenset({
    "app.raman_saab.chart",              # the casting package (arithmetic only, no doctrine)
    "app.raman_saab.chart.varga",        # the 16 division sign-functions: pure arithmetic
    "app.raman_saab.chart.varga_chart",  # casting a varga chart from longitudes
})

#: `app.core` is the older, defunct general engine — itself a (retired) stream. parashara may use
#: only its PURE-ASTRONOMY modules (swisseph position maths), never its doctrine/reading layers.
_CORE_ASTRONOMY_ALLOWLIST: frozenset[str] = frozenset({
    "app.core.ephemeris_engine",         # swisseph positions, ascendant, JD — pure astronomy
    "app.core.nakshatra",                # nakshatra-from-longitude arithmetic
})


def _imports_of(py: Path) -> set[str]:
    """Every module name imported by `py` (both `import x` and `from x import y`)."""
    try:
        tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"), filename=str(py))
    except SyntaxError:                                   # pragma: no cover - not our concern here
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module)
    return out


def _py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def test_raman_saab_never_imports_parashara():
    """Direction 1 — the finished, ratcheted engine must not depend on this new work at all."""
    offenders: list[str] = []
    for py in _py_files(_RAMAN):
        for mod in _imports_of(py):
            if mod.startswith("app.parashara"):
                offenders.append(f"{py.relative_to(_APP)} imports {mod}")
    assert not offenders, (
        "raman_saab imported the parashara engine — the Raman ratchet must stay untouchable "
        "by construction:\n" + "\n".join(offenders))


def test_parashara_never_imports_raman_doctrine_or_judges():
    """Direction 2 — the BPHS engine must not inherit another stream's doctrine or verdicts."""
    offenders: list[str] = []
    for py in _py_files(_PARASHARA):
        for mod in _imports_of(py):
            if not mod.startswith("app.raman_saab"):
                continue
            if mod in _SUBSTRATE_ALLOWLIST:
                continue
            offenders.append(f"{py.relative_to(_APP)} imports {mod}")
    assert not offenders, (
        "parashara imported Raman doctrine/judging. BPHS must be encoded from BPHS, not inherited "
        "from another stream's reading of it. If the import is genuinely stream-agnostic maths, "
        "add it to _SUBSTRATE_ALLOWLIST deliberately:\n" + "\n".join(offenders))


def test_parashara_uses_only_pure_astronomy_from_core():
    """`app.core` is a retired BPHS-ish stream; parashara may borrow its swisseph astronomy but NOT
    its doctrine or reading composers (that would be inheriting another engine's interpretation)."""
    offenders: list[str] = []
    for py in _py_files(_PARASHARA):
        for mod in _imports_of(py):
            if not mod.startswith("app.core"):
                continue
            if mod in _CORE_ASTRONOMY_ALLOWLIST:
                continue
            offenders.append(f"{py.relative_to(_APP)} imports {mod}")
    assert not offenders, (
        "parashara imported a non-astronomy app.core module. Only pure-astronomy substrate is "
        "allowed; anything doctrinal must be encoded from BPHS here:\n" + "\n".join(offenders))


def test_parashara_has_its_own_registry_with_bphs_as_root():
    """The engines' authority models must actually differ — otherwise separating them bought
    nothing. BPHS is root here and NOT citable in the Raman natal engine; Raman's own books are
    corroboration here and root there."""
    from app.parashara.doctrine import book_registry as p_reg
    from app.raman_saab.doctrine import book_registry as r_reg

    # This engine: BPHS is the authority.
    assert p_reg.is_root("BPHS-7") is True
    assert p_reg.is_citable("BPHS-7") is True
    # ...and Raman resolves but cannot be cited as authority here.
    assert p_reg.status_of("HTJAH-I") == p_reg.CORROBORATION
    assert p_reg.is_citable("HTJAH-I") is False

    # The Raman engine: exactly the other way round.
    assert r_reg.is_natal_citable("HTJAH-I") is True
    assert r_reg.is_natal_citable("BPHS-7") is False


def test_exactly_one_root_book():
    """`root` means Parashara's own text. If a second book ever claims root, the engine has lost
    its authority model — two roots cannot both win a tie."""
    from app.parashara.doctrine import book_registry as p_reg
    roots = [b.tag for b in p_reg.BOOKS if b.status == p_reg.ROOT]
    assert roots == ["BPHS"], f"expected exactly one root book (BPHS), got {roots}"


def test_registry_status_values_are_known():
    from app.parashara.doctrine import book_registry as p_reg
    for b in p_reg.BOOKS:
        assert b.status in p_reg._STATUSES, f"{b.tag}: unknown status {b.status}"
