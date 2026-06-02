import ast, pathlib

FORBIDDEN = {"app.core.bhava_judge","app.core.reading_composer","app.core.drishti_argala",
             "app.core.yogas","app.core.shadbala"}
PKG = pathlib.Path(__file__).resolve().parents[2] / "app" / "raman_saab"

def _imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {n.name for n in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
            if node.module.startswith("app.core.dkp"):  # dkp_* family
                mods.add("app.core.dkp_*")
    return mods

def test_no_forbidden_core_imports():
    offenders = {}
    for f in PKG.rglob("*.py"):
        mods = _imports(f)
        bad = mods & FORBIDDEN | {m for m in mods if m.startswith("app.core.dkp")}
        if bad:
            offenders[str(f)] = bad
    assert not offenders, f"forbidden app/core imports: {offenders}"
