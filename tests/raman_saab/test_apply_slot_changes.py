"""The slot-change applier edits real rule files by id, and reads back exactly what was asked."""
from __future__ import annotations

import ast
from pathlib import Path

from tools.raman_saab.apply_slot_changes import apply, literal

_FILE = Path(__file__).resolve().parents[2] / "app/raman_saab/doctrine/rule_sets/house_06_ari/lord_in_12.py"


def _rules(src: str) -> dict:
    ns: dict = {}
    exec(compile(src, "<edited>", "exec"), ns)
    return {r.id: r for r in ns["RULES"]}


class TestApplySlotChanges:
    def test_replace_insert_clear_and_append_round_trip_exactly(self) -> None:
        """Every edit shape the sweep needs, on a real file, read back through Python itself."""
        long_text = ("the 6th lord well fortified — " + "a long reading that must wrap " * 6).strip()
        src = apply(_FILE,
                    changes={
                        "H6.L.8": {"fortified": long_text, "note": "test note"},  # replace
                        "H6.L.12": {"general": "inserted base reading"},           # insert kw
                        "H6.L.10": {"afflicted": None},                            # clear
                    },
                    new=[{"id": "H6.L.8z", "after": "H6.L.8", "house": 6,
                          "signification": "enemies_disease", "kind": "descriptive",
                          "slot": "general", "text": "a re-homed clause", "src": 6039,
                          "work": "HTJAH-I", "polarity": "neutral"}])
        recs = _rules(src)
        assert recs["H6.L.8"].fortified == long_text
        assert recs["H6.L.12"].general == "inserted base reading"
        assert recs["H6.L.10"].afflicted is None
        assert recs["H6.L.8z"].general == "a re-homed clause"
        assert recs["H6.L.8z"].polarity == "neutral"
        # untouched records are untouched
        original = _rules(_FILE.read_text(encoding="utf-8"))
        key = lambda r: (r.general, r.fortified, r.afflicted, r.polarity, r.source)
        assert key(recs["H6.L.1"]) == key(original["H6.L.1"])  # Conditions compare by identity
        # the new record sits immediately after its anchor
        ids = list(recs)
        assert ids.index("H6.L.8z") == ids.index("H6.L.8") + 1

    def test_an_unknown_rule_id_raises_and_writes_nothing(self) -> None:
        """A typo in a spec must fail loudly, not silently skip a reviewed change."""
        try:
            apply(_FILE, changes={"H6.L.99": {"general": "x"}}, new=[])
        except KeyError as exc:
            assert "H6.L.99" in str(exc)
        else:
            raise AssertionError("expected KeyError")

    def test_wrapped_literals_never_fuse_words(self) -> None:
        """Adjacent literals concatenate with no separator; each chunk must carry its space."""
        text = " ".join(["word"] * 60)
        expr = literal(text, 8)
        assert expr.count("\n") >= 1
        assert ast.literal_eval(f"({expr})") == text
