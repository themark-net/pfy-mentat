#!/usr/bin/env python3
"""G0 gate: no encoded or sharded source in the operator surface. Stdlib only.

FAIL if any *tracked* file under scripts/, pfy, gui/ is:
  1. a payload/shard by name  (*.b64*, *.payload.*, *_body_NN.py, *_p0.py/_p1a.py style parts)
  2. a runtime assembler      (decodes base64 / gunzips / concatenates parts and then
                               exec()s, compile()s, or runs the result)

Why: scripts/pfy was a 9-line stub decoding gzip+base64 shards, and pfy-board.py /
pfy-gui.py / pfy_enterable_162_b.py concatenated byte-split parts at import time
(2026-09-03..06). That defeats diff, review, grep and blame and contradicts
"receipts over vibes". See docs/ops/critical-review-2026-09-20.md and OQ-0014.

Usage:
  python3 scripts/check_no_encoded_payloads.py            # gate (exit 0/1)
  python3 scripts/check_no_encoded_payloads.py --selftest # classifier fixtures
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ("scripts", "pfy", "gui")
SELF = Path(__file__).resolve()

NAME_PATTERNS = (
    "*.b64",
    "*.b64.*",
    "*.payload.*",
    "*_body_[0-9][0-9].py",
    "*_p[0-9].py",
    "*_p[0-9][a-z].py",
)

# A file is an assembler when it DECODES/ASSEMBLES and then EXECUTES the result.
DECODE_RE = re.compile(
    r"base64\s+(-d|--decode)|b64decode\s*\(|gzip\s+-dc|gunzip|zlib\.decompress\s*\("
)
ASSEMBLE_RE = re.compile(
    r"""glob\(\s*["'][^"']*(_body_|_part|\.payload|\.b64)[^"']*["']\s*\)"""
    r"""|\.read_text\([^)]*\)\s*for\s+\w+\s+in\s+(parts|_parts)"""
    r"""|"".join\(\s*(_parts|parts)\s*\)"""
)
EXECUTE_RE = re.compile(
    r"""\bexec\s*\(\s*compile\s*\(|\bexec\s+bash\s+"?\$\w*BODY|\bexec\s+"?\$BODY|\bsource\s+"?\$BODY"""
    r"""|\bexec\s*\(\s*(body|_body)\b"""
)

TEXT_MAX_BYTES = 2_000_000


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--", *SCOPES],
            cwd=ROOT, capture_output=True, check=True,
        ).stdout
        rels = [r for r in out.decode("utf-8", "replace").split("\0") if r]
    except (subprocess.CalledProcessError, FileNotFoundError):
        rels = []
        for scope in SCOPES:
            p = ROOT / scope
            if p.is_file():
                rels.append(scope)
            elif p.is_dir():
                rels += [str(q.relative_to(ROOT)) for q in p.rglob("*") if q.is_file()]
    return [ROOT / r for r in rels if "node_modules" not in r and "/target/" not in r]


def name_violation(path: Path) -> str | None:
    for pat in NAME_PATTERNS:
        if fnmatch.fnmatch(path.name, pat):
            return f"shard/payload filename matches {pat}"
    return None


def classify_text(text: str) -> str | None:
    """Return a reason if TEXT looks like a decode/assemble-then-execute wrapper."""
    decode = DECODE_RE.search(text)
    assemble = ASSEMBLE_RE.search(text)
    execute = EXECUTE_RE.search(text)
    if execute and (decode or assemble):
        how = "decodes" if decode else "concatenates parts"
        return f"runtime assembler: {how} then executes the result"
    if decode and re.search(r"gzip\s+-dc|gunzip", text) and re.search(r"base64\s+(-d|--decode)", text):
        return "decodes gzip+base64 payload"
    return None


def content_violation(path: Path) -> str | None:
    try:
        if path.stat().st_size > TEXT_MAX_BYTES:
            return None
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw[:8000]:
        return None
    return classify_text(raw.decode("utf-8", "replace"))


def run_gate() -> int:
    bad: list[str] = []
    files = tracked_files()
    for f in files:
        if f.resolve() == SELF:
            continue
        rel = f.relative_to(ROOT)
        reason = name_violation(f) or content_violation(f)
        if reason:
            bad.append(f"{rel}: {reason}")
    if bad:
        print("FAIL  no_encoded_payloads:")
        for b in bad:
            print(f"  - {b}")
        print("\nCommit plain source. If a tool cannot write a file this large, fix the tool, not the repo (OQ-0014).")
        return 1
    print(f"PASS  no_encoded_payloads: ok {len(files)} tracked files under {', '.join(SCOPES)}")
    return 0


def selftest() -> int:
    bad_stub = (
        'cat "$DIR"/pfy.payload.b64.* | tr -d "\\n" | base64 -d | gzip -dc >"$BODY"\n'
        'exec bash "$BODY" "$@"\n'
    )
    bad_assembler = (
        'parts = sorted(HERE.glob("_pfy_board_body_*.py"))\n'
        'body = "".join(p.read_text() for p in parts)\n'
        'exec(compile(body, str(HERE / "pfy-board.py"), "exec"), globals())\n'
    )
    bad_py_b64 = 'import base64\nexec(compile(base64.b64decode(BLOB), "<x>", "exec"))\n'
    ok_plain = '#!/usr/bin/env bash\nset -euo pipefail\nmain() { echo hi; }\nmain "$@"\n'
    ok_uses_b64_for_data = (
        'import base64\n'
        'payload = json.dumps({"title": t}).encode()\n'
        'auth = base64.b64encode(b"u:p")\n'
    )
    ok_docstring_mentions = '"""Do not use base64 -d payloads; commit plain source."""\nprint(1)\n'
    cases = [
        ("bad_stub", bad_stub, True),
        ("bad_assembler", bad_assembler, True),
        ("bad_py_b64", bad_py_b64, True),
        ("ok_plain", ok_plain, False),
        ("ok_uses_b64_for_data", ok_uses_b64_for_data, False),
        ("ok_docstring_mentions", ok_docstring_mentions, False),
    ]
    errors = []
    for name, text, expect_bad in cases:
        got = classify_text(text) is not None
        if got != expect_bad:
            errors.append(f"{name}: expected {'FAIL' if expect_bad else 'PASS'} got {'FAIL' if got else 'PASS'}")
    for fname, expect_bad in (
        ("pfy.payload.b64.00", True),
        ("_pfy_gui_body_07.py", True),
        ("pfy_enterable_162_b_p1a.py", True),
        ("pfy_attach_usable_220.py", False),
        ("pfy-board.py", False),
    ):
        got = name_violation(Path(fname)) is not None
        if got != expect_bad:
            errors.append(f"name {fname}: expected {'FAIL' if expect_bad else 'PASS'} got {'FAIL' if got else 'PASS'}")
    if errors:
        print("FAIL selftest · " + " ; ".join(errors))
        return 1
    print("PASS selftest · no_encoded_payloads classifier · names + content")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv[1:] else run_gate())
