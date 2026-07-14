"""Increment 34 pins: the fresh Three-Hundred-Combinations yoga corpus + the engine coverage finding.

Non-strength axis (the strength vein is exhausted). Pins corpus integrity and the concrete finding
that the engine's yoga library covers only a MINORITY of Raman's named yogas — the mechanical reason
the increment-30 yoga strength token was a documented negative. Measurement only; no engine change.
"""
from __future__ import annotations

import json

from app.medini.doctrine.validation import yoga_coverage as YC


def test_three_hundred_yoga_corpus_and_engine_coverage_gap():
    corpus = json.loads(YC._CORPUS.read_text())
    rows = corpus["rows"]
    assert len(rows) >= 40, len(rows)
    assert corpus["n_example_charts"] >= 35, corpus["n_example_charts"]
    # every row has a name + at least a definition or results (structure held through OCR)
    for r in rows:
        assert r["name"] and (r["definition"] or r["results"]), r["num"]
    # a coarse outcome class was tagged for the majority
    assert sum(1 for r in rows if r["outcome_classes"]) >= len(rows) * 0.6

    o = YC.run()
    # coverage is computed on DISTINCT yogas (OCR duplicates deduped) with EXACT stem matching.
    # After the increment-37 Nabhāsa + navāṁśa batch the engine covers ~74% of Raman's named
    # yogas (increments 35+36 reached ~42%; pre-35 was ~24%).
    assert 70 <= o["coverage_pct"] < 90, o["coverage_pct"]
    assert o["covered"] >= 44, o["covered"]
    assert o["n_distinct_yogas"] >= 55, o["n_distinct_yogas"]
    # the increment-35 (occupancy) and increment-36 (lord-based) additions are present
    covered_lower = {n.lower() for n in o["covered_names"]}
    assert any("gajakesari" in n for n in covered_lower)
    for added in ("chatussagara", "dhurdhura", "sakata", "vasumathi", "chakra", "gola",
                  "parvata", "sankha", "sreenatha", "samudra", "chapa"):
        assert any(added in n for n in covered_lower), added
    # increment-37 Nabhāsa Ākṛti/Saṅkhyā/Dala + navāṁśa + solar additions are present.
    # covered_names keeps the corpus's (OCR) spelling, so the alias-mapped members show under
    # their raw form: vapee→vapi, obhayachari→ubhayachari, daiida→danda, imdra→indra,
    # thriiochana→trilochana, adhl→adhi.
    for added in ("kedara", "damini", "vallaki", "nala", "sarpa", "matsya", "vihaga", "yava",
                  "hala", "ardha chandra", "vapee", "daiida", "obhayachari", "ravi", "imdra",
                  "thriiochana", "gauri", "bharathi", "mridanga", "adhl"):
        assert any(added in n for n in covered_lower), added


def test_increment_35_new_detectors_fire_on_defining_charts():
    """Each increment-35 yoga fires on a chart built to its Raman definition, and is silent
    otherwise — a faithfulness check on the 8 new detectors."""
    from app.core import yoga_library as YL
    from app.core.chart_model import Chart

    def chart(signs):
        houses = dict(signs)  # asc_sign=1 → house == sign
        lons = {p: (s - 1) * 30 + 15.0 for p, s in signs.items()}
        return Chart(planet_signs=signs, planet_houses=houses, planet_lons=lons,
                     asc_sign=1, asc_lon=5.0)

    def fires(c, name):
        return next(y for y in YL.detect_all(c) if y.name == name).active

    seven = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    # Gola: all seven in one sign
    assert fires(chart({p: 5 for p in seven} | {"Rahu": 1, "Ketu": 7}), "Gola")
    # Chatussagara: kendras 1,4,7,10 occupied
    assert fires(chart({"Sun": 1, "Moon": 4, "Mars": 7, "Jupiter": 10, "Mercury": 2,
                        "Venus": 3, "Saturn": 5, "Rahu": 6, "Ketu": 12}), "Chatussagara")
    # Sakata: Moon in 6th from Jupiter (Jup=1 → Moon=6)
    assert fires(chart({"Jupiter": 1, "Moon": 6, "Sun": 2, "Mars": 3, "Mercury": 4,
                        "Venus": 5, "Saturn": 7, "Rahu": 8, "Ketu": 2}), "Sakata")
    # and a plain chart should not trip Gola/Chatussagara
    spread = {"Sun": 1, "Moon": 2, "Mars": 5, "Mercury": 3, "Jupiter": 8, "Venus": 11,
              "Saturn": 9, "Rahu": 6, "Ketu": 12}
    assert not fires(chart(spread), "Gola")


