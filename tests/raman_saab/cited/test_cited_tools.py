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
    # loaded by path: a stray site-packages "tests" package can shadow the repo's tests/ folder
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_golden_harness", Path(__file__).resolve().parents[1] / "test_goldens.py")
    harness = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(harness)
    track_b_scoreboard, track_b_ordinal_scoreboard = (harness.track_b_scoreboard,
                                                      harness.track_b_ordinal_scoreboard)
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


# -- the spread of indications (2026-11-05) ----------------------------------------------------

from app.raman_saab.cited import spread as sp  # noqa: E402


def test_spread_kinds() -> None:
    assert sp.kind_of(2, 1) == sp.BOTH
    assert sp.kind_of(2, 0) == sp.ONLY_FOR
    assert sp.kind_of(0, 3) == sp.ONLY_AGAINST
    assert sp.kind_of(0, 0) == sp.SILENT


def test_spread_counts_match_the_ledgers_and_change_no_verdict(fdr: reading.CitedReading) -> None:
    for hr in fdr.houses:
        pf = ht.judge_house(fdr.chart, hr.audit.house)
        for c, sv in zip(hr.counts, pf.significations):
            assert c.spread is not None and c.spread.verdict == str(sv.verdict)
            assert c.n_for == len({f.rule.id for f in sv.ledger.fired_benefic})
            assert c.n_against == len({f.rule.id for f in sv.ledger.fired_malefic})
            assert c.spread.n_descriptive == len({f.rule.id for f in sv.ledger.fired_neutral})


def test_baseline_covers_every_matter_and_is_shares(fdr: reading.CitedReading) -> None:
    b = sp.baseline()
    assert b is not None and b["n"] >= 1000
    for hr in fdr.houses:
        for c in hr.counts:
            m = sp.base_for(c.spread.house, c.spread.matter)
            assert m is not None, (c.spread.house, c.spread.matter)
            total = m["both_share"] + m["only_for_share"] + m["only_against_share"]
            assert 0.0 <= total <= 1.0 + 1e-9


def test_baseline_is_reproducible_on_a_small_sample() -> None:
    a, b = sp.build_baseline(n=5, seed=11), sp.build_baseline(n=5, seed=11)
    assert a == b and a["n"] == 5


def test_reading_states_the_spread(fdr: reading.CitedReading) -> None:
    html, md = reading.to_html(fdr), reading.to_markdown(fdr, quotes=False)
    for text in (html, md):
        assert "How sure the books are" in text
        assert "random charts" in text
    assert any(c.spread.kind == sp.BOTH for h in fdr.houses for c in h.counts)
    assert "Both outcomes are indicated" in html
    assert "1 rules" not in html


# -- classical shelf --------------------------------------------------------------------------

_SARAV = """---
id: saravali-ch012
---

# Chapter 12

1. The Sun in the seventh house makes the native suffer humiliation from women and
keeps him wandering, says the sage, without a settled home.

2-3. If the seventh lord joins a malefic the spouse will be of a harsh temper and the
union will know quarrels, unless a benefic aspects the house.

Page 214

4. Jupiter in the seventh gives a devoted and learned spouse and an honoured name in
the assembly of the wise.
"""

_JP = """Some front matter of the scan, with no chapter yet and nothing numbered here.

ADHYAYA VII

Sloka 1. Raja yogas are now described by the author in their order and in full detail.

38. A bare number like this is a page or list number in this scan, not a verse.

Siokos 2-3. When three or more planets are exalted the native becomes a king, or equal to one.
"""


@pytest.fixture()
def shelf_sources(tmp_path: Path) -> Path:
    src = tmp_path / "sources"
    (src / "saravali").mkdir(parents=True)
    (src / "saravali" / "chapter_012_seventh-house.md").write_text(_SARAV, encoding="utf-8")
    (src / "jataka_parijata").mkdir()
    (src / "jataka_parijata" / "chapter_003_ocr-junk-name.md").write_text(_JP, encoding="utf-8")
    (src / "bphs").mkdir()                     # the registry's copy, which the shelf replaces
    (src / "bphs" / "chapter_024_effects.md").write_text(_SARAV, encoding="utf-8")
    return src


