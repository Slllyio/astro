"""verify_quotes: the honesty gate's matching semantics."""
from app.medini.doctrine.tools.page_map import build_page_map
from app.medini.doctrine.tools.verify_quotes import (
    SourceVerifier,
    normalize,
    verify_quote,
)

SOURCE = """\
134

KEY-PLANETS FOR EACH SIGN

Aries. —Saturn, Mercury and Venus are ill-
disposed. Jupiter and the Sun are auspicious.
The mere combination of Jupiter and Saturn
produces no beneficial results.

135

Taurus .—Saturn is the most auspicious and
powerful planet. Thrikona reduction follows.
"""


class TestNormalize:
    def test_casefold_and_whitespace(self):
        assert normalize("The  MOON\nis  bright") == "the moon is bright"

    def test_linebreak_hyphenation_joins(self):
        assert normalize("combi-\nnation") == "combination"

    def test_inline_compound_matches_broken_form(self):
        assert normalize("ill-disposed") == normalize("ill-\ndisposed")

    def test_soft_hyphen_and_ocr_notsign(self):
        assert normalize("favour¬able") == "favourable"
        assert normalize("favour­\nable") == "favourable"

    def test_punctuation_collapses(self):
        assert normalize("Aries. —Saturn, Mercury") == "aries saturn mercury"

    def test_spelling_variants_canonicalized(self):
        assert normalize("Thrikona sodhana") == normalize("Trikona sodhana")


class TestVerifyQuote:
    def test_verbatim_quote_found(self):
        res = verify_quote("Jupiter and the Sun are auspicious.", SOURCE)
        assert res.found and res.offset == SOURCE.index("Jupiter and the Sun")

    def test_quote_across_hyphenated_linebreak(self):
        res = verify_quote(
            "Saturn, Mercury and Venus are ill-disposed. Jupiter and the Sun are auspicious.",
            SOURCE,
        )
        assert res.found

    def test_invented_quote_rejected(self):
        res = verify_quote("Saturn is always benefic for Aries", SOURCE)
        assert not res.found and res.offset is None and res.page is None

    def test_page_assignment_top_folio(self):
        pmap = build_page_map(SOURCE)
        res = verify_quote("Saturn is the most auspicious", SOURCE, pmap)
        assert res.found and res.page == 135
        res2 = verify_quote("Jupiter and the Sun are auspicious", SOURCE, pmap)
        assert res2.found and res2.page == 134

    def test_page_assignment_bottom_folio(self):
        # HPA style: the folio line closes its page, so text BEFORE the
        # "135" line belongs to page 135.
        pmap = build_page_map(SOURCE)
        res = verify_quote(
            "produces no beneficial results", SOURCE, pmap, folio_at="bottom"
        )
        assert res.found and res.page == 135
        # text after the last folio line has no bottom anchor
        res2 = verify_quote(
            "Thrikona reduction follows", SOURCE, pmap, folio_at="bottom"
        )
        assert res2.found and res2.page is None

    def test_empty_quote_rejected(self):
        assert not verify_quote("  — ", SOURCE).found


class TestSourceVerifier:
    def test_stamp_sets_verified_and_page(self):
        v = SourceVerifier(SOURCE, build_page_map(SOURCE))
        rule = {"quote": "powerful planet. Thrikona reduction follows.", "page": None}
        out = v.stamp(rule)
        assert out["quote_verified"] is True
        assert out["page"] == 135
        # original untouched
        assert "quote_verified" not in rule

    def test_stamp_rejects_unfound(self):
        v = SourceVerifier(SOURCE)
        out = v.stamp({"quote": "the moon is made of cheese and so is mars", "page": 3})
        assert out["quote_verified"] is False
        assert out["page"] == 3  # left as-is; the false bit quarantines it
