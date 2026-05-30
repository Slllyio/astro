"""Tests for ``app.reading.computations.yoga_calibration`` (Tier-3).

Phase 6 Wave B — closed-form yoga strength scoring.

Discipline asserted by this test file (Spec Section 14):

1.  **Methodology docstring block** — Section 14 mandate.
2.  **Closed-form, doctrine-cited constants** — every coefficient
    (dignity multiplier, drishti boost) is BPHS-cited; nothing in this
    module is fit / tuned against a historical outcome dataset.
3.  **No-fitting declaration** — the docstring must declare verbatim
    that no threshold or weight was fit against any outcome corpus.
4.  **Strength range [0.0, 1.0]** — every emitted strength_score is
    normalised; participating-planet vimsopaka inputs are in [0, 20]
    each.
5.  **Pass-through for non-yoga classifications** — Findings whose
    classification is not ``"yoga"`` are returned unchanged.
6.  **Lazy-import discipline** — no heavy ML stack at module top.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_yoga_finding():
    """Factory for a Finding with classification=yoga and parametric evidence."""
    from app.reading.schema import ConfidenceScore, Finding

    def _make(
        *,
        rule: str = "Gajakesari Yoga",
        participants: list[str] | None = None,
        id_suffix: str = "default",
        classification: str = "yoga",
    ) -> Finding:
        evidence: list[str] = []
        if participants:
            evidence.append("participants=" + ",".join(participants))
        return Finding(
            id=f"practitioner.yogas_extended.{id_suffix}",
            rule=rule,
            source_sequence=None,
            classification=classification,  # type: ignore[arg-type]
            direction="positive",
            verdict="placeholder",
            evidence=evidence,
            confidence=ConfidenceScore(
                score=0.6,
                votes={"house": True, "lord": True, "karaka": True},
                band="medium",
            ),
        )

    return _make


@pytest.fixture
def make_primitives():
    """Factory for a minimal primitives dict carrying vimsopaka / dignity inputs."""

    def _make(
        *,
        vimsopaka: dict[str, float] | None = None,
        dignity: dict[str, str] | None = None,
        jupiter_aspects: list[str] | None = None,
    ) -> dict:
        return {
            "vimsopaka": vimsopaka or {},
            "dignity": dignity or {},
            "jupiter_aspects": jupiter_aspects or [],
        }

    return _make


# ---------------------------------------------------------------------------
# Spec Section 14 — methodology block
# ---------------------------------------------------------------------------


class TestMethodologyBlock:
    """Auditable docstring block required by Spec Section 14."""

    def test_module_has_methodology_block(self):
        from app.reading.computations import yoga_calibration

        doc = yoga_calibration.__doc__ or ""
        assert "Methodology:" in doc

    def test_module_publishes_prediction_trap_declaration(self):
        from app.reading.computations import yoga_calibration

        doc = yoga_calibration.__doc__ or ""
        assert "Prediction-trap declaration:" in doc

    def test_module_publishes_famous_chart_anti_contamination(self):
        from app.reading.computations import yoga_calibration

        doc = yoga_calibration.__doc__ or ""
        assert "Famous-chart anti-contamination:" in doc

    def test_module_declares_no_fitting_against_outcome_dataset(self):
        """Section 14 mandate: closed-form, no fitting against outcome corpus.

        The module's docstring MUST literally declare that no threshold
        or weight has been fit, tuned, or selected against any dataset
        of historical outcomes. This is the central anti-overreach
        statement.
        """
        from app.reading.computations import yoga_calibration

        doc = yoga_calibration.__doc__ or ""
        lower = doc.lower()
        assert "no threshold or weight" in lower
        assert "fit" in lower
        assert "historical outcomes" in lower

    def test_module_cites_bphs_chapters(self):
        """Constants source must be cited: BPHS Ch.3 (dignity), Ch.27 (drishti)."""
        from app.reading.computations import yoga_calibration

        doc = yoga_calibration.__doc__ or ""
        assert "BPHS" in doc
        # dignity ladder + drishti weights both need a chapter citation
        assert "Ch.3" in doc or "Ch.39" in doc
        assert "Ch.27" in doc


# ---------------------------------------------------------------------------
# Strength scoring
# ---------------------------------------------------------------------------


class TestStrengthScoring:
    """calibrate_yogas attaches a strength_score in [0.0, 1.0] to yoga findings."""

    def test_yoga_finding_gets_strength_score(self, make_yoga_finding, make_primitives):
        from app.reading.computations.yoga_calibration import calibrate_yogas

        finding = make_yoga_finding(
            rule="Gajakesari Yoga",
            participants=["Jupiter", "Moon"],
        )
        prims = make_primitives(
            vimsopaka={"Jupiter": 18.0, "Moon": 16.0},
            dignity={"Jupiter": "exalted", "Moon": "neutral"},
        )
        out = calibrate_yogas([finding], prims)
        assert len(out) == 1
        evidence = " | ".join(out[0].evidence).lower()
        assert "strength_score=" in evidence

    def test_strength_score_is_in_unit_interval(
        self, make_yoga_finding, make_primitives
    ):
        from app.reading.computations.yoga_calibration import calibrate_yogas

        finding = make_yoga_finding(
            participants=["Jupiter", "Moon"],
            id_suffix="unit",
        )
        prims = make_primitives(
            vimsopaka={"Jupiter": 20.0, "Moon": 20.0},
            dignity={"Jupiter": "exalted", "Moon": "exalted"},
        )
        out = calibrate_yogas([finding], prims)
        ev = " | ".join(out[0].evidence)
        # extract the strength score numeric
        import re

        m = re.search(r"strength_score=([0-9.]+)", ev)
        assert m is not None
        score = float(m.group(1))
        assert 0.0 <= score <= 1.0

    def test_exalted_yields_higher_than_debilitated(
        self, make_yoga_finding, make_primitives
    ):
        """Same vimsopaka but better dignity must NEVER lower the strength."""
        from app.reading.computations.yoga_calibration import calibrate_yogas

        good = make_yoga_finding(participants=["Jupiter", "Moon"], id_suffix="good")
        bad = make_yoga_finding(participants=["Jupiter", "Moon"], id_suffix="bad")
        good_prims = make_primitives(
            vimsopaka={"Jupiter": 15.0, "Moon": 15.0},
            dignity={"Jupiter": "exalted", "Moon": "exalted"},
        )
        bad_prims = make_primitives(
            vimsopaka={"Jupiter": 15.0, "Moon": 15.0},
            dignity={"Jupiter": "debilitated", "Moon": "debilitated"},
        )
        good_out = calibrate_yogas([good], good_prims)
        bad_out = calibrate_yogas([bad], bad_prims)
        import re

        good_score = float(
            re.search(r"strength_score=([0-9.]+)", " | ".join(good_out[0].evidence)).group(1)
        )
        bad_score = float(
            re.search(r"strength_score=([0-9.]+)", " | ".join(bad_out[0].evidence)).group(1)
        )
        assert good_score > bad_score

    def test_jupiter_aspect_boost_increases_score(
        self, make_yoga_finding, make_primitives
    ):
        """Per BPHS Ch.27 v.38, Jupiter's full aspect adds a small boost."""
        from app.reading.computations.yoga_calibration import calibrate_yogas

        finding_unaspected = make_yoga_finding(
            participants=["Mercury"], id_suffix="no_jup"
        )
        finding_aspected = make_yoga_finding(
            participants=["Mercury"], id_suffix="with_jup"
        )
        prims_no = make_primitives(
            vimsopaka={"Mercury": 15.0},
            dignity={"Mercury": "neutral"},
            jupiter_aspects=[],
        )
        prims_yes = make_primitives(
            vimsopaka={"Mercury": 15.0},
            dignity={"Mercury": "neutral"},
            jupiter_aspects=["Mercury"],
        )
        out_no = calibrate_yogas([finding_unaspected], prims_no)
        out_yes = calibrate_yogas([finding_aspected], prims_yes)
        import re

        score_no = float(
            re.search(r"strength_score=([0-9.]+)", " | ".join(out_no[0].evidence)).group(1)
        )
        score_yes = float(
            re.search(r"strength_score=([0-9.]+)", " | ".join(out_yes[0].evidence)).group(1)
        )
        assert score_yes > score_no


