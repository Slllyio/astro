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
from app.raman_saab.doctrine.sources import Citation


# ---------------------------------------------------------------------------
# Helpers: build FiredRule / FrameLedger instances directly for _decide units.
# ---------------------------------------------------------------------------

def _fired(polarity: str) -> rf.FiredRule:
    """A synthetic FiredRule carrying only the polarity `_decide` reads."""
    rule = RuleRecord(
        id=f"TEST.{polarity}",
        house=1,
        signification="self",
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
) -> ht.FrameLedger:
    return ht.FrameLedger(
        frame=frame, lord=lord, lord_strong=lord_strong, karaka=karaka,
        karaka_strong=karaka_strong, bhava_bala=bhava_bala,
        bhava_bala_strong=bhava_bala_strong, navamsa_status=navamsa_status,
        karaka_intact=karaka_intact, maraka_active=maraka_active,
        parivartana_resilient=parivartana_resilient,
        lord_karaka_identical=lord_karaka_identical,
        fired_benefic=tuple(fired_benefic), fired_malefic=tuple(fired_malefic),
        fired_neutral=tuple(fired_neutral), flags=tuple(flags))


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
        """Benefic AND malefic rules both firing show contradiction -> mixed (never hidden)."""
        v, _ = ht._decide(_ledger(fired_benefic=(_fired("benefic"),), fired_malefic=(_fired("malefic"),)))
        assert v == "mixed"

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
        """D9 weakening drops a borderline mixed to afflicted (navamsa modulation)."""
        v, shifted = ht._decide(_ledger(lord_strong=False, karaka_strong=True,
                                        fired_neutral=(_fired("neutral"),), navamsa_status="weakens"))
        assert v == "afflicted" and shifted is True

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
