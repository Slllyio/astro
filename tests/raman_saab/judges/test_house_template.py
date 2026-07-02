"""Per-signification house judge (NEW engine) — `judges/house_template.py`.

TDD spec for the 3-frame ledger + corrected `_decide` (veto / contradiction /
Track-B fallback / karaka-salvage / navamsa-modulation) and the per-signification
routing that the legacy house-level judge does not do.

Astronomical-fact docstrings on each test state the doctrine being verified.
The legacy `house_judge` is left untouched; `test_as_house_verdict_compatible`
proves the new proforma can stand in for it (same lord/karaka, ordinal verdict).
"""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges import house_judge as legacy
from app.raman_saab.judges import house_template as ht
from app.raman_saab.judges import rule_firing as rf
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.significations import Signification
from app.raman_saab.doctrine.sources import Citation

#: Minimal significations for the _decisive_affliction signification-scoping tests.
_SIBLINGS_SIG = Signification(key="siblings", house=3, primary_karaka="Mars",
                              rule_tags=("siblings",), source=Citation("HTJAH-I", 3351))
_SELF_SIG = Signification(key="self", house=1, primary_karaka="Sun",
                          rule_tags=("self",), source=Citation("HTJAH-I", 1))


# ---------------------------------------------------------------------------
# Helpers: build FiredRule / FrameLedger instances directly for _decide units.
# ---------------------------------------------------------------------------

def _fired(polarity: str, rule_id: str | None = None,
           signification: str = "self") -> rf.FiredRule:
    """A synthetic FiredRule carrying the polarity `_decide` reads, with an optional
    explicit rule id + signification (for the decisive-affliction-rule tests)."""
    rule = RuleRecord(
        id=rule_id or f"TEST.{polarity}",
        house=1,
        signification=signification,
        group="combination",
        kind="evaluable",
        condition=None,
        fortified="ok",
        afflicted="bad",
        frame="LAGNA",
        varga="D1",
        polarity=polarity,
        source=Citation("HTJAH-I", 1),
    )
    return rf.FiredRule(rule=rule, branch="fortified", text="ok")


def _ledger(
    *,
    frame: str = "lagna",
    lord: str = "Mars",
    lord_strong=True,
    karaka: str = "Sun",
    karaka_strong=True,
    bhava_bala=None,
    bhava_bala_strong=None,
    navamsa_status: str = "neutral",
    karaka_intact: bool = True,
    maraka_active: bool = False,
    parivartana_resilient: bool = False,
    lord_karaka_identical: bool = False,
    fired_benefic=(),
    fired_malefic=(),
    fired_neutral=(),
    flags=(),
    lord_effective=None,
    karaka_effective=None,
    dominant_factor=None,
    dominant_severe: bool = False,
) -> ht.FrameLedger:
    return ht.FrameLedger(
        frame=frame, lord=lord, lord_strong=lord_strong, karaka=karaka,
        karaka_strong=karaka_strong, bhava_bala=bhava_bala,
        bhava_bala_strong=bhava_bala_strong, navamsa_status=navamsa_status,
        karaka_intact=karaka_intact, maraka_active=maraka_active,
        parivartana_resilient=parivartana_resilient,
        lord_karaka_identical=lord_karaka_identical,
        fired_benefic=tuple(fired_benefic), fired_malefic=tuple(fired_malefic),
        fired_neutral=tuple(fired_neutral), flags=tuple(flags),
        lord_effective=lord_effective, karaka_effective=karaka_effective,
        dominant_factor=dominant_factor, dominant_severe=dominant_severe)


