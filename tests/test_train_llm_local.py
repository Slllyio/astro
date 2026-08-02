"""Tests for the Phase-3 local trainer + evaluator (stateless logic only — no model
download, no GPU: dataset loading, completion-only label masking via a fake tokenizer,
hold-out hashing, and prompt->Evidence reconstruction)."""
from __future__ import annotations

import json
from collections import Counter

import pytest

from app.medini.ml.eval_analysis_llm import evidence_from_prompt, is_holdout, score
from app.medini.ml.train_llm_local import (assert_grounded_rows_survive, drop_holdout,
                                           encode_row, load_rows)


class _FakeTokenizer:
    """Minimal chat-templating tokenizer: 1 token per whitespace word."""
    eos_token = "<eos>"

    def apply_chat_template(self, msgs, tokenize=True, add_generation_prompt=False):
        text = " ".join(m["content"] for m in msgs) + (" <gen>" if add_generation_prompt else "")
        return list(range(len(text.split())))

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": list(range(1000, 1000 + len(text.split())))}


class TestEncodeRow:
    def test_prompt_tokens_are_masked_completion_carries_loss(self):
        """Only completion tokens train (labels != -100); prompt labels are all -100."""
        row = {"system": "sys words here", "prompt": "the user prompt",
               "completion": "the model answer text", "_meta": {"weight": 3}}
        ids, labels, weight = encode_row(row, _FakeTokenizer(), max_len=512)
        n_prompt = len(_FakeTokenizer().apply_chat_template(
            [{"role": "system", "content": row["system"]},
             {"role": "user", "content": row["prompt"]}], add_generation_prompt=True))
        assert labels[:n_prompt] == [-100] * n_prompt
        assert all(l != -100 for l in labels[n_prompt:])
        assert len(ids) == len(labels)
        assert weight == 3.0

    def test_max_len_truncates_consistently(self):
        row = {"system": "s", "prompt": "p " * 30, "completion": "c " * 50, "_meta": {}}
        ids, labels, _ = encode_row(row, _FakeTokenizer(), max_len=40)
        assert len(ids) == 40 and len(labels) == 40

    def test_prompt_swallowing_max_len_skips_the_row(self):
        """If truncation leaves no completion token, the row is skipped (None) — an
        all-masked row produces NaN loss (the CPU-smoke bug of 2026-07-28)."""
        row = {"system": "s", "prompt": "p " * 50, "completion": "c " * 50, "_meta": {}}
        assert encode_row(row, _FakeTokenizer(), max_len=20) is None


class TestLoadRows:
    def test_malformed_rows_are_dropped_loudly(self, tmp_path):
        p = tmp_path / "d.jsonl"
        p.write_text(json.dumps({"system": "s", "prompt": "p", "completion": "c"}) + "\n"
                     + "not json\n"
                     + json.dumps({"prompt": "", "completion": "c"}) + "\n",
                     encoding="utf-8")
        rows = load_rows(p)
        assert len(rows) == 1


class TestHoldoutExclusion:
    """2026-08-02: the eval has always held out ~1/8 of teacher rows by a person_id hash and its
    docstring has always said training must exclude the same rows — but training read every row,
    so the student was fine-tuned on its own eval set and every reported score measured
    memorisation. 74 of 588 teacher rows were leaking on the corpus that trained the last model."""

    def _rows(self):
        teacher_held = next(p for p in (f"P:{i}" for i in range(500)) if is_holdout(p))
        teacher_train = next(p for p in (f"P:{i}" for i in range(500)) if not is_holdout(p))
        mk = lambda pid, src: {"prompt": "p", "completion": "c",                # noqa: E731
                               "_meta": {"person_id": pid, "source": src}}
        return [mk(teacher_held, "teacher"), mk(teacher_train, "teacher"),
                mk(teacher_held, "raman_voice")], teacher_held, teacher_train

    def test_held_out_teacher_rows_are_removed(self):
        rows, held, train_pid = self._rows()
        kept, dropped = drop_holdout(rows)
        assert dropped == 1
        assert [r["_meta"]["person_id"] for r in kept
                if r["_meta"]["source"] == "teacher"] == [train_pid]

    def test_voice_anchors_are_never_held_out(self):
        """Style supervision is never evaluated, so excluding it would only shrink training."""
        rows, held, _ = self._rows()
        kept, _dropped = drop_holdout(rows)
        assert any(r["_meta"]["source"] == "raman_voice" and r["_meta"]["person_id"] == held
                   for r in kept)


class TestGroundedRowsSurvive:
    """2026-08-02, caught mid-run: teacher prompts grew to ~3.1k tokens after the Phase-7 evidence
    decomposition, so at the old max_len=2048 default all 214 teacher rows lost their supervised
    tokens and training proceeded on the 426 voice anchors alone — a pure-style student with no
    grounding supervision, signalled by a single warning line."""

    def test_aborts_when_only_voice_rows_survive(self):
        all_src = Counter({"teacher": 214, "raman_golden_voice": 389, "raman_voice": 37})
        skipped = Counter({"teacher": 214})
        with pytest.raises(SystemExit, match="drops EVERY grounded row"):
            assert_grounded_rows_survive(all_src, skipped, max_len=2048)

    def test_allows_a_partial_skip_that_keeps_grounded_rows(self):
        """Losing some teacher rows to length is a tuning warning, not a corrupt run."""
        all_src = Counter({"teacher": 214, "raman_golden_voice": 389})
        assert_grounded_rows_survive(all_src, Counter({"teacher": 40}), max_len=3072) is None

    def test_no_skips_is_always_fine(self):
        assert_grounded_rows_survive(Counter({"teacher": 10}), Counter(), max_len=4096)


