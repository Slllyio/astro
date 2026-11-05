"""The cited tools (app/raman_saab/cited): source layer, library, study view, cited reading.

The library and source tests build on a small synthetic book in a temp folder, so they run on a
clone without the book texts. Tests that need the real texts skip when they are absent.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from app.raman_saab.cited import corpus, library, reading, study
from app.raman_saab.judges import house_template as ht

_HAVE_BOOKS = corpus.file_for("NH") is not None
_needs_books = pytest.mark.skipif(not _HAVE_BOOKS, reason="book texts not on this machine")

_BOOK = """---
id: test
---

# Test book

The seventh lord in the eighth house
gives a delayed marriage, says the text.

<!-- page 2 -->
A short line.

Kemadruma Yoga arises when there are no planets on both sides of the Moon. The person
will be poor and dependent.
"""


@pytest.fixture()
def tiny_sources(tmp_path: Path) -> Path:
    d = tmp_path / "sources" / "kp_reader1_casting"          # any slug the corpus knows
    d.mkdir(parents=True)
    (d / "chapter_001_full-text-unsplit.md").write_text(_BOOK, encoding="utf-8")
    return tmp_path / "sources"


# -- source layer -----------------------------------------------------------------------------

def test_parse_cite() -> None:
    assert corpus.parse_cite("HTJAH-I:1586") == ("HTJAH-I", 1586, 1586)
    assert corpus.parse_cite("HPA-20:70-65") == ("HPA-20", 65, 70)
    assert corpus.parse_cite("not a cite") is None


def test_scopes_keep_systems_apart() -> None:
    assert corpus.scope_of("HTJAH-I", "live") == "Raman, natal"
    assert corpus.scope_of("PM2F", "live") == "horary"
    assert corpus.scope_of("BPHS", "corroboration") == "classical, not Raman"
    assert corpus.scope_of("ROW-BJ", "lineage-catalog") == "Rao lineage, not citable"


def test_book_files_on_a_tiny_corpus(tiny_sources: Path) -> None:
    files = corpus.book_files(tiny_sources)
    assert [(f.prefix, f.scope) for f in files] == [("KPR1", corpus.KP_SCOPE)]


def test_a_paraphrase_is_not_located() -> None:
    rec = {"book": "NH", "citations": ["NH:10131"]}
    assert corpus.locate("words that Raman never wrote anywhere in any of his books", rec) is None


@_needs_books
def test_a_quote_is_located_at_its_own_lines() -> None:
    rec = corpus.example("NH.chart_47")
    where = corpus.locate(rec["expected_verdicts"]["H10"]["verdict_prose"], rec)
    assert where is not None
    text = " ".join(corpus.passage(where)["text"].split())
    assert "highest position in life" in text


# -- library ----------------------------------------------------------------------------------

def test_chunks_read_back_exactly(tiny_sources: Path) -> None:
    lines = corpus.lines_of(tiny_sources / "kp_reader1_casting" / "chapter_001_full-text-unsplit.md")
    chunks = list(library.chunk_lines(lines))
    assert chunks, "the book produced no passages"
    for lo, hi, text in chunks:
        assert text == "\n".join(lines[lo - 1:hi]).strip()
        assert "id: test" not in text and "<!--" not in text


def test_expand_widens_synonyms_and_ordinals() -> None:
    groups = library.expand('What does the 7th lord in the eighth give for "dhana yoga" marriage')
    flat = [set(g) for g in groups]
    assert {"7th", "seventh"} <= flat[0]
    assert {"eighth", "8th"} in flat
    assert ("dhana yoga",) in groups
    assert any({"marriage", "kalatra", "spouse"} <= g for g in flat)
    assert not any("the" in g for g in flat)


def test_search_finds_the_planted_passage(tiny_sources: Path, tmp_path: Path) -> None:
    idx = tmp_path / "lib.sqlite"
    counts = library.build(idx, sources=tiny_sources)
    assert counts["passage"] >= 1 and counts["rule"] > 500 and counts["example"] > 300
    res = library.search("seventh lord in the eighth", kinds=("passage",), path=idx)
    assert res.mode == "all words"
    assert res.hits and res.hits[0].cite.startswith("KPR1:")
    _, lo, hi = corpus.parse_cite(res.hits[0].cite)
    lines = corpus.lines_of(tiny_sources / "kp_reader1_casting" / "chapter_001_full-text-unsplit.md")
    assert "seventh lord in the eighth" in "\n".join(lines[lo - 1:hi])
    # nothing has all the words, so the search falls back to any word, and says so
    res2 = library.search("kemadruma zzzunknownword", kinds=("passage",), path=idx)
    assert res2.mode == "any word" and res2.hits
    # scope filter: no Raman-natal book in the tiny corpus
    assert not library.search("kemadruma", kinds=("passage",), scope="Raman, natal", path=idx).hits


def test_search_without_an_index_says_how_to_build(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="library build"):
        library.search("anything", path=tmp_path / "missing.sqlite")


# -- study ------------------------------------------------------------------------------------

def test_distance_matches_the_harness_convention() -> None:
    assert study.distance("mixed", "mixed") == 0
    assert study.distance("mixed", "favourable") == 1
    assert study.distance("afflicted", "favourable") == 2
    assert study.distance("insufficient-evidence", "mixed") == 2
    assert study.distance(None, "mixed") == 2


def test_study_totals_equal_the_scored_harness() -> None:
    """The study page must report exactly the figure the golden ratchet scores."""
    from tests.raman_saab.test_goldens import track_b_ordinal_scoreboard, track_b_scoreboard
    exact, total, _ = track_b_scoreboard()
    within1, _, real = track_b_ordinal_scoreboard()
    tally = Counter()
    for s in study.all_studies():
        tally.update(s.tally())
    assert sum(tally.values()) == total
    assert tally[study.AGREE] == exact
    assert tally[study.AGREE] + tally[study.NEAR] == within1
    assert tally[study.OPPOSITE] == len(real)


def test_study_chart_page_shows_both_sides() -> None:
    s = study.study(corpus.example("NH.chart_47"))
    html = study.chart_html(s)
    assert "Raman's own write-up" in html and "The engine" in html
    for h in s.houses:
        for r in h.rules_for + h.rules_against:
            assert ":" in r.cite


# -- the cited reading ------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fdr() -> reading.CitedReading:
    return reading.from_golden("NH.chart_47", stability=False)


def test_reading_changes_no_verdict(fdr: reading.CitedReading) -> None:
    for hr in fdr.houses:
        pf = ht.judge_house(fdr.chart, hr.audit.house)
        assert hr.audit.verdict == pf.rollup
        assert [c.verdict for c in hr.counts] == [str(sv.verdict) for sv in pf.significations]


def test_every_rule_carries_a_citation(fdr: reading.CitedReading) -> None:
    rules = [r for hr in fdr.houses for r in hr.audit.rules]
    assert rules
    assert all(corpus.parse_cite(r.citation) for r in rules)


def test_reading_carries_the_honesty_notice_and_ramans_words(fdr: reading.CitedReading) -> None:
    html = reading.to_html(fdr)
    md = reading.to_markdown(fdr, quotes=False)
    assert "It is not a forecast" in html and "It is not a forecast" in md
    assert "Raman's own conclusion" in html
    assert md.count("## The ") == 12


def test_reading_of_a_new_chart_has_no_raman_conclusion() -> None:
    r = reading.from_birth("Test", "1950-01-01", "12:00", 5.5, 13.0, 77.6, stability=False)
    assert all(h.raman is None for h in r.houses)
    assert "Raman's own conclusion on this chart" not in reading.to_html(r)