class TestClassicalShelf:
    def test_shelf_books_are_labelled_not_raman(self, shelf_sources: Path) -> None:
        """Every shelf file is scoped 'classical, not Raman' and none is natal-citable."""
        from app.raman_saab.cited import classics
        from app.raman_saab.doctrine import book_registry
        fs = classics.shelf_files(shelf_sources)
        assert {f.prefix for f in fs} == {"SARAV-12", "JP-3"}
        assert all(f.scope == "classical, not Raman" for f in fs)
        assert not any(book_registry.is_natal_citable(f.prefix) for f in fs)
        assert {c.tag for c in classics.SHELF}.isdisjoint({b.tag for b in book_registry.BOOKS})

    def test_chapter_and_verse_labels(self, shelf_sources: Path) -> None:
        """Chapter comes from the file (Saravali) or a heading (JP); verses as printed."""
        from app.raman_saab.cited import classics
        fs = {f.prefix: f for f in classics.shelf_files(shelf_sources)}
        rows = list(classics.passages(list(fs.values()), corpus.lines_of, library.chunk_lines))
        labels = {(r[0].prefix, r[4]) for r in rows}
        assert ("SARAV-12", "ch. 12, vv. 1-3") in labels
        assert ("SARAV-12", "ch. 12, v. 4") in labels
        assert any(p == "JP-3" and lab.startswith("adhyaya 7, v") for p, lab in labels)
        assert not any("38" in lab for p, lab in labels if p == "JP-3")     # bare number ignored
        for f, lo, hi, text, _ in rows:                         # tokens read back verbatim
            assert text == "\n".join(corpus.lines_of(f.path)[lo - 1:hi]).strip()

    def test_library_indexes_one_bphs_and_says_where(self, shelf_sources: Path, tmp_path: Path) -> None:
        """The registry BPHS copy is left out (the shelf's copy replaces it); hits carry location."""
        idx = tmp_path / "lib.sqlite"
        library.build(idx, sources=shelf_sources)
        m = library.meta(idx)
        assert "passages_BPHS" not in m and int(m["passages_SARAV"]) >= 2
        res = library.search("seventh lord malefic spouse", kinds=("passage",), path=idx)
        assert res.hits and res.hits[0].cite.startswith("SARAV-12:")
        assert res.hits[0].scope == "classical, not Raman"
        assert "ch. 12" in res.hits[0].title and "tr. R. Santhanam" in res.hits[0].title
        assert not library.search("seventh lord malefic", kinds=("passage",), scope="Raman, natal",
                                  path=idx).hits

    def test_heading_parser_ignores_prose(self) -> None:
        """'CHAPTER XII' is a heading; a sentence mentioning a chapter is not."""
        from app.raman_saab.cited import classics
        assert classics.chapter_heading("CHAPTER XII") == 12
        assert classics.chapter_heading("Adhyaya 3", "adhyaya") == 3
        assert classics.chapter_heading("chapter of the book is long") is None
        assert classics.chapter_heading("Adh. XVII.", "adhyaya") == 17
        assert classics.chapter_heading("chapter 1 supra") is None
        assert classics.chapter_heading("ch. 1 as well.") is None
        assert classics.chapter_heading("Hora Ratnam / Chapter 5", "hora-ratnam") == 5
        assert classics.verse_at("1995") is None and classics.verse_at("12-14. Saturn in") == (12, 14, False)
        assert classics.verse_at("12. If the", "sloka") is None
        assert classics.verse_at("Siokos 61-63. During", "sloka") == (61, 63, True)

    def test_merged_chapter_takes_its_running_head(self, tmp_path: Path) -> None:
        """A BPHS file holding two chapters labels the second by its own 'Chapter N' head."""
        from app.raman_saab.cited import classics
        d = tmp_path / "sources" / "bphs_santhanam_full"
        d.mkdir(parents=True)
        (d / "chapter_053_x.md").write_text(
            "1. The first verse of chapter fifty three is here in full.\n\n"
            "Chapter 54\n\n1. The first verse of chapter fifty four is here in full.\n",
            encoding="utf-8")
        fs = classics.shelf_files(tmp_path / "sources")
        rows = list(classics.passages(fs, corpus.lines_of, library.chunk_lines))
        assert rows[-1][4].endswith("54")       # "ch. 54" or, merged with 53, "ch. 53-54"

    def test_colophon_chapters_and_switched_off_labels(self, tmp_path: Path) -> None:
        """Hora Sara takes its chapter from 'Thus ends'; Laghu Parashari gets no verse label;
        Phaladeepika's index file is left out."""
        from app.raman_saab.cited import classics
        src = tmp_path / "sources"
        for slug, name, text in (
                ("hora_sara_santhanam", "chapter_013_x.md",
                 "Should Mars be in the 8th house there will be misconceptions with one's enemies.\n"
                 "Thus ends the 11th Chapter entitled Effects of Mars Dasa.\n"),
                ("laghu_parashari_verma_v2", "chapter_001_full-text-unsplit.md",
                 "77. Vimsottari Dasa is one such scientific method to time good and bad periods.\n"),
                ("phaladeepika", "chapter_33_english-index.md",
                 "KUHU YOGA. VI-57, 61. KUJA and many more index words to fill the line here.\n")):
            (src / slug).mkdir(parents=True)
            (src / slug / name).write_text(text, encoding="utf-8")
        fs = classics.shelf_files(src)
        assert {f.book for f in fs} == {"HSARA", "LP"}
        labels = {r[0].book: r[4] for r in classics.passages(fs, corpus.lines_of, library.chunk_lines)}
        assert labels == {"HSARA": "ch. 11", "LP": ""}

    def test_house_word_dropped_beside_an_ordinal(self) -> None:
        """'seventh lord in the eighth house' must find a verse that omits 'house'."""
        assert library.expand("seventh lord in the eighth house") == [
            ("seventh", "7th"), ("lord",), ("eighth", "8th")]
        assert library.expand("house") == [("house",)]

    def test_notes_list_does_not_reset_the_verse_counter(self, tmp_path: Path) -> None:
        """BPHS ch. 24: a Notes list '1. 2. 3.' must not hide verse 80 that follows."""
        from app.raman_saab.cited import classics
        d = tmp_path / "sources" / "bphs_santhanam_full"
        d.mkdir(parents=True)
        (d / "chapter_024_x.md").write_text(
            "79. If the 7th lord is in the 7th itself, the native will be of good conduct and charm.\n\n"
            "Notes : the following points may be kept in view by the reader of this verse.\n"
            "1. The lord's strength matters here in the reading of the verse above.\n"
            "2. The aspects of benefics on the house matter equally in the reading.\n\n"
            "Some more lines of the translator's notes run on here for a while more.\n"
            "And still more lines of notes that follow in the scan of the book.\n\n"
            "80. If the 7th lord is in the 8th, the native will be deprived of his wife.\n",
            encoding="utf-8")
        rows = list(classics.passages(classics.shelf_files(tmp_path / "sources"), corpus.lines_of,
                                      library.chunk_lines))
        last = [r for r in rows if "80. If the 7th lord" in r[3]][0]
        assert "v. 80" in last[4] and "(cont.)" not in last[4]

    def test_footers_and_colophons_name_the_chapter(self, tmp_path: Path) -> None:
        """Hora Ratnam: the scraper header is ignored, the page footer names the chapter.
        Brihat Jataka: a file holding two chapters is split by its colophons."""
        from app.raman_saab.cited import classics
        src = tmp_path / "sources"
        (src / "hora_ratnam_santhanam").mkdir(parents=True)
        (src / "hora_ratnam_santhanam" / "chapter_016_pages-751-800.md").write_text(
            "# Bala Bhadra's Hora Ratnam — Chapter 16 (pages 751-800)\n\n"
            "67. The native will be involved in crimes if Rahu joins another malefic planet.\n\n"
            "Hora Ratnam / Chapter 5\n", encoding="utf-8")
        (src / "brihat_jataka").mkdir()
        (src / "brihat_jataka" / "chapter_002_x.md").write_text(
            "The animals born are to be ascertained from the colour of the planets in the Lagna.\n"
            "Thus ends the third Chapter on the subject of births of animals.\n\n"
            "1. Now the Moon's yogas are described by the author for the reader in full.\n"
            "Thus ends the Fifth Chapter on the subject in this book.\n\n"
            "An appendix by the translator follows with notes on various matters here.\n",
            encoding="utf-8")
        rows = list(classics.passages(classics.shelf_files(src), corpus.lines_of, library.chunk_lines))
        hr = [r[4] for r in rows if r[0].book == "HRAT"]
        assert hr and all(x.startswith("ch. 5") for x in hr)
        (src / "hora_ratnam_santhanam" / "chapter_019_pages-901-950.md").write_text(
            "12. The last verse of the fifth chapter is printed here for the reader.\n"
            "Thus ends the 5th Chapter of the work.\n\n"
            "Glossary: Dasa Varga means the ten divisional charts used by the author.\n\n"
            "Hora Ratnam / Chapter 5\n", encoding="utf-8")
        f19 = [f for f in classics.shelf_files(src) if f.prefix == "HRAT-19"][0]
        chs = [c for c, _, _ in classics.line_locations(f19, corpus.lines_of(f19.path), 5)]
        assert chs[0] == 5 and chs[3] is None and chs[5] is None    # back matter left blank
        src2 = tmp_path / "sources2"
        (src2 / "hora_ratnam_santhanam").mkdir(parents=True)
        (src2 / "hora_ratnam_santhanam" / "chapter_016_pages-751-800.md").write_text(
            "67. The native will be involved in crimes if Rahu joins another malefic planet.\n\n"
            "Hora Ratnam / Chapter 5\n", encoding="utf-8")
        f20 = src2 / "hora_ratnam_santhanam" / "chapter_020_pages-951-990.md"
        f20.write_text(
            "12. The last verse of the fifth chapter is printed here for the reader, at length\n"
            "so that it makes a passage of its own in the index of the library here.\n"
            "Thus ends the 5th Chapter of the work.\n\n"
            "Some more words of the colophon page follow here.\n"
            "And more of them, on the same page of the scan.\n"
            "And still more of them, on that page of the scan.\n"
            "And yet more of them, closing the colophon page.\n\n"
            "1. Garga, the ancient author whose works Bala Bhadra consulted for this book.\n"
            "2. Yavanacharya, another ancient author consulted by Bala Bhadra for it.\n",
            encoding="utf-8")
        hr = [f for f in classics.shelf_files(src2) if f.book == "HRAT"]     # 16 then 20
        labs = [(r[0].prefix, r[4]) for r in classics.passages(hr, corpus.lines_of, library.chunk_lines)]
        h20 = [lab for p, lab in labs if p == "HRAT-20"]
        assert h20[0].startswith("ch. 5") and h20[-1] == ""        # the list after it is not verses
        bj = [f for f in classics.shelf_files(src) if f.book == "BJ"][0]
        lines = corpus.lines_of(bj.path)
        chs = [c for c, _, _ in classics.line_locations(bj, lines)]
        assert chs[0] == 3 and chs[3] == 5 and chs[-1] is None       # appendix left unlabelled

    def test_inline_sloka_counts_in_sloka_books(self) -> None:
        """Phaladeepika prints '|| Sloka 15.' mid-line; Jataka Parijata OCR spells 'Slokfi 23'."""
        from app.raman_saab.cited import classics
        assert classics.verse_at("asameva ... || Sloka 15.", "sloka")[:2] == (15, 15)
        assert classics.verse_at("Slokfi 23. When the", "sloka")[:2] == (23, 23)
        assert classics.verse_at("text then Sloka 15. here", "numbered") is None
        assert classics.verse_at("|| Sloka 20-Whenever the", "sloka")[:2] == (20, 20)
        assert classics.verse_at("Sloka 31- When", "sloka")[:2] == (31, 31)
        assert classics.chapter_heading("Hora Ratnara / Chapter 1", "hora-ratnam") == 1
        assert classics.chapter_heading("/ Chapter 4", "hora-ratnam") == 4
        assert classics.chapter_heading("t Chapter 81") == 81

    def test_notes_item_repeating_a_verse_number_is_not_a_verse(self, tmp_path: Path) -> None:
        """BPHS ch. 19: '3. The 10th lord' in the Notes after verse 3 is a list item."""
        from app.raman_saab.cited import classics
        d = tmp_path / "sources" / "bphs_santhanam_full"
        d.mkdir(parents=True)
        (d / "chapter_019_x.md").write_text(
            "3. If the 10th lord is strong the native will be famous and of good deeds.\n\n"
            "Notes : the reader should keep these in mind while reading this verse.\n\n"
            "3. The 10th lord in the 10th itself is a list item of the notes, not a verse.\n",
            encoding="utf-8")
        f = classics.shelf_files(tmp_path / "sources")[0]
        opened = [i for i, (_, _, o) in enumerate(classics.line_locations(f, corpus.lines_of(f.path))) if o]
        assert opened == [0]