# ---------------------------------------------------------------------------
# Pass-through behaviour
# ---------------------------------------------------------------------------


class TestPassThrough:
    """Non-yoga findings are returned unchanged."""

    def test_primitive_finding_unchanged(self, make_yoga_finding, make_primitives):
        from app.reading.computations.yoga_calibration import calibrate_yogas

        primitive = make_yoga_finding(
            classification="primitive",
            id_suffix="prim",
        )
        out = calibrate_yogas([primitive], make_primitives())
        assert len(out) == 1
        joined = " | ".join(out[0].evidence)
        assert "strength_score=" not in joined

    def test_yoga_without_participants_yields_default_score(
        self, make_yoga_finding, make_primitives
    ):
        """A yoga whose evidence doesn't list participants gets a neutral score."""
        from app.reading.computations.yoga_calibration import calibrate_yogas

        finding = make_yoga_finding(participants=None, id_suffix="bare")
        out = calibrate_yogas([finding], make_primitives())
        assert len(out) == 1
        # Either no strength_score is attached (silent) OR a neutral
        # default 0.0 is attached. Both are acceptable for v1 as long
        # as the unit-interval invariant is respected.
        ev = " | ".join(out[0].evidence)
        if "strength_score=" in ev:
            import re

            score = float(re.search(r"strength_score=([0-9.]+)", ev).group(1))
            assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Constants discipline
