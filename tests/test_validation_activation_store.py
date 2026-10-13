"""Phase 3 instrument store: real periods are the engine's own dashas; the placebo shifts the lord sequence."""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.reading import read
from tools.validation.activation_store import process, tier

ROW = dict(person_id="x", birth_date="1990-07-15", birth_time="12:00", tz_offset=5.5,
           latitude=12.97, longitude=77.59)   # canonical Bangalore baseline: Mercury MD at birth


class TestActivationStore:
    def test_real_periods_match_engine_read(self):
        """The stored 'real' (MD, AD, start, end) sequence equals read()'s Vimshottari bhuktis."""
        rec = [r for r in process(ROW) if r[1] == "real"]
        vim = next(d for d in read(cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5,
                                        latitude=12.97, longitude=77.59)).dashas
                   if d.system == "vimshottari")
        eng = [(m, b.lord, round(max(0.0, b.start_year), 6), round(b.end_year, 6))
               for m, bs in vim.bhuktis for b in bs if b.end_year > 0]
        assert [(r[2], r[3], round(r[4], 6), round(r[5], 6)) for r in rec] == eng
        assert rec[0][2] == "Mercury"

    def test_placebo_shifts_to_next_lord(self):
        """Seeding one nakshatra ahead makes the birth MD the next Vimshottari lord (Mercury -> Ketu)."""
        plc = [r for r in process(ROW) if r[1] == "placebo"]
        assert plc[0][2] == "Ketu"

    def test_tier_ordering_follows_raman(self):
        """feeble (MD only) < limited (AD only) < ordinary (both) < par excellence (both + associated)."""
        assert (tier(False, False, True), tier(True, False, False), tier(False, True, False),
                tier(True, True, False), tier(True, True, True)) == (0, 1, 2, 3, 4)


class TestRevisedInstrument:
    def test_moon_house_lord_counts_as_influence(self):
        """Factor (f): the lord of the H-th from the Moon influences H even with no other link."""
        from app.parashara.primitives.relationships import SIGN_LORDS
        from app.parashara.synthesis.chart_facts import planet_signs
        from tools.validation.activation_store import influence
        ch = cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5, latitude=12.97, longitude=77.59)
        signs = planet_signs(ch)
        for h in range(1, 13):
            lord = SIGN_LORDS[(signs["Moon"] - 1 + h - 1) % 12 + 1]
            assert influence(lord, h, ch, signs)

    def test_second_lord_is_primary_maraka(self):
        """The lord of the 2nd from lagna is always a primary maraka."""
        from app.parashara.primitives.relationships import SIGN_LORDS
        from app.parashara.synthesis.chart_facts import house_sign, planet_signs
        from tools.validation.activation_store import primary_maraka
        ch = cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5, latitude=12.97, longitude=77.59)
        assert primary_maraka(SIGN_LORDS[house_sign(ch.asc_sign, 2)], ch, planet_signs(ch))
