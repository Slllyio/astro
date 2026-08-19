"""fetch_sources: QC gate logic (no network — QC functions only)."""
from app.medini.doctrine.tools.fetch_sources import (
    MANIFEST,
    UNAVAILABLE_TITLES,
    english_ratio,
    missing_markers,
    qc_text,
)


def _english_book(pages=60, marker="hindu predictive astrology"):
    lines = [f"Chapter about {marker} and planetary strength"]
    for p in range(10, 10 + pages):
        lines.append(str(p))
        lines.append("The lord of the lagna is strong in this case chart")
        lines.append("and the native enjoys the results of the yoga fully")
    lines.append("ashtakavarga tables follow here in the ayurdaya chapter")
    return "\n".join(lines) + "\n"


class TestEnglishRatio:
    def test_english_prose_scores_high(self):
        assert english_ratio(_english_book()) > 0.6

    def test_devanagari_scan_scores_zero(self):
        # hpa2.txt precedent: Hindi-script OCR has no latin word lines.
        text = "\n".join(["शनि की दशा", "मृत्यु योग", "१२३"] * 50)
        assert english_ratio(text) == 0.0

    def test_empty_text(self):
        assert english_ratio("") == 0.0


class TestMarkers:
    def test_all_present(self):
        assert missing_markers("Notable Horoscopes of famous men", ("notable horoscopes",)) == []

    def test_missing_reported(self):
        assert missing_markers("some other book", ("prasna", "muhurtha")) == ["prasna", "muhurtha"]

    def test_match_survives_ocr_whitespace(self):
        # Markers match across line breaks via whitespace folding.
        assert missing_markers("THREE  HUNDRED\nIMPORTANT   COMBINATIONS", ("three hundred important combinations",)) == []


class TestQCGate:
    def test_good_scan_passes(self):
        spec = next(s for s in MANIFEST if s.key == "hpa")
        qc = qc_text(spec, _english_book(pages=300))
        assert qc.passed
        assert qc.page_max >= spec.min_pages
        assert qc.sha256 and qc.bytes > 0

    def test_garbled_scan_fails_on_english_ratio(self):
        spec = next(s for s in MANIFEST if s.key == "hpa")
        qc = qc_text(spec, "\n".join(["॥ श्री ॥"] * 500))
        assert not qc.passed

    def test_wrong_book_fails_on_markers(self):
        spec = next(s for s in MANIFEST if s.key == "muhurtha")
        qc = qc_text(spec, _english_book(pages=300, marker="something else"))
        assert not qc.passed
        assert qc.markers_missing


class TestManifest:
    def test_keys_unique(self):
        keys = [s.key for s in MANIFEST]
        assert len(keys) == len(set(keys))

    def test_every_spec_has_markers_and_floor(self):
        for s in MANIFEST:
            assert s.markers, s.key
            assert s.min_pages > 0, s.key
            assert s.filename.endswith("_djvu.txt"), s.key

    def test_unavailable_titles_recorded(self):
        assert "Ashtakavarga System of Prediction" in UNAVAILABLE_TITLES