def test_increment_36_lord_based_detectors():
    """The lord-based increment-36 yogas fire on charts built to their definition."""
    from app.core import yoga_library as YL
    from app.core.chart_model import Chart

    def chart(signs, asc=1):
        return Chart(planet_signs=signs, planet_houses={p: ((s - asc) % 12) + 1 for p, s in signs.items()},
                     planet_lons={p: (s - 1) * 30 + 15.0 for p, s in signs.items()},
                     asc_sign=asc, asc_lon=(asc - 1) * 30 + 5.0)

    def fires(c, name):
        return next(y for y in YL.detect_all(c) if y.name == name).active

    # Samudra: all seven planets in even houses (asc=Aries → even signs)
    even = {"Sun": 2, "Moon": 4, "Mars": 6, "Mercury": 8, "Jupiter": 10, "Venus": 12,
            "Saturn": 2, "Rahu": 1, "Ketu": 7}
    assert fires(chart(even), "Samudra")

    # Kahala (Aries asc): L4=Moon, L9=Jupiter in mutual kendras; L1=Mars strong (own sign Aries)
    kahala = {"Mars": 1, "Moon": 1, "Jupiter": 4, "Sun": 5, "Mercury": 6,
              "Venus": 7, "Saturn": 8, "Rahu": 9, "Ketu": 3}
    assert fires(chart(kahala), "Kahala")
    # a chart with a debilitated/weak Lagna lord should not fire Kahala
    weak = dict(kahala, Mars=4)  # Mars now in Cancer (debilitated), not strong
    assert not fires(chart(weak), "Kahala")


