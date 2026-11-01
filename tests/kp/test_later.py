"""The walled later-author layer: cited, labelled, kept apart from Krishnamurti's own rules."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

from app.kp.chart import Birth, cast, sign_index
from app.kp.later.citations import LATER_CITATIONS
from app.kp.later.gulbarga import gulbarga
from app.kp.later.registry import LATER_RULES
from app.kp.later.rules import FRAMING, KINDS, later_indications
from app.kp.later.sources import SOURCES
from app.kp.significators import planet_significations
from app.kp.subs import divisions

BANGALORE = Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59)
ALIBAG = Birth(1924, 12, 23, 21, 0, tz=5.5, lat=18 + 39 / 60, lon=72 + 55 / 60)
KP_DIR = Path(__file__).resolve().parents[2] / "app" / "kp"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _book(source: str) -> Path | None:
    s = SOURCES[source]
    for cand in (os.environ.get(s.env), s.path):
        if cand and Path(cand).is_file():
            return Path(cand)
    return None


class TestWall:
    def test_nothing_outside_the_layer_imports_it(self) -> None:
        """Krishnamurti's natal and horary code never imports app.kp.later."""
        for py in KP_DIR.rglob("*.py"):
            if "later" in py.relative_to(KP_DIR).parts:
                continue
            for node in ast.walk(ast.parse(py.read_text(encoding="utf-8"))):
                names = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
                elif isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                assert not any(n.startswith("app.kp.later") for n in names), py

    def test_every_citation_is_a_later_book(self) -> None:
        """Every quote comes from a later-author book, never from a Krishnamurti Reader."""
        assert {c.source for c in LATER_CITATIONS.values()} <= set(SOURCES)
        for s in SOURCES.values():
            assert "Krishnamurti" not in s.author


@pytest.mark.parametrize("source", sorted(SOURCES))
class TestQuotes:
    def test_every_quote_is_on_its_page(self, source: str) -> None:
        """Each quote occurs on its page marker or runs on into the next page."""
        cites = [c for c in LATER_CITATIONS.values() if c.source == source]
        if not cites:
            pytest.skip(f"no rules cite {source}")
        path = _book(source)
        if path is None:
            pytest.skip(f"{source} text not present (data/ is gitignored)")
        text = path.read_text(encoding="utf-8")
        pages = {int(m.group(1)): m.end() for m in re.finditer(r"<!-- page (\d+) \(scan \d+\) -->", text)}
        order = sorted(pages)
        for c in cites:
            i = order.index(c.page)
            end = pages[order[i + 2]] if i + 2 < len(order) else len(text)
            seg = re.sub(r"<!-- page .*? -->", " ", text[pages[c.page]:end])
            assert _norm(c.quote) in _norm(seg), c.key


class TestRegistry:
    def test_rules_are_well_formed(self) -> None:
        """Every rule has a known condition kind, a cusp 1-12, a context and a citation."""
        assert len(LATER_RULES) == 132
        for r in LATER_RULES.values():
            assert 1 <= r.cusp <= 12 and r.context in ("natal", "horary") and r.sex in (None, "male", "female")
            assert r.conds and all(k in KINDS for k, _ in r.conds), r.key
            assert r.citation in LATER_CITATIONS and r.author, r.key

    def test_excluded_topics_are_absent(self) -> None:
        """No death, lifespan, life-threat, suicide, murder, punishment or moral-character rule (LR3, LR7)."""
        bad = re.compile(r"death|\bdie|dead|lifespan|longevity|life threat|suicid|murder|punish|criminal|"
                         r"illicit|elope|bad habit|timid", re.I)
        for r in LATER_RULES.values():
            assert not bad.search(r.indicates + " " + LATER_CITATIONS[r.citation].quote), r.key

    def test_bosmia_service_rule_reads_star_levels(self) -> None:
        """EZN p.507 'significator (in the star of the occupant or owner)' is read as levels A and C (LR4)."""
        assert LATER_RULES["sixth_service_ac"].conds == (("signifies_ac", ((2, 6, 10),)),)


def _levels(sigs, p: str, levels: str) -> frozenset[int]:
    return frozenset(s.house for s in sigs[p] if s.level in levels)


@pytest.mark.parametrize("birth", [BANGALORE, ALIBAG])
class TestFiring:
    def test_fired_rules_hold(self, birth: Birth) -> None:
        """Independent re-check of the common kinds: a rule fires exactly when its conditions hold."""
        c = cast(birth)
        sigs = planet_significations(c, level_e=True)
        fired = {f.rule.key for f in later_indications(c)}
        simple = {"is", "star_is", "signifies", "star_signifies", "signifies_ac", "not_signifies",
                  "sign_in", "star_sign_in", "star_occupies"}
        checked = 0
        for r in LATER_RULES.values():
            if not all(k in simple for k, _ in r.conds):
                continue
            csl = c.cusp(r.cusp).sub_lord
            star = c.planets[csl].star_lord
            ok = True
            for k, a in r.conds:
                if k == "is":
                    ok &= csl in a
                elif k == "star_is":
                    ok &= star in a
                elif k in ("signifies", "star_signifies", "signifies_ac"):
                    hs = _levels(sigs, star if k == "star_signifies" else csl, "AC" if k == "signifies_ac" else "ABCD")
                    ok &= all(hs & set(g) for g in a)
                elif k == "not_signifies":
                    ok &= not (_levels(sigs, csl, "ABCD") & set(a))
                elif k == "sign_in":
                    ok &= sign_index(c.planets[csl].longitude) in a
                elif k == "star_sign_in":
                    ok &= sign_index(c.planets[star].longitude) in a
                elif k == "star_occupies":
                    ok &= c.planets[star].bhava in a
            assert (r.key in fired) == ok, r.key
            checked += 1
        assert checked > 100

    def test_every_row_is_labelled(self, birth: Birth) -> None:
        """Each fired row names its author and book and says it is not Krishnamurti's."""
        for f in later_indications(cast(birth)):
            d = f.to_dict()
            assert d["author"] and d["book"] and d["framing"] == FRAMING
            assert "not Krishnamurti's" in d["framing"] and "not a validated prediction" in d["framing"]

    def test_sex_filter(self, birth: Birth) -> None:
        """A rule the author ties to women is dropped for a male native, kept otherwise."""
        c = cast(birth)
        male = {f.rule.key for f in later_indications(c, sex="male")}
        assert not any(LATER_RULES[k].sex == "female" for k in male)
        both = {f.rule.key for f in later_indications(c)}
        assert male <= both

    def test_context_filter(self, birth: Birth) -> None:
        """context='horary' returns horary rules only."""
        assert all(f.rule.context == "horary" for f in later_indications(cast(birth), context="horary"))


class TestGulbarga:
    def test_book_example_number_245(self) -> None:
        """AS6 p.1603: number 245 is 'co-ruled by Jupiter, Mercury and Moon'; on 8-1-1981 6 p.m. the Moon
        star lord was the Moon, so the answer was yes."""
        d = divisions()[244]
        assert (d.sign_lord, d.star_lord, d.sub_lord) == ("Jupiter", "Mercury", "Moon")
        a = gulbarga(245, Birth(1981, 1, 8, 18, 25, tz=5.5, lat=13.08, lon=80.27))
        assert a.moon_star_lord == "Moon" and a.yes
        assert "not Krishnamurti's" in a.to_dict()["framing"]

    def test_number_range(self) -> None:
        """Numbers outside 1-249 are refused."""
        with pytest.raises(ValueError):
            gulbarga(250, BANGALORE)
