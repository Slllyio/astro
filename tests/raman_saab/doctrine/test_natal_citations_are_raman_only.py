"""The strictly-Raman guarantee, re-expressed as an explicit guard.

Before 2026-08-21 the house engine was kept strictly-Raman for free by the registry firewall:
a non-live tag did not resolve, so `verify()` rejected it and no rule could carry it. Admitting
BPHS/Phaladeepika under the `corroboration` tier SPLIT that: corroboration tags now RESOLVE (so a
varga report can show classical verses click-to-source), which means `verify()` passing no longer
proves a citation is Raman's.

So the guarantee moves here: every citation on the NATAL verdict path must map to a `live` (Raman)
book — `book_registry.is_natal_citable` is True. Corroboration (classical) citations are allowed
ONLY on the report-only varga surface (the Shodasavarga domain table), never in a rule, yoga,
signification, synthesis rule, or event spec that feeds a verdict.

If this fails, a classical source has leaked into the natal engine — the exact thing the Prime
Directive forbids.
"""
from __future__ import annotations

from app.raman_saab.doctrine import book_registry as br


def _natal_sources():
    """Every citation the NATAL verdict path holds — rules, yogas, significations, the raman-band
    synthesis rules, the natal lookup registries, and the rectification event specs. Deliberately
    EXCLUDES the report-only varga domain table (corroboration is allowed there) and the walled
    electional/horary subsystems (their own tests own their scope)."""
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
    from app.raman_saab.rectification.events import EVENT_TAXONOMY

    for rule in ALL_RULES:
        yield ("rule", rule.source)
    for syn in SYNTHESIS_RULES:
        if syn.source is not None:               # only the raman band cites
            yield ("synthesis", syn.source)
    for yoga in YOGAS:
        yield ("yoga", yoga.source)
    for sigs in SIGNIFICATIONS.values():
        for sig in sigs:
            yield ("signification", sig.source)
    for registry in (DECANATE_CAUSES, PLANET_IN_11TH_GAINS, SECOND_LORD_HOUSE_GAINS,
                     KARAKA_IN_12_INVERSIONS, CONFINEMENT_MODES, PLANET_ORGANS,
                     PLANET_TRIDOSHAS, PLANET_SEASONS):
        for record in registry.values():
            for cit in getattr(record, "sources", ()):
                yield ("lookup", cit)
    for spec in EVENT_TAXONOMY.values():
        if getattr(spec, "source", None) is not None:
            yield ("event", spec.source)


def test_no_natal_citation_is_classical_corroboration():
    """Every natal-path citation maps to a `live` Raman book — none to a `corroboration`
    (classical) or out-of-scope tag."""
    leaks = []
    for kind, cit in _natal_sources():
        if not br.is_natal_citable(cit.work):
            entry = br.entry_for(cit.work)
            status = entry.status if entry else "unknown"
            leaks.append(f"{kind} cites {cit.work}:{cit.line} (status={status})")
    assert not leaks, "classical/non-Raman citation on the natal verdict path:\n" + "\n".join(leaks)


def test_corroboration_tag_is_actually_barred_here():
    """Sanity: a corroboration tag really is rejected by the guard predicate (so the test above is
    not vacuous). If BPHS ever became natal-citable this fails."""
    assert br.is_natal_citable("BPHS-7") is False
    assert br.is_natal_citable("PHALA") is False
    assert br.is_natal_citable("HTJAH-I") is True     # a real Raman tag still passes
