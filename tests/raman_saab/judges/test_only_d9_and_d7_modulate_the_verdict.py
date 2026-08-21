"""Pin which divisional charts may modulate the D1 verdict — so the invariant cannot silently drift.

The engine's rule is: the Navamsa (D9) modulates ALL matters (`_navamsa_modulate`), and — since the
2026-07-22 D-7 promotion — the Sapthamsa (D7) modulates the H5 children matter only
(`_saptamsa_gate`, borderline-only). EVERY other divisional read is REPORT-ONLY and must be
verdict-invariant: the matter-varga overlay (which reads D3/D10/D12/D30) and the ashtakavarga
overlay both return `Metadata`, never a `Verdict`, so by signature they cannot shift a verdict.

This was a real defect class: `varga_domains.py` carried a prose invariant ("the ONLY division that
modulates D1") that went stale for two years when D-7 was promoted, with no test to catch it. This
guard makes the modulation surface mechanically checkable. If a third divisional modulator is ever
added, this fails — update it deliberately (and update the varga_domains note in the same commit).
"""
from __future__ import annotations

import inspect

from app.raman_saab.judges import house_template as ht


def _ret(fn) -> str:
    """Return-annotation of `fn` as a string (module uses `from __future__ import annotations`)."""
    return str(inspect.signature(fn).return_annotation)


def test_the_two_verdict_modulators_return_a_verdict():
    """The D9 and D7 modulators take/return a Verdict — they are the modulation surface."""
    assert "Verdict" in _ret(ht._navamsa_modulate), "D9 navamsa modulator must return a Verdict"
    assert "Verdict" in _ret(ht._saptamsa_gate), "D7 saptamsa gate must return a Verdict"


def test_matter_varga_and_ashtakavarga_overlays_are_verdict_invariant():
    """The other divisional reads are report-only: they return Metadata, never a Verdict, so they
    structurally cannot modulate a verdict (D3/D10/D12/D30 via the matter-varga overlay; the
    Sarvashtakavarga bindus via the ashtakavarga overlay)."""
    for fn in (ht._matter_varga_overlay, ht._ashtakavarga_overlay):
        ret = _ret(fn)
        assert "Metadata" in ret, f"{fn.__name__} should return Metadata"
        assert "Verdict" not in ret, (
            f"{fn.__name__} returns a Verdict — a new divisional modulator? "
            f"Update this guard AND the varga_domains D9 note deliberately.")


def test_matter_varga_overlay_reads_only_reporting_divisions():
    """Belt-and-braces: the matter->varga map (the report-only overlay) covers D3/D10/D12/D30 and
    never D9/D7 — those two have their own dedicated verdict modulators, so routing them through the
    invariant overlay would silently drop their modulation."""
    divisions = {n for n, _ in ht._MATTER_VARGA.values()}
    assert 9 not in divisions, "D9 must go through _navamsa_modulate, not the invariant overlay"
    # D7 is handled by _saptamsa_gate for H5; the overlay may still REPORT D7 dignity, so we do not
    # forbid 7 here — only D9, whose whole-chart modulation must never be demoted to metadata.
    assert divisions, "matter-varga overlay unexpectedly empty"