# ---------------------------------------------------------------------------


class TestConstantsDeclared:
    """Dignity multipliers and drishti boost are explicit, doctrine-cited."""

    def test_dignity_multipliers_table_present(self):
        from app.reading.computations import yoga_calibration

        # Module must expose the dignity multiplier mapping for audit.
        assert hasattr(yoga_calibration, "_DIGNITY_MULTIPLIER")
        table = yoga_calibration._DIGNITY_MULTIPLIER
        assert table["exalted"] >= table["own"] >= table["neutral"] >= table["debilitated"]

    def test_drishti_boost_constant_present(self):
        from app.reading.computations import yoga_calibration

        # Module must expose the Jupiter-aspect boost constant for audit.
        assert hasattr(yoga_calibration, "_JUPITER_ASPECT_BOOST")
        assert 0.0 <= yoga_calibration._JUPITER_ASPECT_BOOST <= 0.5


# ---------------------------------------------------------------------------
# Lazy-import regression
# ---------------------------------------------------------------------------


class TestLazyImportDiscipline:
    """No sentence_transformers / torch / knowledge_search at module top."""

    def test_sentence_transformers_not_imported_at_module_top(self):
        import inspect

        from app.reading.computations import yoga_calibration

        src = inspect.getsource(yoga_calibration)
        lines = src.splitlines()
        top_lines: list[str] = []
        in_doc = False
        doc_closed = False
        for line in lines:
            stripped = line.strip()
            if not doc_closed:
                if stripped.startswith('"""') and not in_doc:
                    in_doc = True
                    if stripped.endswith('"""') and len(stripped) > 3:
                        in_doc = False
                        doc_closed = True
                    continue
                if in_doc and stripped.endswith('"""'):
                    in_doc = False
                    doc_closed = True
                    continue
                if in_doc:
                    continue
                doc_closed = True
            if stripped.startswith(("def ", "class ", "async def ")):
                break
            top_lines.append(line)
        top_src = "\n".join(top_lines)
        assert "sentence_transformers" not in top_src
        assert "from app.medini.services" not in top_src