def _track_b(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


# ---------------------------------------------------------------------------
# 1. _decide unit tests — every branch + veto + salvage + navamsa shift.
# ---------------------------------------------------------------------------

class TestDecide:
    """The §6.3 ordinal decision rule; order is load-bearing."""

    def test_karaka_veto_yields_afflicted(self):
        """A non-intact karaka (combust+debilitated+maraka) vetoes to afflicted regardless of evidence."""
        v, shifted = ht._decide(_ledger(karaka_intact=False, fired_benefic=(_fired("benefic"),)))
        assert v == "afflicted" and shifted is False

    def test_contradiction_yields_mixed(self):
        """Benefic AND malefic both firing on a BALANCED ledger (1 strong pillar, 1
        weak — no pillar preponderance) shows contradiction -> mixed (never hidden)."""
        v, _ = ht._decide(_ledger(lord_strong=True, karaka_strong=False,
                                  fired_benefic=(_fired("benefic"),),
                                  fired_malefic=(_fired("malefic"),)))
        assert v == "mixed"

    def test_contradiction_two_strong_pillars_favourable(self):
        """Stage-3 'V2' preponderance: a contradiction with 2 strong pillars and a
        non-weakening navamsa lifts to favourable (CONTRA_PILLAR_FAVOUR=2)."""
        v, _ = ht._decide(_ledger(lord_strong=True, karaka_strong=True,
                                  fired_benefic=(_fired("benefic"),),
                                  fired_malefic=(_fired("malefic"),)))
        assert v == "favourable"

    def test_contradiction_navamsa_weakens_afflicted(self):
        """Stage-3 'V2' navamsa guard: the same 2-strong-pillar contradiction with a
        WEAKENING navamsa is held back from favourable, falls to mixed, and is then
        dropped to afflicted by the navamsa modulation."""
        v, _ = ht._decide(_ledger(lord_strong=True, karaka_strong=True,
                                  fired_benefic=(_fired("benefic"),),
                                  fired_malefic=(_fired("malefic"),),
                                  navamsa_status="weakens"))
        assert v == "afflicted"

    def test_affliction_matter_lone_malefic_afflicted(self):
        """Stage-3 'B' dusthana-affliction (clause 1.5): an AFFLICTION_MATTER ledger
        (6th/12th malefic signification) with a lone malefic and NO benefic reads
        'afflicted' even when ALL pillars are strong — a strong dusthana lord strengthens
        the evil, never rescues it."""
        v, shifted = ht._decide(_ledger(lord_strong=True, karaka_strong=True,
                                        bhava_bala_strong=True,
                                        fired_malefic=(_fired("malefic"),),
                                        flags=("AFFLICTION_MATTER",)))
        assert v == "afflicted" and shifted is False

    def test_affliction_matter_not_lifted_by_navamsa_confirms(self):
        """The dusthana-affliction verdict is decisive: a confirming navamsa (which would
        lift a borderline mixed to favourable) does NOT touch it."""
        v, shifted = ht._decide(_ledger(lord_strong=True, karaka_strong=True,
                                        bhava_bala_strong=True, navamsa_status="confirms",
                                        fired_malefic=(_fired("malefic"),),
                                        flags=("AFFLICTION_MATTER",)))
        assert v == "afflicted" and shifted is False

    def test_affliction_matter_with_benefic_routes_to_preponderance(self):
        """A BENEFIC contradiction (e.g. a Vipareeta/Harsha yoga or benefic aspect) takes a
        dusthana matter OUT of clause-1.5 and back to the clause-2 preponderance weigh: two
        strong pillars + a non-weakening navamsa -> favourable, not auto-afflicted."""
        v, _ = ht._decide(_ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=False,
                                  fired_benefic=(_fired("benefic"),),
                                  fired_malefic=(_fired("malefic"),),
                                  flags=("AFFLICTION_MATTER",)))
        assert v == "favourable"

    def test_affliction_matter_deferred_under_longevity_guard(self):
        """The Phase-E longevity guard wins: an AFFLICTION_MATTER that is ALSO longevity-
        guarded does not fire clause-1.5 (death/span is owned by the longevity pre-pass)."""
        v, _ = ht._decide(_ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=True,
                                  fired_malefic=(_fired("malefic"),),
                                  flags=("AFFLICTION_MATTER", "LONGEVITY_GUARD")))
        assert v != "afflicted"

    def test_decisive_affliction_rule_drives_afflicted(self):
        """Stage-3 _decisive_affliction: a fired MALEFIC rule whose id is in
        _DECISIVE_AFFLICTION_RULE_IDS and whose signification matches the matter confirms
        afflicted even from a decisive favourable (chart_58/62: multiply-afflicted karaka)."""
        decisive_id = next(iter(ht._DECISIVE_AFFLICTION_RULE_IDS))
        dec = _fired("malefic", decisive_id, signification="siblings")
        L = _ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=True,
                    fired_malefic=(dec,))
        v, shifted = ht._decisive_affliction("favourable", L, _SIBLINGS_SIG)
        assert v == "afflicted" and shifted is True

    def test_decisive_affliction_signification_scoped(self):
        """No cross-signification leak: a siblings-decisive rule does NOT afflict a 'self'
        matter even when it sits in the (empty-rule_tags) ledger's malefic bucket."""
        decisive_id = next(iter(ht._DECISIVE_AFFLICTION_RULE_IDS))
        dec = _fired("malefic", decisive_id, signification="siblings")
        v, shifted = ht._decisive_affliction("favourable", _ledger(fired_malefic=(dec,)),
                                             _SELF_SIG)
        assert v == "favourable" and shifted is False

    def test_decisive_affliction_deferred_under_longevity_guard(self):
        """The longevity guard defers a decisive-affliction rule too (Phase E owns death)."""
        decisive_id = next(iter(ht._DECISIVE_AFFLICTION_RULE_IDS))
        dec = _fired("malefic", decisive_id, signification="siblings")
        L = _ledger(fired_malefic=(dec,), flags=("LONGEVITY_GUARD",))
        v, shifted = ht._decisive_affliction("favourable", L, _SIBLINGS_SIG)
        assert v == "favourable" and shifted is False

    def test_track_b_fallback_malefic_afflicted(self):
        """No Shadbala (lord_strong None) + a malefic rule -> afflicted by polarity alone."""
        v, _ = ht._decide(_ledger(lord_strong=None, karaka_strong=None, fired_malefic=(_fired("malefic"),)))
        assert v == "afflicted"

    def test_track_b_fallback_benefic_favourable(self):
        """No Shadbala + a lone benefic rule -> favourable by polarity alone."""
        v, _ = ht._decide(_ledger(lord_strong=None, karaka_strong=None, fired_benefic=(_fired("benefic"),)))
        assert v == "favourable"

    def test_track_b_fallback_no_evidence_insufficient(self):
        """No Shadbala and no fired rules -> insufficient-evidence."""
        v, _ = ht._decide(_ledger(lord_strong=None, karaka_strong=None))
        assert v == "insufficient-evidence"

    def test_both_strong_no_malefic_favourable(self):
        """Strong lord + strong karaka + ok bhava + no malefic -> favourable."""
        v, _ = ht._decide(_ledger(lord_strong=True, karaka_strong=True, fired_benefic=(_fired("benefic"),)))
        assert v == "favourable"

    def test_weak_pillar_with_malefic_afflicted(self):
        """A weak pillar plus a malefic rule -> afflicted (both lord+karaka weak so salvage cannot apply)."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=False, fired_malefic=(_fired("malefic"),)))
        assert v == "afflicted"

    def test_karaka_salvage_weak_lord_strong_karaka_lone_malefic_mixed(self):
        """A decisively strong karaka rescues a weak-lord lone-malefic afflicted -> mixed (HTJAH-I:503-505)."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=True, fired_malefic=(_fired("malefic"),)))
        assert v == "mixed"

    def test_no_evidence_at_all_insufficient(self):
        """Shadbala known but no fired rules of any polarity -> insufficient-evidence."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=True))
        assert v == "insufficient-evidence"

    def test_borderline_mixed_when_neutral_only(self):
        """A weak pillar with only neutral evidence (no malefic) lands mixed, not afflicted."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=True, fired_neutral=(_fired("neutral"),)))
        assert v == "mixed"

    def test_navamsa_confirms_promotes_mixed_to_favourable(self):
        """D9 confirmation lifts a borderline mixed to favourable (navamsa modulation)."""
        v, shifted = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                        fired_neutral=(_fired("neutral"),), navamsa_status="confirms"))
        assert v == "favourable" and shifted is True

    def test_navamsa_weakens_demotes_mixed_to_afflicted(self):
        """D9 weakening drops a borderline mixed to afflicted — but only when MALEFIC
        testimony exists to confirm (WP1 testimony gate): the D9 is a confirmation
        varga, it cannot manufacture an affliction from non-malefic rasi testimony."""
        v, shifted = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                        fired_neutral=(_fired("neutral"),),
                                        fired_malefic=(_fired("malefic"),),
                                        fired_benefic=(_fired("benefic"),),
                                        navamsa_status="weakens"))
        assert v == "afflicted" and shifted is True

    def test_navamsa_weakens_needs_malefic_testimony(self):
        """WP1: nav 'weakens' + purely neutral/benefic rasi testimony -> the borderline
        stays mixed (a qualified promise, not a denial)."""
        v, shifted = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                        fired_neutral=(_fired("neutral"),),
                                        navamsa_status="weakens"))
        assert v == "mixed" and shifted is False

    def test_severe_dominant_lord_denies_in_contradiction(self):
        """WP1 comparative override (HTJAH-I:3788): a combust/uncancelled-debilitated
        DOMINANT lord denies the matter in a contradiction, despite strong pillars."""
        v, shifted = ht._decide(_ledger(
            lord_strong=True, karaka_strong=True, bhava_bala_strong=True,
            fired_benefic=(_fired("benefic"),), fired_malefic=(_fired("malefic"),),
            dominant_factor="lord", dominant_severe=True))
        assert v == "afflicted" and shifted is False

    def test_severe_dominant_karaka_does_not_deny(self):
        """WP1: the severe-denial is LORD-scoped — a severe dominant KARAKA with a
        standing lord is chart_54's 'good lord rescues' (HTJAH-I:503-505)."""
        v, _ = ht._decide(_ledger(
            lord_strong=True, karaka_strong=True, bhava_bala_strong=True,
            fired_benefic=(_fired("benefic"),), fired_malefic=(_fired("malefic"),),
            dominant_factor="karaka", dominant_severe=True))
        assert v == "favourable"

    def test_severe_dominant_lord_spared_in_dusthana_house(self):
        """WP1: in a 6/8/12 house a broken lord can LIGHTEN the evil (inversion
        direction) — the severe-denial must not fire there."""
        v, _ = ht._decide(_ledger(
            lord_strong=True, karaka_strong=True, bhava_bala_strong=True,
            fired_benefic=(_fired("benefic"),), fired_malefic=(_fired("malefic"),),
            dominant_factor="lord", dominant_severe=True, flags=("DUSTHANA_HOUSE",)))
        assert v == "favourable"

    def test_decisive_favourable_never_shifts(self):
        """A decisive favourable is never modulated by D9 (modulation only touches mixed)."""
        v, shifted = ht._decide(_ledger(lord_strong=True, karaka_strong=True,
                                        fired_benefic=(_fired("benefic"),), navamsa_status="weakens"))
        assert v == "favourable" and shifted is False

    def test_decisive_afflicted_never_shifts(self):
        """A decisive afflicted is never modulated by D9 even when D9 confirms."""
        v, shifted = ht._decide(_ledger(lord_strong=False, karaka_strong=False,
                                        fired_malefic=(_fired("malefic"),), navamsa_status="confirms"))
        assert v == "afflicted" and shifted is False


