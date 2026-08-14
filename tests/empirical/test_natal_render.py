"""Render completeness: framing first, JSON total, markdown loses nothing.

The epistemic point: the repo's REPORT COMPLETENESS rule (CLAUDE.md) exists
because renderers historically dropped computed fields on the way to the
screen. These tests make the natal surfaces mechanically total — the markdown
is checked against the JSON, and the JSON against the chart — so a field
cannot vanish without a test failing.
"""

from __future__ import annotations

from app.empirical.natal.chart import BirthMoment, assemble_chart
from app.empirical.natal.decoder import decode
from app.empirical.natal.lexicon import TRADITION_BANNER
from app.empirical.natal.render import NATAL_FRAMING, render, to_markdown
from app.empirical.western.tropical import DEFAULT_BODIES

CANONICAL = BirthMoment(1990, 7, 15, 12, 0, 12.97, 77.59, 5.5)
SVALBARD = BirthMoment(1990, 7, 15, 12, 0, 78.0, 15.6, 1.0)


def _decoded(moment=CANONICAL, **kwargs):
    return decode(assemble_chart(moment, **kwargs))


class TestFraming:
    """The disclosure leads every surface, verbatim."""

    def test_json_framing_first_and_verbatim(self):
        """The payload's framing key carries NATAL_FRAMING exactly."""
        data = render(_decoded())
        assert data["framing"] == NATAL_FRAMING
        assert data["tradition_banner"] == TRADITION_BANNER

    def test_markdown_carries_framing_before_any_content(self):
        """The framing blockquote appears before the first data table."""
        md = to_markdown(_decoded())
        assert NATAL_FRAMING in md
        assert md.index(NATAL_FRAMING) < md.index("## Planets at birth")

    def test_framing_names_the_null_and_refuses_prediction(self):
        """The framing must state the measured null and the non-prediction."""
        assert "no predictive advantage" in NATAL_FRAMING
        assert "This is not a prediction about you." in NATAL_FRAMING


class TestJsonCompleteness:
    """Every computed field appears in the payload."""

    def test_all_bodies_with_all_position_fields(self):
        """Each DEFAULT_BODIES entry carries the full Position field set."""
        data = render(_decoded())
        assert set(data["chart"]["positions"]) == set(DEFAULT_BODIES)
        expected = {
            "longitude", "sign", "degree_in_sign", "is_retrograde",
            "latitude", "distance_au", "speed_longitude", "speed_latitude",
        }
        for body, pos in data["chart"]["positions"].items():
            assert set(pos) == expected, body

    def test_houses_carry_cusps_and_all_four_angles(self):
        """12 cusps plus ascendant/midheaven/armc/vertex all present."""
        h = render(_decoded())["chart"]["houses"]
        assert len(h["cusps"]) == 12
        for key in ("ascendant", "midheaven", "armc", "vertex"):
            assert key in h

    def test_aspects_carry_orb_and_applying(self):
        """Every aspect row keeps its full audit fields."""
        data = render(_decoded())
        assert data["chart"]["aspects"]
        for a in data["chart"]["aspects"]:
            assert {"body_a", "body_b", "aspect", "angle", "separation", "orb", "allowed_orb", "applying"} <= set(a)

    def test_balance_weights_disclosed(self):
        """The weighted-balance arithmetic is shown, not just its result."""
        data = render(_decoded())
        assert data["chart"]["balance_weights"]["Sun"] == 2
        assert data["chart"]["balance_weights"]["Ascendant"] == 2

    def test_statements_keep_their_audit_trail(self):
        """text/source/provenance/basis survive rendering for every statement."""
        data = render(_decoded())
        for section in data["facets"]:
            for stmt in section["statements"]:
                assert stmt["text"] and stmt["source"] and stmt["provenance"] and stmt["basis"]


class TestMarkdownLosesNothing:
    """The markdown is checked against the JSON, mechanically."""

    def test_every_statement_text_appears_in_markdown(self):
        """No decoded sentence may be dropped by the text renderer."""
        decoded = _decoded()
        md = to_markdown(decoded)
        for section in render(decoded)["facets"]:
            for stmt in section["statements"]:
                assert stmt["text"] in md

    def test_every_body_and_disclosure_appears_in_markdown(self):
        """All bodies, the south node and every disclosure line surface."""
        decoded = _decoded()
        md = to_markdown(decoded)
        for body in DEFAULT_BODIES:
            assert body in md
        assert "SouthNode" in md
        for d in render(decoded)["disclosures"]:
            assert d in md

    def test_missing_houses_disclosed_in_both_formats(self):
        """A houseless chart states the reason in JSON and markdown alike."""
        decoded = _decoded(SVALBARD, house_system="placidus")
        data = render(decoded)
        assert data["chart"]["houses"] is None
        assert data["chart"]["houses_missing_reason"] == "polar_latitude"
        md = to_markdown(decoded)
        assert "polar_latitude" in md
        assert "Degraded" in md
