"""
WU-1 invariant: _safe_array is defined in exactly the two modules that call it.

Before WU-1 the service carried seven copy-paste duplicates of this helper, five
of them dead code, each docstring claiming a CLAUDE.md standard that does not
exist. This test pins the definition set so the copy-paste pattern cannot
silently re-emerge: any new definition anywhere in the service fails here with
the offending path named.
"""
import ast
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent.parent

# Exactly two entries because services/corner_analysis.py (27 call sites) and
# services/delta_analysis.py (4 call sites) are the only modules that invoke
# _safe_array. Adding a third entry must be a deliberate, reviewed edit of this
# list — never an accident of copy-paste.
ALLOWED = {
    Path("services") / "corner_analysis.py",
    Path("services") / "delta_analysis.py",
}

# Non-source trees excluded from the walk: the test tree itself, build
# artefacts, and bytecode caches.
EXCLUDED_TOP_LEVEL = {"tests", "build"}


def _files_defining_safe_array():
    found = set()
    for py_file in sorted(SERVICE_ROOT.rglob("*.py")):
        rel = py_file.relative_to(SERVICE_ROOT)
        if rel.parts[0] in EXCLUDED_TOP_LEVEL:
            continue
        if "__pycache__" in rel.parts or ".egg-info" in str(rel):
            continue
        # ast, not regex: a regex would also match docstrings/comments that
        # merely mention the name and give a misleading count.
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name == "_safe_array":
                found.add(rel)
                break
    return found


def test_safe_array_defined_only_in_calling_modules():
    found = _files_defining_safe_array()
    unexpected = sorted(str(p) for p in found - ALLOWED)
    missing = sorted(str(p) for p in ALLOWED - found)
    assert not unexpected and not missing, (
        "_safe_array definition set drifted from the WU-1 allow-list. "
        f"Unexpected definitions in: {unexpected if unexpected else 'none'}. "
        f"Expected but absent from: {missing if missing else 'none'}. "
        "If a new definition is intentional, update ALLOWED in this test "
        "deliberately — do not copy-paste the helper into another module."
    )
