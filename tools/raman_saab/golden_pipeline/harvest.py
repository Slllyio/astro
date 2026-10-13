"""Harvest golden-reviewer answers verbatim from Claude Code subagent transcripts.

Each reviewer's final SubagentHandback message is written unchanged to
answers/<packet>.json, so no answer is ever hand-copied. Re-reviews of the same packet:
the latest transcript (by mtime) wins.

Usage:
    py -3.12 -m tools.raman_saab.golden_pipeline.harvest <session_subagents_dir> <run_dir>
    (subagents dir: ~/.claude/projects/<project>/<session-id>/subagents)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
sub, run = Path(sys.argv[1]), Path(sys.argv[2])
latest = {}
for f in sorted(sub.glob("agent-*.jsonl"), key=lambda p: p.stat().st_mtime):
    path = final = None
    for line in f.read_text(encoding="utf-8").splitlines():
        try: m = json.loads(line)
        except json.JSONDecodeError: continue
        msg = m.get("message") or {}
        content = msg.get("content")
        texts = [content] if isinstance(content, str) else [c.get("text", "") for c in (content or []) if isinstance(c, dict) and c.get("type") == "text"]
        for t in texts:
            if path is None and msg.get("role") == "user":
                mm = re.search(r"Review the packet at:\s*(\S+\.md)", t)
                if mm: path = mm.group(1)
            pass
        for c in (content if isinstance(content, list) else []):
            if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "SubagentHandback":
                final = c["input"].get("message", "")
    if path and final and str(run.name) in path:
        latest[Path(path).name] = final          # later mtime wins (re-reviews)
n = 0
for name, text in latest.items():
    m = re.search(r"\{.*\}", text, re.S)
    if not m: print("NO JSON:", name); continue
    (run / "answers" / name.replace(".md", ".json")).write_text(m.group(0), encoding="utf-8"); n += 1
print(n, "answers harvested")