# ---------------------------------------------------------------------------
# 2. Per-signification routing on a real chart.
# ---------------------------------------------------------------------------

def test_per_signification_h4_multiple_verdicts():
    """H4 splits into several sub-matters (mother/happiness/education/...) each judged
    through its own karaka (Moon/Jupiter/...), each carrying an ordinal verdict."""
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    proforma = ht.judge_house(chart, 4)
    assert len(proforma.significations) >= 3              # mother, happiness, education, ...
    keys = {sv.signification for sv in proforma.significations}
    assert "mother" in keys
    for sv in proforma.significations:
        assert sv.verdict in ("favourable", "mixed", "afflicted", "insufficient-evidence")
        assert sv.lead_frame in ("lagna", "moon", "karaka")
        assert sv.house == 4
    # the mother sub-matter is routed through the Moon karaka
    mother = next(sv for sv in proforma.significations if sv.signification == "mother")
    assert mother.karaka == "Moon"


def test_all_houses_each_have_significations():
    """Every house yields at least one SignificationVerdict and a house-level rollup."""
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    proformas = ht.judge_all_houses(chart)
    assert len(proformas) == 12
    for pf in proformas:
        assert pf.significations
        assert pf.rollup in ("favourable", "mixed", "afflicted", "insufficient-evidence")


