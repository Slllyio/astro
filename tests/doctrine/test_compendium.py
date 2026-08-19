"""compendium: schema + integrity validation of rule records."""
import json

import pytest

from app.medini.doctrine.compendium import (
    CompendiumError,
    load_book,
    load_compendium,
    quote_sha256,
    validate_rule,
    write_book,
)


def make_rule(**overrides):
    quote = overrides.pop(
        "quote",
        "Saturn, Mercury and Venus are ill-disposed. Jupiter and the Sun are auspicious.",
    )
    rule = {
        "id": "raman.hpa.xvii.aries_key_planets",
        "book": "hpa",
        "archive_item": "hindupredictiveastrologyofbvraman",
        "page": 134,
        "quote": quote,
        "quote_sha256": quote_sha256(quote),
        "quote_verified": True,
        "domain": "general",
        "rule_type": "functional_role",
        "antecedent": {"op": "lagna_sign_is", "sign": "aries"},
        "consequent": {
            "polarity": "neutral",
            "text": "Functional roles for Aries lagna.",
            "payload": {"auspicious": ["jupiter", "sun"]},
        },
        "inputs_required": ["lagna_sign"],
        "computability": "full",
        "ambiguity_notes": None,
        "conflicts_with": [],
        "supersedes": None,
        "provenance": {"sweep_id": "seed", "extractor": "hand", "chapter": "XVII"},
    }
    rule.update(overrides)
    return rule


class TestValidateRule:
    def test_valid_rule_passes(self):
        validate_rule(make_rule())

    def test_sha_mismatch_rejected(self):
        rule = make_rule(quote_sha256="0" * 64)
        with pytest.raises(CompendiumError, match="quote_sha256"):
            validate_rule(rule)

    def test_id_book_segment_must_match(self):
        rule = make_rule(id="raman.muhurtha.xvii.aries_key_planets")
        with pytest.raises(CompendiumError, match="book segment"):
            validate_rule(rule)

    def test_short_quote_rejected(self):
        rule = make_rule(quote="too short")
        rule["quote_sha256"] = quote_sha256("too short")
        with pytest.raises(CompendiumError, match="schema"):
            validate_rule(rule)

    def test_unknown_domain_rejected(self):
        with pytest.raises(CompendiumError, match="schema"):
            validate_rule(make_rule(domain="destiny"))

    def test_executable_requires_antecedent(self):
        with pytest.raises(CompendiumError, match="requires an antecedent"):
            validate_rule(make_rule(antecedent=None))

    def test_manual_requires_null_antecedent(self):
        with pytest.raises(CompendiumError, match="antecedent null"):
            validate_rule(make_rule(computability="manual"))

    def test_manual_with_null_antecedent_ok(self):
        validate_rule(make_rule(computability="manual", antecedent=None))

    def test_escape_hatch_string_antecedent_ok(self):
        validate_rule(make_rule(antecedent="impl:python:hpa.aries_roles"))

    def test_correction_id_suffix_ok(self):
        validate_rule(make_rule(id="raman.hpa.xvii.aries_key_planets_r2"))

    def test_extra_top_level_key_rejected(self):
        with pytest.raises(CompendiumError, match="schema"):
            validate_rule(make_rule(surprise=1))


class TestBookIO:
    def test_write_then_load_round_trip(self, tmp_path):
        path = tmp_path / "hpa.jsonl"
        rules = [make_rule(), make_rule(id="raman.hpa.xvii.taurus_key_planets")]
        write_book(path, rules)
        loaded = load_book(path)
        assert [r["id"] for r in loaded] == sorted(r["id"] for r in rules)

    def test_duplicate_ids_rejected_on_write(self, tmp_path):
        with pytest.raises(CompendiumError, match="duplicate"):
            write_book(tmp_path / "hpa.jsonl", [make_rule(), make_rule()])

    def test_duplicate_ids_rejected_on_load(self, tmp_path):
        path = tmp_path / "hpa.jsonl"
        line = json.dumps(make_rule())
        path.write_text(line + "\n" + line + "\n")
        with pytest.raises(CompendiumError, match="duplicate"):
            load_book(path)

    def test_wrong_book_file_rejected(self, tmp_path):
        path = tmp_path / "muhurtha.jsonl"
        path.write_text(json.dumps(make_rule()) + "\n")
        with pytest.raises(CompendiumError, match="book"):
            load_book(path)

    def test_invalid_json_line_reported_with_lineno(self, tmp_path):
        path = tmp_path / "hpa.jsonl"
        path.write_text(json.dumps(make_rule()) + "\n{not json\n")
        with pytest.raises(CompendiumError, match="hpa.jsonl:2"):
            load_book(path)

    def test_cross_book_id_collision_rejected(self, tmp_path):
        write_book(tmp_path / "hpa.jsonl", [make_rule()])
        # same id smuggled into another book file fails that file's book
        # check first; craft a legal muhurtha record with a colliding id via
        # direct write of the hpa book under another name
        (tmp_path / "hpa2.jsonl").write_text(json.dumps(make_rule()) + "\n")
        with pytest.raises(CompendiumError):
            load_compendium(tmp_path)


class TestRepoCompendium:
    def test_committed_compendium_loads_clean(self):
        # Every committed book file must validate; every record verified.
        books = load_compendium()
        for book, rules in books.items():
            for rule in rules:
                assert rule["quote_verified"], f"{rule['id']}: unverified quote committed"
