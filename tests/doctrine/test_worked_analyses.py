"""Guards for the Raman worked-chart-analysis exemplar corpus + few-shot loader (Track C)."""
import hashlib

from app.medini.doctrine import worked_analyses as WA


def test_corpus_loads_and_is_verbatim():
    ex = WA.load_exemplars()
    assert len(ex) >= 80                              # ~83 worked analyses
    for r in ex:
        assert r["analysis_text"] and r["house"] in range(1, 13)
        # sha256 proves the stored prose is unmodified (verbatim, like the compendium)
        assert hashlib.sha256(r["analysis_text"].encode()).hexdigest() == r["sha256"]


def test_exemplars_prefer_requested_house_and_verdict_samples():
    picks = WA.exemplars_for([8], k=2)
    assert len(picks) == 2
    assert picks[0]["house"] == 8                     # matching house ranks first
    # a verdict-bearing exemplar is preferred among matches
    assert any(p.get("verdict_sentences") for p in picks)


def test_exemplar_block_is_style_only_and_grounded():
    block = WA.exemplar_block([8], k=2)
    assert "STYLE EXEMPLARS" in block
    # the block MUST tell the model these are style-only, not chart facts (grounding contract)
    assert "NOT facts about the current chart" in block
    assert "Ground every claim in the engine evidence" in block
    # and it must carry Raman's verbatim prose
    assert "HTJAH" in block


def test_interpreter_wires_exemplars_without_breaking_the_contract():
    from app.medini.doctrine import interpret as I
    # the grounding contract in the system prompt is untouched by Track C
    assert "GROUNDING IS ABSOLUTE" in I._SYSTEM
    # the interpreter imports the exemplar loader (few-shot wiring present)
    import inspect
    src = inspect.getsource(I.interpret_chart)
    assert "exemplar_block" in src and "style_exemplars" in src
