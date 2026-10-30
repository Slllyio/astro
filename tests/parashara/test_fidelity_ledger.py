"""BPHS fidelity ratchet — the parashara engine must reproduce ALL of Parashara's own worked results.

The analog of the Raman golden ratchet, honest about being different in kind: Raman's 259/293 is
verdict accuracy on his published chart-verdict gallery; BPHS gives no gallery, so this scores the
engine's reproduction of the concrete worked RESULTS Parashara printed (Ahargana lords, ashtakavarga
totals + trine reduction, the Vimshottari seed, the Uchcha value, the argala of his hypothetical
chart). It prints the headline the way the Raman ratchet does and FAILS if any worked result stops
reproducing — so a regression cannot pass silently.
"""
from __future__ import annotations

from tools.parashara.fidelity_ledger import ledger, summary


def test_all_worked_results_reproduced(capsys):
    reproduced, total, detail = summary()
    failures = [(name, exp, got) for name, ok, exp, got in detail if not ok]
    # Headline, printed like the Raman ratchet ("[ratchet] exact=259/293").
    with capsys.disabled():
        print(f"\n[bphs-fidelity] reproduced={reproduced}/{total} of Parashara's own worked results")
    assert not failures, "worked results that stopped reproducing:\n" + "\n".join(
        f"  {n}: expected {e!r} got {g!r}" for n, e, g in failures)


def test_ledger_does_not_shrink():
    """The ledger is a floor — a refactor must not quietly drop worked examples."""
    assert len(ledger()) >= 30


def test_every_ledger_citation_resolves():
    from app.parashara.doctrine.sources import verify
    for ex in ledger():
        assert verify(ex.citation), (ex.name, ex.citation)
