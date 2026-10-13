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

    def test_new_records_can_chain_after_each_other_in_spec_order(self) -> None:
        """A split often yields several clauses from one entry; they must land in reading order."""
        base = {"house": 6, "signification": "enemies_disease", "kind": "descriptive",
                "slot": "general", "src": 6039, "work": "HTJAH-I", "polarity": "neutral"}
        src = apply(_FILE, changes={}, new=[
            dict(base, id="H6.L.8x", after="H6.L.8", text="first"),
            dict(base, id="H6.L.8y", after="H6.L.8x", text="second"),
        ])
        ids = list(_rules(src))
        i = ids.index("H6.L.8")
        assert ids[i + 1:i + 3] == ["H6.L.8x", "H6.L.8y"]

    def test_a_parked_record_can_be_promoted_to_a_live_rule(self) -> None:
        """Turning a descriptive record evaluable needs its kind, condition and text changed
        together; the condition is written as code, the kind as a string."""
        src = apply(_FILE, changes={"H6.L.2b": {
            "kind": "evaluable",
            "condition": 'C.And(C.LordIn(6, 2), C.IsWeak("Venus"))',
            "afflicted": "Venus weak - celibate and poverty stricken"}}, new=[])
        r = _rules(src)["H6.L.2b"]
        assert r.kind == "evaluable" and r.condition is not None
        assert r.afflicted == "Venus weak - celibate and poverty stricken"

    def test_a_removed_record_leaves_a_comment_and_its_heir_takes_its_place(self) -> None:
        """Removal keeps the reason in the file, and children anchored after it still land there."""
        base = {"house": 6, "signification": "enemies_disease", "kind": "descriptive",
                "slot": "general", "src": 6039, "work": "HTJAH-I", "polarity": "neutral"}
        src = apply(_FILE, changes={}, new=[dict(base, id="H6.L.8x", after="H6.L.8", text="heir")],
                    delete={"H6.L.8": "every sentence moved to its own record"})
        recs = _rules(src)
        assert "H6.L.8" not in recs and "H6.L.8x" in recs
        assert "H6.L.8 REMOVED: every sentence moved to its own record" in src

    def test_replacing_text_containing_multibyte_characters_keeps_the_comma(self, tmp_path) -> None:
        """AST columns are UTF-8 bytes. A slot holding an arrow once made the cut land two
        characters late and eat the trailing comma; the result must parse and read back exactly."""
        f = tmp_path / "rules.py"
        f.write_text("\n".join([
            "from app.raman_saab.doctrine import conditions as C",
            "from app.raman_saab.doctrine.rules import RuleRecord",
            "from app.raman_saab.doctrine.sources import Citation",
            "RULES = (",
            "    RuleRecord(",
            '        id="T.L.1", house=3, signification="siblings", group="lord_in_house",',
            '        kind="evaluable", condition=C.LordIn(3, 3),',
            '        fortified="one → two — three",',
            "        afflicted=None,",
            '        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3348)),',
            ")",
            ""]), encoding="utf-8")
        recs = _rules(apply(f, changes={"T.L.1": {"fortified": "plain replacement"}}, new=[]))
        assert recs["T.L.1"].fortified == "plain replacement"