class TestCompletionLoss:
    """2026-08-02: `labels=` made transformers materialise logits for ALL ~3.4k positions and
    upcast them to fp32 (3400 x 151936 x 4 = 2.03 GB), OOMing the 16GB card. Loss is computed over
    the completion tail only, so the alignment between the kept logit window and the labels must
    be pinned — an off-by-one here trains the model to predict the wrong token, silently."""

    def test_perfectly_predicted_completion_has_near_zero_loss(self):
        import torch

        from app.medini.ml.train_llm_local import completion_loss
        vocab, n_sup = 7, 3
        labels = torch.tensor([[-100, -100, -100, 4, 5, 6]])       # prompt masked, tail supervised
        logits = torch.zeros(1, n_sup + 1, vocab)
        for i, tok in enumerate((4, 5, 6)):                         # window position i predicts it
            logits[0, i, tok] = 50.0
        assert completion_loss(logits, labels, n_sup).item() < 1e-3

    def test_shifting_the_prediction_by_one_is_penalised(self):
        """Guards the alignment itself: predicting each NEXT label one slot early must score badly."""
        import torch

        from app.medini.ml.train_llm_local import completion_loss
        vocab, n_sup = 7, 3
        labels = torch.tensor([[-100, -100, -100, 4, 5, 6]])
        logits = torch.zeros(1, n_sup + 1, vocab)
        for i, tok in enumerate((5, 6, 4)):
            logits[0, i, tok] = 50.0
        assert completion_loss(logits, labels, n_sup).item() > 10.0


class TestOllamaBaseTag:
    """A LoRA adapter is only meaningful on the base it trained against, but the Modelfile writer
    hard-coded `FROM qwen2.5:1.5b` regardless of --base-model — so a 3B run would emit a Modelfile
    pairing the 1.5B base with a 3B adapter, which Ollama accepts and then serves as garbage."""

    def test_tag_follows_the_trained_base(self, tmp_path):
        from app.medini.ml.train_llm_local import _write_modelfile
        _write_modelfile(tmp_path, "Qwen/Qwen2.5-3B-Instruct")
        assert "FROM qwen2.5:3b" in (tmp_path / "Modelfile").read_text(encoding="utf-8")

    def test_unknown_base_aborts_rather_than_guessing(self):
        from app.medini.ml.train_llm_local import ollama_tag_for
        with pytest.raises(SystemExit, match="no Ollama base tag known"):
            ollama_tag_for("meta-llama/Llama-3-8B-Instruct")


class TestEval:
    def test_holdout_is_stable(self):
        """The same person_id always lands on the same side of the split."""
        assert is_holdout("ADB:x") == is_holdout("ADB:x")
        picks = {pid: is_holdout(pid) for pid in (f"P:{i}" for i in range(200))}
        frac = sum(picks.values()) / len(picks)
        assert 0.05 < frac < 0.25                       # ~2/16 of the hash space

    def test_evidence_reconstruction_and_scoring(self):
        """Fact lines in the prompt become scorable Evidence; a cited, decree-free answer
        passes the same guard the serving path applies."""
        prompt = "[Fact 1] The Lagna is Virgo.\n[Fact 2] The ruler is Mercury.\n"
        ev = evidence_from_prompt(prompt)
        assert [f.n for f in ev.facts] == [1, 2]
        good = score("The engine reads the Lagna as Virgo [Fact 1]. " * 5, ev, 0.6)
        assert good["passes"] is True
        bad = score("You will marry in 2027 [Fact 1].", ev, 0.6)
        assert bad["passes"] is False

    def test_crisp_ok_is_independent_of_guard_passing(self):
        """2026-07-29 crispness fix: the guard alone never judged length — a maximally
        verbose, jargon-dense answer could pass guard_pass_rate perfectly. `crisp_ok` is a
        SEPARATE check: an answer can pass the guard but fail crisp_ok (too long), or vice
        versa isn't possible (crisp_ok never blocks passes, it's reported independently)."""
        prompt = "[Fact 1] The Lagna is Virgo.\n"
        ev = evidence_from_prompt(prompt)
        short = score("The engine reads the Lagna as Virgo [Fact 1].", ev, 0.6, max_words=220)
        assert short["passes"] is True and short["crisp_ok"] is True

        long_text = "The engine reads the Lagna as Virgo [Fact 1]. " + ("word " * 250)
        long = score(long_text, ev, 0.6, max_words=220)
        assert long["passes"] is True                    # still grounded/decree-free
        assert long["crisp_ok"] is False                  # but over the word budget
        assert long["words"] > 220

    def test_failure_row_carries_every_key_the_report_reads(self):
        """A candidate that errors must still produce a scoreable row. The failure path used to
        omit the citation keys, so a model failing every call (gemma4:12b returning empty, live
        2026-08-03) crashed the aggregation with KeyError and threw away the whole run."""
        from app.medini.ml.eval_analysis_llm import evidence_from_prompt, score
        real = score("The engine reads the Lagna as Virgo [Fact 1].",
                     evidence_from_prompt("[Fact 1] The Lagna is Virgo.\n"), 0.6)
        failure = {"passes": False, "reason": "client: boom", "grounding": 0.0, "anchors": 0,
                   "chars": 0, "words": 0, "crisp_ok": False, "cite_ok": False,
                   "mis_attributed": 0, "unsupported": 0, "checked_sentences": 0}
        assert set(real) == set(failure)

    def test_max_words_default_matches_corpus_ceiling(self):
        from app.medini.ml.build_analysis_corpus import MAX_WORDS
        from app.medini.ml.eval_analysis_llm import MAX_WORDS_DEFAULT
        assert MAX_WORDS_DEFAULT == MAX_WORDS
