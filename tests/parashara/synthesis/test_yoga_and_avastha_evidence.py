"""Phase-3 evidence wiring — avasthas, argala, yogas, the 8th's extras, and the honest confidence.

Each test pins one behavior of the new gatherers: house-scoped attachment, family aggregation,
polarity, the double-count guard, and the normalized/disclosing convergence.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.parashara.doctrine.argala import Argala
from app.parashara.doctrine.sources import Citation
from app.parashara.synthesis.convergence import converge
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier
from app.parashara.synthesis.evidence_engine import gather_avastha
from app.parashara.synthesis.yoga_evidence import (
    gather_argala, gather_eighth_extras, gather_yogas)

_C = Citation("BPHS-41", 27)


def _chart(asc_sign: int, signs: dict[str, int], *, moon_waxing: bool = True) -> SimpleNamespace:
    return SimpleNamespace(asc_sign=asc_sign, moon_waxing=moon_waxing,
                           longitudes={p: (s - 1) * 30 + 5.0 for p, s in signs.items()})


def _avastha(**kw) -> SimpleNamespace:
    base = dict(lajjitadi=(), lajjitadi_destroys_house=False,
                deeptadi="Deena", deeptadi_vikala=False, deeptadi_kopa=False)
    base.update(kw)
    return SimpleNamespace(**base)


def _yoga(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, reason="r", source=_C)


class TestAvasthaEvidence:
    def test_lajjitadi_destroys_attaches_to_occupied_house_only(self):
        """Kshudita Saturn in the 5th afflicts the 5th (BPHS-45:165) — and no other house."""
        r = SimpleNamespace(
            chart=_chart(1, {"Saturn": 5}),
            avasthas={"Saturn": _avastha(lajjitadi=("Kshudita",), lajjitadi_destroys_house=True)})
        hit = gather_avastha(r, 5)
        assert any(e.condition == "lajjitadi_destroys" and e.polarity is Polarity.CONTRADICTS
                   and e.source.line == 165 for e in hit)
        assert not any(e.condition == "lajjitadi_destroys" for e in gather_avastha(r, 6))

    def test_deeptadi_polarity(self):
        """A Deepta occupant supports its house; a Khala occupant weakens it (BPHS-45:113)."""
        r = SimpleNamespace(
            chart=_chart(1, {"Jupiter": 4, "Mars": 7}),
            avasthas={"Jupiter": _avastha(deeptadi="Deepta"), "Mars": _avastha(deeptadi="Khala")})
        assert any(e.polarity is Polarity.SUPPORTS and "Deepta" in e.rule
                   for e in gather_avastha(r, 4))
        assert any(e.polarity is Polarity.CONTRADICTS and "Khala" in e.rule
                   for e in gather_avastha(r, 7))


class TestArgalaEvidence:
    def _reading(self, argalas, signs=None):
        return SimpleNamespace(chart=_chart(1, signs or {"Jupiter": 2}),
                               argala={4: tuple(argalas)})

    def test_prevailing_benefic_argala_supports_with_magnitude(self):
        """An unobstructed benefic intervention supports, worded by Parashara's 1/2/3+ scale."""
        a = Argala(argala_house=2, argala_planets=("Jupiter",), obstructor_house=12,
                   obstructor_planets=(), prevails=True)
        ev = gather_argala(self._reading([a]), 4)
        hit = [e for e in ev if e.condition == "argala_prevails"]
        assert len(hit) == 1 and hit[0].polarity is Polarity.SUPPORTS
        assert "limited" in hit[0].rule            # one planet -> limited (BPHS-31:79)

    def test_prevailing_malefic_argala_contradicts(self):
        """Argala amplifies what the planet signifies — a malefic majority votes against."""
        a = Argala(argala_house=11, argala_planets=("Saturn", "Mars"), obstructor_house=3,
                   obstructor_planets=(), prevails=True)
        ev = gather_argala(self._reading([a], signs={"Saturn": 2, "Mars": 2}), 4)
        hit = [e for e in ev if e.condition == "argala_prevails"]
        assert len(hit) == 1 and hit[0].polarity is Polarity.CONTRADICTS
        assert "medium" in hit[0].rule             # two planets -> medium

    def test_obstructed_argala_is_disclosed_neutral(self):
        """A duly obstructed argala 'goes astray' — one NEUTRAL disclosure, no vote."""
        a = Argala(argala_house=2, argala_planets=("Jupiter",), obstructor_house=12,
                   obstructor_planets=("Saturn",), prevails=False)
        ev = gather_argala(self._reading([a], signs={"Jupiter": 2, "Saturn": 12}), 4)
        hit = [e for e in ev if e.condition == "argala_obstructed"]
        assert len(hit) == 1 and hit[0].polarity is Polarity.NEUTRAL and hit[0].source.line == 82


