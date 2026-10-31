"""The house audit (app/raman_saab/house_audit.py): it explains the scored judge, never moves it."""
from __future__ import annotations

import json

import pytest

from app.raman_saab import house_audit as ha
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.judges import house_template as ht


@pytest.fixture(scope="module")
def mainpuri():
    """12 Oct 1989, 10:02 IST, Mainpuri: Ketu in Leo but the 9th Bhava, Mercury in the 11th sandhi."""
    return cast_chart(BirthData("mainpuri", 1989, 10, 12, 10, 2, 5.5, 27.23, 79.03), ayanamsa="raman")


@pytest.fixture(scope="module")
def audit10(mainpuri):
    return ha.audit_house(mainpuri, 10)


@pytest.fixture(scope="module")
def audit11(mainpuri):
    return ha.audit_house(mainpuri, 11)


class TestExclusionHook:
    def test_default_is_empty_so_judging_is_unchanged(self) -> None:
        """The hook is off unless the audit sets it; the ratchet runs with it off."""
        assert ht.EXCLUDED_RULES.get() == frozenset()

    def test_excluding_a_rule_removes_it_and_resets(self, mainpuri) -> None:
        """A rule excluded inside the context does not fire; outside it fires again."""
        with ha._excluding(frozenset({"H10.L.11"})):
            ids = {fr.rule.id for sv in ht.judge_house(mainpuri, 10).significations
                   for fr in sv.ledger.fired_benefic}
        assert "H10.L.11" not in ids
        ids = {fr.rule.id for sv in ht.judge_house(mainpuri, 10).significations
               for fr in sv.ledger.fired_benefic}
        assert "H10.L.11" in ids


class TestConditionCheck:
    def test_ketu_in_another_bhava_is_doubtful(self, audit10) -> None:
        """Ketu is in Leo (10th sign) but the 9th Bhava, so H10.P.Ketu rests on a freed house."""
        r = {x.id: x for x in audit10.rules}
        assert r["H10.P.Ketu"].doubts and "9th Bhava" in r["H10.P.Ketu"].doubts[0]
        assert not r["H10.L.11"].doubts

    def test_mercury_in_sandhi_is_doubtful(self, audit11) -> None:
        """Mercury, 0.84 deg from the 11th sandhi, gives no Bhava result (HPA-24:98-100)."""
        r = {x.id: x for x in audit11.rules}
        assert "sandhi" in r["H11.P.Mercury"].doubts[0]
        assert not r["H11.P.Sun"].doubts

    def test_or_with_a_firm_arm_holds(self, mainpuri) -> None:
        """An Or survives when one arm (the Sun, firmly in the 11th) holds without the doubtful one."""
        ctx = C.EvalContext(mainpuri)
        assert ha._firm(C.Or(C.InRashiHouse("Mercury", 11), C.InRashiHouse("Sun", 11)), mainpuri, ctx)
        assert not ha._firm(C.And(C.InRashiHouse("Mercury", 11), C.InRashiHouse("Sun", 11)), mainpuri, ctx)


class TestRobustness:
    def test_tenth_does_not_rest_on_the_doubtful_ketu(self, audit10) -> None:
        """Without the Ketu rules the 10th still reads favourable."""
        assert audit10.verdict == "favourable" and audit10.robust_verdict == "favourable"

    def test_eleventh_does_not_rest_on_the_sandhi_mercury(self, audit11) -> None:
        """Without the sandhi-Mercury rules the 11th still reads favourable."""
        assert audit11.verdict == "favourable" and audit11.robust_verdict == "favourable"


def _golden_ledgers():
    for rec_id, house, *_ in ha.precedent_index()[::7]:
        yield rec_id, house


