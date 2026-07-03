"""page_map: mechanical folio-line page maps for OCR dumps."""
from app.medini.doctrine.tools.page_map import PageMap, build_page_map


def _text(lines):
    return "\n".join(lines) + "\n"


class TestBuildPageMap:
    def test_accepts_monotonic_folio_chain(self):
        text = _text(["intro prose", "12", "page twelve prose", "13", "more", "14"])
        pmap = build_page_map(text)
        assert [a.page for a in pmap.anchors] == [12, 13, 14]

    def test_rejects_backward_and_huge_jumps(self):
        # 1962 is a year (over the page ceiling, not even a candidate);
        # 5 is a table figure after page 40.
        text = _text(["39", "prose", "40", "1962", "5", "41"])
        pmap = build_page_map(text)
        assert [a.page for a in pmap.anchors] == [39, 40, 41]
        assert pmap.candidates_seen == 4

    def test_year_table_cannot_form_a_chain(self):
        # Ayanamsa tables list consecutive years — perfectly monotonic, but
        # above any plausible folio. The ceiling excludes them entirely.
        years = [str(y) for y in range(1826, 1861)]
        text = _text(["3", "prose", "4", *years, "5"])
        pmap = build_page_map(text)
        assert [a.page for a in pmap.anchors] == [3, 4, 5]

    def test_tolerates_missing_folios_within_max_jump(self):
        text = _text(["10", "x", "13", "x", "22"])  # 13->22 exceeds max_jump=8
        pmap = build_page_map(text)
        assert [a.page for a in pmap.anchors] == [10, 13]

    def test_ocr_specked_folio_lines_match(self):
        text = _text(["* 77 *", "prose", ". 78", "79 —"])
        pmap = build_page_map(text)
        assert [a.page for a in pmap.anchors] == [77, 78, 79]

    def test_prose_numbers_are_not_candidates(self):
        text = _text(["born in 1917 at 12 noon", "the 8th house"])
        pmap = build_page_map(text)
        assert pmap.candidates_seen == 0
        assert pmap.anchors == []


class TestPageForOffset:
    def test_lookup_between_anchors(self):
        lines = ["5", "aaaa", "6", "bbbb", "7"]
        text = _text(lines)
        pmap = build_page_map(text)
        # offset of "aaaa" is right after "5\n"
        assert pmap.page_for_offset(text.index("aaaa")) == 5
        assert pmap.page_for_offset(text.index("bbbb")) == 6
        assert pmap.page_for_offset(len(text) - 1) == 7

    def test_before_first_anchor_is_none(self):
        text = _text(["front matter", "9", "prose"])
        pmap = build_page_map(text)
        assert pmap.page_for_offset(0) is None

    def test_json_round_trip(self):
        text = _text(["3", "x", "4"])
        pmap = build_page_map(text)
        clone = PageMap.from_json(pmap.to_json())
        assert clone.anchors == pmap.anchors
        assert clone.candidates_seen == pmap.candidates_seen
        assert clone.page_for_offset(text.index("x")) == 3


class TestQCSignals:
    def test_monotonic_fraction_low_for_garbled_scan(self):
        # Random large numbers (chart longitudes / years) accept poorly.
        text = _text(["350", "1962", "12", "1899", "271", "4"])
        pmap = build_page_map(text)
        assert pmap.monotonic_fraction < 0.5

    def test_max_page_empty_text(self):
        pmap = build_page_map("")
        assert pmap.max_page == 0
        assert pmap.monotonic_fraction == 0.0