class TestYogaEvidence:
    def _reading(self, **kw):
        base = dict(mahapurusha=(), dhana_yogas=(), daridra_yogas=(), royal_yogas=(),
                    chandra_yogas=(), special_yogas=())
        base.update(kw)
        return SimpleNamespace(**base)

    def test_dhana_and_daridra_aggregate_one_atom_each_on_wealth_houses(self):
        """All fired ch.41 yogas are ONE supporting atom (and ch.42 one contradicting) on 2 and 11."""
        r = self._reading(dhana_yogas=(_yoga("A"), _yoga("B")), daridra_yogas=(_yoga("P"),))
        for house in (2, 11):
            ev = gather_yogas(r, house)
            assert sum(1 for e in ev if e.condition == "dhana_yogas") == 1
            assert sum(1 for e in ev if e.condition == "daridra_yogas") == 1
            dh = next(e for e in ev if e.condition == "dhana_yogas")
            assert dh.polarity is Polarity.SUPPORTS and "A, B" == dh.observed

    def test_wealth_yogas_do_not_leak_to_other_houses(self):
        """The 2/11 mapping is exact — the 5th hears nothing from ch.41/42."""
        r = self._reading(dhana_yogas=(_yoga("A"),), daridra_yogas=(_yoga("P"),))
        assert gather_yogas(r, 5) == []

    def test_kemadruma_contradicts_the_first_house_only(self):
        """The lunar negative lands on the self (house 1) and nowhere else."""
        r = self._reading(chandra_yogas=(_yoga("Kemadruma"),))
        ev1 = gather_yogas(r, 1)
        assert any(e.condition == "kemadruma" and e.polarity is Polarity.CONTRADICTS for e in ev1)
        assert gather_yogas(r, 4) == []

    def test_mahapurusha_attaches_to_its_own_kendra(self):
        """A Mahapurusha yoga supports the kendra it occupies, not the others."""
        y = SimpleNamespace(name="Sasa", planet="Saturn", dignity="own", house=10, source=_C)
        r = self._reading(mahapurusha=(y,))
        assert any(e.condition == "mahapurusha" for e in gather_yogas(r, 10))
        assert not any(e.condition == "mahapurusha" for e in gather_yogas(r, 7))


class TestEighthExtras:
    def _reading(self, signs, marakas):
        return SimpleNamespace(
            chart=_chart(1, signs),
            maraka_planets=tuple(SimpleNamespace(planet=p, reason="maraka lord",
                                                 source=Citation("BPHS-44", 51))
                                 for p in marakas),
            nisargayu_full=SimpleNamespace(total_years=72.4, planetary_years=60.0,
                                           ascendant_years=12.4))

    def test_benefic_maraka_touching_eighth_votes(self):
        """A non-malefic maraka (Venus) aspecting the 8th is cited affliction (BPHS-44:51)."""
        # Aries lagna: Venus in Taurus (2) casts its 7th-aspect on Scorpio (8) = the 8th house.
        r = self._reading({"Venus": 2}, ["Venus"])
        ev = gather_eighth_extras(r)
        assert any(e.condition == "maraka_touch" and "Venus" in e.observed for e in ev)

    def test_malefic_maraka_guarded_against_double_count(self):
        """A maraka already voting as a functioning malefic casts NO second maraka atom."""
        r = self._reading({"Saturn": 2}, ["Saturn"])         # Saturn aspects the 8th (7th-aspect)
        ev = gather_eighth_extras(r)
        assert not any(e.condition == "maraka_touch" for e in ev)

    def test_span_disclosed_neutral(self):
        """The Nisargayu span is always disclosed beside the 8th, as a no-vote note."""
        ev = gather_eighth_extras(self._reading({}, []))
        span = [e for e in ev if e.condition == "nisargayu_span"]
        assert len(span) == 1 and span[0].polarity is Polarity.NEUTRAL
        assert "72.4" in span[0].observed


class TestNormalizedConfidence:
    def _ev(self, tier, pol):
        return Evidence(topic=1, tier=tier, category="x", polarity=pol, rule="r", condition="c",
                        observed="o", source=_C)

    def test_contested_volume_cannot_reach_the_top_tiers(self):
        """net=5 but agreement fraction 0.45 — normalization holds it to moderate."""
        sup = [self._ev(Tier.PROMISE, Polarity.SUPPORTS), self._ev(Tier.STRENGTH, Polarity.SUPPORTS),
               self._ev(Tier.CORROBORATION, Polarity.SUPPORTS),
               self._ev(Tier.CORROBORATION, Polarity.SUPPORTS),
               self._ev(Tier.CORROBORATION, Polarity.SUPPORTS)]
        con = [self._ev(Tier.STRENGTH, Polarity.CONTRADICTS),
               self._ev(Tier.CORROBORATION, Polarity.CONTRADICTS)]
        c = converge(sup + con, toward=1)
        assert c.net == 5 and c.tier == "moderate"

    def test_clean_convergence_still_grades_par_excellence(self):
        """All three deciding tiers agreeing, uncontested -> the top tier."""
        c = converge([self._ev(Tier.PROMISE, Polarity.SUPPORTS),
                      self._ev(Tier.STRENGTH, Polarity.SUPPORTS),
                      self._ev(Tier.CORROBORATION, Polarity.SUPPORTS)], toward=1)
        assert c.tier == "par-excellence"

    def test_split_note_fires_when_majority_disagrees(self):
        """Verdict follows the deciding tier; the raw-count disclosure says so."""
        c = converge([self._ev(Tier.PROMISE, Polarity.SUPPORTS),
                      self._ev(Tier.CORROBORATION, Polarity.CONTRADICTS),
                      self._ev(Tier.CORROBORATION, Polarity.CONTRADICTS)], toward=1)
        assert "majority leans the other way" in c.split_note

    def test_split_note_silent_when_majority_agrees(self):
        c = converge([self._ev(Tier.PROMISE, Polarity.SUPPORTS),
                      self._ev(Tier.STRENGTH, Polarity.SUPPORTS)], toward=1)
        assert c.split_note == ""