class TestWeighingTrace:
    def test_clause_words_agree_with_the_judge_on_goldens(self) -> None:
        """Each clause the audit names implies a base verdict; unshifted, it equals the judge's."""
        recs = {}
        for line in ha.GOLDENS_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                rec = json.loads(line)
                recs[rec["id"]] = rec
        checked = 0
        for rec_id, house in sorted(set(_golden_ledgers())):
            chart = ha._golden_chart(recs[rec_id])
            for sv in ht.judge_house(chart, house).significations:
                L = sv.ledger
                clause, verdict = ha.decide_clause(L)
                if "Navamsa then moved" in clause or "LONGEVITY_GUARD" in L.flags:
                    continue
                if clause.startswith("clause 1.5"):
                    base = "afflicted"
                elif clause.startswith("clause 1,"):
                    base = "afflicted"
                elif clause.startswith("clause 2"):
                    base = ("afflicted" if "afflict" in clause.rsplit(":", 1)[-1]
                            else "favourable" if clause.endswith("lift it") else "mixed")
                elif clause.startswith("clause 5"):
                    base = "favourable"
                elif clause.startswith("clause 6"):
                    base = "mixed" if ("rescues" in clause or "salvages" in clause) else "afflicted"
                elif clause.startswith("clause 7"):
                    base = "insufficient-evidence"
                elif clause.startswith("clause 8"):
                    base = "mixed"
                else:
                    continue                                  # clause 3: polarity, not pillars
                assert base == verdict, (rec_id, house, sv.signification, clause, verdict)
                checked += 1
        assert checked > 50


class TestPrecedents:
    def test_index_reads_confirmed_conclusions(self) -> None:
        """The index holds Raman's CONFIRMED worked-example verdicts only."""
        idx = ha.precedent_index()
        assert len(idx) > 300
        assert {v for _, _, v, _, _ in idx} <= {"favourable", "mixed", "afflicted"}

    def test_a_golden_chart_is_never_its_own_precedent(self) -> None:
        """Auditing a golden chart excludes its own record from the comparison."""
        rec_id, house, *_ = ha.precedent_index()[0]
        recs = [json.loads(l) for l in ha.GOLDENS_PATH.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")]
        rec = next(r for r in recs if r["id"] == rec_id)
        _, sims = ha.precedents_for(ha._golden_chart(rec), house, exclude=rec_id)
        assert rec_id not in {s.record for s in sims}


class TestStabilityAndCli:
    def test_stability_has_six_offsets(self, audit10) -> None:
        """The 10th is re-judged at -20..+20 minutes and reads favourable throughout."""
        assert [m for m, _ in audit10.stability] == list(ha.STABILITY_MINUTES)
        assert {v for _, v in audit10.stability} == {"favourable"}

    def test_cli_markdown(self, capsys) -> None:
        """The command prints a markdown audit for the houses asked."""
        ha.main(["--date", "1989-10-12", "--time", "10:02", "--tz", "5.5", "--lat", "27.23",
                 "--lon", "79.03", "--houses", "10", "--no-stability"])
        out = capsys.readouterr().out
        assert "## The 10th house (lord Sun): favourable in 6 of 6 matters" in out
        assert "H10.P.Ketu" in out


@pytest.fixture(scope="module")
def kanpur():
    """10 Oct 1989, 15:15 IST, Kanpur: the chart whose 10th led the 2026-10-30 diagnosis."""
    return cast_chart(BirthData("kanpur", 1989, 10, 10, 15, 15, 5.5, 26.4499, 80.3319),
                      ayanamsa="raman")


class TestMatterBreakdown:
    def test_one_afflicted_matter_is_named_not_hidden(self, kanpur) -> None:
        """Kanpur's 10th rolls up afflicted on one matter; the breakdown names it beside the rest."""
        pf = ht.judge_house(kanpur, 10)
        assert pf.rollup == "afflicted"
        b = ht.matter_breakdown(pf)
        assert b.startswith("favourable in 4 of 6 matters")
        assert "afflicted in 1 (profession_trade)" in b

    def test_breakdown_counts_every_matter(self, mainpuri) -> None:
        """Every signification is counted once; the breakdown re-reads, never re-decides."""
        for h in range(1, 13):
            pf = ht.judge_house(mainpuri, h)
            b = ht.matter_breakdown(pf)
            import re
            assert sum(int(x) for x in re.findall(r" in (\d+)", b)) == len(pf.significations)