# ---------------------------------------------------------------------------
# 3. lord == karaka identity flag (must not double-penalise).
# ---------------------------------------------------------------------------

def test_lord_karaka_identity_flag():
    """When the bhava lord IS the karaka (e.g. Leo lagna -> H1 lord Sun == karaka Sun)
    the LORD_KARAKA_IDENTITY flag is set so one affliction is not counted twice."""
    # Leo ascendant (hour 7): H1 LAGNA-frame lord = Sun, H1 karaka = Sun -> identity.
    chart = cast_chart(BirthData("Leo", 1990, 8, 10, 7, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    assert chart.asc_sign == 5                        # Leo rising (pin)
    sv = ht.judge_house(chart, 1).significations[0]
    # the LAGNA frame is the lead or an alternate; locate it.
    ledger = next(L for L in (sv.ledger,) + sv.alt_ledgers if L.frame == "lagna")
    assert ledger.lord == ledger.karaka == "Sun"
    assert ledger.lord_karaka_identical is True
    assert "LORD_KARAKA_IDENTITY" in ledger.flags
    # collapsed pillar: the two strengths agree (one value drives both)
    assert ledger.lord_strong == ledger.karaka_strong


def test_lord_karaka_identity_unit():
    """Directly: a collapsed-identity ledger reports the flag and equal pillar strengths."""
    # Build via the public ledger builder on a chart where H1 lord == karaka (Leo lagna).
    chart = cast_chart(BirthData("Leo", 1990, 8, 10, 7, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    from app.raman_saab.doctrine.significations import significations_of
    sig = significations_of(1)[0]
    ledger = ht._build_frame_ledger(chart, sig, "lagna")
    assert ledger.lord == ledger.karaka == "Sun"
    assert ledger.lord_karaka_identical and ledger.lord_strong == ledger.karaka_strong


# ---------------------------------------------------------------------------
# 4. Legacy compatibility — as_house_verdict() stands in for house_judge.
# ---------------------------------------------------------------------------

def test_as_house_verdict_compatible():
    """The new proforma's as_house_verdict() yields a legacy-shaped HouseVerdict with
    the same lord/karaka as the legacy judge and an ordinal verdict."""
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    for h in range(1, 13):
        new_hv = ht.judge_house(chart, h).as_house_verdict()
        old_hv = legacy.judge_house(chart, h)
        assert isinstance(new_hv, legacy.HouseVerdict)
        assert new_hv.house == old_hv.house == h
        assert new_hv.lord == old_hv.lord            # same bhava lord
        assert new_hv.karaka == old_hv.karaka        # same primary karaka
        assert new_hv.verdict in ("favourable", "mixed", "afflicted", "insufficient-evidence")
        # fired-rule evidence is preserved as tuples
        assert isinstance(new_hv.benefic, tuple)
        assert isinstance(new_hv.malefic, tuple)
        assert isinstance(new_hv.neutral, tuple)


def test_as_house_verdict_unions_all_signification_rules():
    """The house-level HouseVerdict unions the fired rules across every signification."""
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    proforma = ht.judge_house(chart, 7)
    hv = proforma.as_house_verdict()
    union = set(hv.benefic) | set(hv.malefic) | set(hv.neutral)
    # the union must contain every fired rule appearing in any signification ledger
    for sv in proforma.significations:
        for fr in sv.ledger.fired_benefic + sv.ledger.fired_malefic + sv.ledger.fired_neutral:
            assert fr in union


# ---------------------------------------------------------------------------
# 5. Track-B — stated-positions chart decides on polarity fallback.
# ---------------------------------------------------------------------------

def test_track_b_decides_on_polarity():
    """A from_stated_positions chart has no Shadbala; every ledger pillar is None and
    the verdict is driven by rule polarity (the Track-B fallback)."""
    # Aries lagna, Saturn (malefic) in the 8th -> H8 malefic fires; strengths None.
    chart = _track_b({"Saturn": 220.0})
    proforma = ht.judge_house(chart, 8)
    assert proforma.significations
    for sv in proforma.significations:
        assert sv.ledger.lord_strong is None
        assert sv.ledger.karaka_strong is None
        assert sv.ledger.bhava_bala is None
        assert sv.verdict in ("favourable", "mixed", "afflicted", "insufficient-evidence")


def test_track_b_lead_frame_is_lagna():
    """With no Shadbala the lead frame cannot be chosen by lord strength -> defaults to lagna."""
    chart = _track_b({"Saturn": 220.0})
    proforma = ht.judge_house(chart, 8)
    for sv in proforma.significations:
        assert sv.lead_frame == "lagna"


# ---------------------------------------------------------------------------
# 6. Longevity guard — death/longevity verdicts deferred to the Phase-E engine.
#    methodology §1 (lines 39-42): longevity is a pre-pass that gates all house
#    judgment, so this judge must NOT emit a death/afflicted verdict for a
#    longevity/death matter while the span class is unfixed.
# ---------------------------------------------------------------------------

class TestLongevityGuard:
    """LONGEVITY_GUARD makes the guard load-bearing in `_decide` (was cosmetic)."""

    def test_guarded_maraka_track_b_yields_insufficient_not_afflicted(self):
        """A guarded death matter on Track-B with an active maraka must NOT read
        'afflicted' — the death call belongs to the Phase-E longevity engine."""
        v, _ = ht._decide(_ledger(lord_strong=None, karaka_strong=None,
                                  maraka_active=True, flags=("LONGEVITY_GUARD",)))
        assert v == "insufficient-evidence"

    def test_unguarded_maraka_track_b_still_afflicted(self):
        """Without the guard (a non-longevity matter) an active maraka still drives
        afflicted on Track-B — the suppression is scoped to longevity/death only."""
        v, _ = ht._decide(_ledger(lord_strong=None, karaka_strong=None,
                                  maraka_active=True))
        assert v == "afflicted"

    def test_guarded_maraka_both_pillars_yields_insufficient(self):
        """Both pillars known: a weak-lord guarded matter with maraka pressure is
        clamped to insufficient-evidence instead of afflicted."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                  maraka_active=True, flags=("LONGEVITY_GUARD",)))
        assert v == "insufficient-evidence"

    def test_guarded_broken_karaka_veto_clamped(self):
        """The karaka VETO (non-intact karaka) is clamped to insufficient-evidence
        under the guard rather than hard-driving the death verdict to afflicted."""
        v, _ = ht._decide(_ledger(karaka_intact=False, flags=("LONGEVITY_GUARD",)))
        assert v == "insufficient-evidence"

    def test_guarded_weak_pillar_malefic_clamped(self):
        """A weak-pillar lone-malefic guarded matter is clamped to insufficient-evidence
        (the afflicted clause-6 verdict is deferred to the longevity engine)."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=False,
                                  fired_malefic=(_fired("malefic"),),
                                  flags=("LONGEVITY_GUARD",)))
        assert v == "insufficient-evidence"

    def test_guarded_navamsa_weakens_does_not_resurrect_afflicted(self):
        """Even a D9-weakening of a guarded borderline must not surface afflicted."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                  fired_neutral=(_fired("neutral"),),
                                  navamsa_status="weakens",
                                  flags=("LONGEVITY_GUARD",)))
        assert v != "afflicted"

    def test_h8_longevity_significations_are_guarded_on_real_chart(self):
        """H8 longevity/death significations set LONGEVITY_GUARD and never read afflicted
        on the canonical chart (the longevity engine owns that call)."""
        chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
        proforma = ht.judge_house(chart, 8)
        guarded = [sv for sv in proforma.significations
                   if "LONGEVITY_GUARD" in sv.ledger.flags]
        assert guarded, "H8 longevity/death significations should carry LONGEVITY_GUARD"
        for sv in guarded:
            assert sv.verdict != "afflicted"


# ---------------------------------------------------------------------------
# 7. HTJAH-I:503-505 bhava-rescue vs three-pillar karaka-salvage (distinct clauses).
# ---------------------------------------------------------------------------

class TestBhavaAndKarakaRescue:
    """The two demotion clauses cite DIFFERENT Raman doctrine and fire on DIFFERENT
    evidence — the bhava itself (good aspects) vs the karaka's strength."""

    def test_bhava_rescue_strong_bhava_benefic_demotes_afflicted(self):
        """HTJAH-I:503-505 — a weak lord but a strong bhava with good benefic aspects
        ('the house itself has good conjunctions and aspects') -> do not predict evil:
        afflicted demoted to mixed by the BHAVA, not the karaka."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=False,
                                  bhava_bala_strong=True,
                                  fired_benefic=(_fired("benefic"),)))
        assert v == "mixed"

    def test_bhava_rescue_requires_strong_bhava(self):
        """Without a strong Bhava Bala the :503 rescue does not apply: a weak-bhava
        weak-pillar matter stays afflicted."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=False,
                                  bhava_bala_strong=False,
                                  fired_benefic=(_fired("benefic"),)))
        assert v == "afflicted"

    def test_karaka_salvage_still_demotes_lone_malefic(self):
        """The three-pillar karaka-salvage (HTJAH-II:221 / HTJAH-I:985) still demotes a
        weak-lord strong-karaka lone-malefic matter -> mixed (no benefic present)."""
        v, _ = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                  fired_malefic=(_fired("malefic"),)))
        assert v == "mixed"


# ---------------------------------------------------------------------------
# 8. as_house_verdict lord/lord_strong consistency (lagna-frame, not lead-frame).
# ---------------------------------------------------------------------------

def test_as_house_verdict_lord_strong_matches_lagna_lord():
    """`lord` (the LAGNA bhava-lord) and `lord_strong` must describe the SAME planet.
    When the lead signification's lead ledger is the MOON frame (different lord), the
    strength readout must still be taken from the LAGNA-frame ledger."""
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    from app.raman_saab.judges.house_judge import _strong as legacy_strong
    for h in range(1, 13):
        pf = ht.judge_house(chart, h)
        hv = pf.as_house_verdict()
        # the reported lord_strength is exactly the lagna lord's own strength
        assert hv.lord_strong == legacy_strong(hv.lord, chart)
