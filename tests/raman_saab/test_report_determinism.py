"""The report is byte-stable — the same chart renders the same bytes in any process.

This is not a style preference. The golden ratchet, every "did this refactor move a verdict"
diff, and every regression snapshot rest on the report being a pure function of the chart. One
line that changes between runs makes all of them unreliable, and it hid for a long time because
it only shows when two PROCESSES are compared, never two calls in one.

Found by diffing two charts' full markdown before and after a caching change: everything matched
except a yoga's `Computation` line, which renders a condition's arguments and interpolated a
`frozenset` straight into an f-string — iteration order there follows the interpreter's
per-process string-hash seed.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys

from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.yoga_deep_read import _describe_value, describe

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


class TestSetsRenderInAStableOrder:
    def test_a_set_argument_is_sorted(self):
        """The exact failure: `states={'moolatrikona', 'own'}` in one process and
        `states={'own', 'moolatrikona'}` in the next."""
        assert _describe_value({"own", "moolatrikona"}) == "{'moolatrikona', 'own'}"
        assert _describe_value(frozenset({"own", "moolatrikona"})) == "{'moolatrikona', 'own'}"

    def test_the_two_orderings_render_identically(self):
        """Built from the same members in opposite insertion order, they must not differ."""
        assert _describe_value({"a", "b", "c"}) == _describe_value({"c", "b", "a"})

    def test_a_non_set_value_is_untouched(self):
        """Only sets were unstable; nothing else changes, so no other line moves."""
        assert _describe_value(7) == "7"
        assert _describe_value("Mars") == "Mars"
        assert _describe_value((5, 9)) == "(5, 9)"

    def test_a_condition_carrying_a_set_describes_stably(self):
        one = describe(C.HasDignity("Sun", {"own", "moolatrikona"}))
        two = describe(C.HasDignity("Sun", {"moolatrikona", "own"}))
        assert one == two
        assert "moolatrikona" in one and "own" in one


class TestTheWholeReportIsStableAcrossProcesses:
    def test_the_same_chart_hashes_the_same_under_different_hash_seeds(self):
        """The only check that can actually catch this class of bug: `PYTHONHASHSEED` is fixed
        within a process, so two runs in ONE interpreter agree even when the report is
        unstable. Two interpreters with different seeds do not."""
        code = (
            "from app.raman_saab.chart.model import BirthData;"
            "from app.raman_saab.detailed_report import build_detailed_report, to_markdown;"
            "import hashlib;"
            "m=to_markdown(build_detailed_report("
            "BirthData('Canonical Test',1990,7,15,12,0,5.5,12.97,77.59)));"
            "print(hashlib.sha256(m.encode()).hexdigest())")
        # Anchor the child on the repo root derived from __file__, not on the parent's cwd.
        # `PYTHONPATH: "."` resolves against wherever pytest was launched, so running the
        # suite from a subdirectory made the child fail to import app.raman_saab — an import
        # error reported as a determinism failure. It also discarded any inherited PYTHONPATH.
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[2]
        inherited = os.environ.get("PYTHONPATH", "")
        digests = []
        for seed in ("1", "12345"):
            env = {**os.environ, "PYTHONHASHSEED": seed,
                   "PYTHONPATH": os.pathsep.join(x for x in (str(root), inherited) if x)}
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               env=env, cwd=str(root), timeout=900)
            assert r.returncode == 0, r.stderr[-2000:]
            digests.append(r.stdout.strip())
        assert digests[0] and digests[0] == digests[1], digests

    def test_two_builds_in_one_process_also_agree(self):
        """Cheap companion: catches ordinary state leaks between builds — a cache that carried
        one chart's values into the next would fail here even though the seeds match."""
        from app.raman_saab.detailed_report import build_detailed_report, to_markdown
        first = to_markdown(build_detailed_report(_CANONICAL))
        second = to_markdown(build_detailed_report(_CANONICAL))
        assert hashlib.sha256(first.encode()).hexdigest() == \
            hashlib.sha256(second.encode()).hexdigest()