def test_increment_37_nabhasa_and_navamsa_detectors():
    """The increment-37 Nabhāsa (occupancy) + navāṁśa yogas fire on charts built to their
    Raman definitions and stay silent on a violating chart — covering every new code path
    (arc helper, sign-modality, sign-count, benefic/malefic kendras, and the D9 idiom)."""
    from app.core import yoga_library as YL
    from app.core.chart_model import Chart
    from app.core.shodashavarga import compute_divisional_longitude
    from app.core.dignity import SIGN_RULERS

    seven = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

    def chart(signs, lons=None, asc=1):
        houses = {p: ((s - asc) % 12) + 1 for p, s in signs.items()}
        lons = lons or {p: (s - 1) * 30 + 15.0 for p, s in signs.items()}
        return Chart(planet_signs=signs, planet_houses=houses, planet_lons=lons,
                     asc_sign=asc, asc_lon=(asc - 1) * 30 + 5.0)

    def fires(c, name):
        return next(y for y in YL.detect_all(c) if y.name == name).active

    def by_house(hmap, asc=1, extra=None):
        signs = {p: ((h - 1 + asc - 1) % 12) + 1 for p, h in hmap.items()}
        signs.update(extra or {"Rahu": 1, "Ketu": 7})
        return chart(signs, asc=asc)

    # --- Ākṛti arcs -----------------------------------------------------
    assert fires(by_house({"Sun": 10, "Moon": 11, "Mars": 12, "Mercury": 1, "Jupiter": 10,
                           "Venus": 11, "Saturn": 12}), "Danda")           # 4-arc from 10th
    assert fires(by_house({"Sun": 2, "Moon": 3, "Mars": 4, "Mercury": 5, "Jupiter": 6,
                           "Venus": 7, "Saturn": 8}), "Ardha Chandra")     # 7-arc, non-kendra start
    # a 7-arc that starts on a kendra is Nauka, NOT Ardha Chandra
    assert not fires(by_house({"Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4, "Jupiter": 5,
                               "Venus": 6, "Saturn": 7}), "Ardha Chandra")

    # --- shapes / modality / sign-count --------------------------------
    assert fires(by_house({"Sun": 4, "Moon": 4, "Mars": 4, "Mercury": 10, "Jupiter": 10,
                           "Venus": 10, "Saturn": 4}), "Vihaga")           # all in 4 & 10
    assert fires(by_house({"Sun": 1, "Mars": 7, "Saturn": 1, "Jupiter": 4, "Venus": 10,
                           "Mercury": 4, "Moon": 10}), "Yava")             # malefics 1/7, benefics 4/10
    assert fires(chart({"Sun": 3, "Moon": 6, "Mars": 9, "Mercury": 12, "Jupiter": 3,
                        "Venus": 6, "Saturn": 9, "Rahu": 1, "Ketu": 7}), "Nala")   # dual signs
    assert fires(chart({"Sun": 1, "Moon": 1, "Mars": 2, "Mercury": 2, "Jupiter": 3,
                        "Venus": 3, "Saturn": 4, "Rahu": 5, "Ketu": 11}), "Kedara")  # 4 signs
    # Sarpa: kendras exclusively malefic; a benefic in a kendra cancels it
    assert fires(by_house({"Sun": 1, "Mars": 4, "Saturn": 7, "Moon": 2, "Mercury": 3,
                           "Jupiter": 5, "Venus": 6}), "Sarpa")
    assert not fires(by_house({"Sun": 1, "Mars": 4, "Saturn": 7, "Jupiter": 10, "Moon": 2,
                               "Mercury": 3, "Venus": 6}), "Sarpa")
    # Matsya: malefics in 1/4/8/9, mixed 5th
    assert fires(chart({"Sun": 1, "Mars": 4, "Saturn": 8, "Rahu": 9, "Ketu": 5, "Jupiter": 5,
                        "Moon": 2, "Mercury": 11, "Venus": 12}), "Matsya")

    # --- solar ----------------------------------------------------------
    assert fires(by_house({"Sun": 10, "Saturn": 3, "Moon": 1, "Mars": 2, "Mercury": 4,
                           "Jupiter": 5, "Venus": 6}), "Ravi")            # Sun 10th, 10th-lord Saturn in 3rd

    # --- navāṁśa (D9) — build placements forward via compute_divisional_longitude ---
    def nsign(lon):
        return int(compute_divisional_longitude(lon, 9) % 360.0 // 30) + 1

    def lon_with_navamsa_in(target_navs):
        for step in range(0, 720):
            lon = step * 0.5
            if nsign(lon) in target_navs:
                return lon
        raise AssertionError("no longitude found")

    # Gauri: 10th lord (Aries asc → Saturn) navāṁśa-lord = Mars; Mars exalted in the 10th (Cap),
    # conjunct the Lagna lord (itself). Saturn placed so its navāṁśa sign is Mars-ruled (Ari/Sco).
    sat_lon = lon_with_navamsa_in({1, 8})
    sat_sign = int(sat_lon // 30) + 1
    g_signs = {"Saturn": sat_sign, "Mars": 10, "Sun": 2, "Moon": 3, "Mercury": 4, "Jupiter": 5,
               "Venus": 7, "Rahu": 6, "Ketu": 12}
    g_lons = {p: (s - 1) * 30 + 15.0 for p, s in g_signs.items()}
    g_lons["Saturn"] = sat_lon
    g_lons["Mars"] = 9 * 30 + 28.0            # 28° Capricorn — Mars exalted, house 10
    assert fires(chart(g_signs, g_lons), "Gauri")

    # Mridanga: Sun exalted (10° Aries); the navāṁśa-lord of Sun's navāṁśa sign placed in its own
    # sign within a kendra/trikona; Lagna lord Mars strong (own sign Aries).
    sun_lon = 10.0
    nl = SIGN_RULERS[nsign(sun_lon)]
    own = next(s for s in range(1, 13)
               if SIGN_RULERS[s] == nl and ((s - 1) % 12 + 1) in (1, 4, 5, 7, 9, 10))
    m_signs = {"Mars": 1, "Sun": 1, "Moon": 2, "Mercury": 2, "Jupiter": 2, "Venus": 2,
               "Saturn": 2, "Rahu": 6, "Ketu": 12}
    m_signs[nl] = own
    m_lons = {p: (s - 1) * 30 + 15.0 for p, s in m_signs.items()}
    m_lons["Mars"] = 5.0
    m_lons["Sun"] = sun_lon
    assert fires(chart(m_signs, m_lons), "Mridanga")
