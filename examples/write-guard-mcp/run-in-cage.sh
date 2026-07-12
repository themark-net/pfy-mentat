#!/usr/bin/env bash
# In-cage smoke: install write-guard, selftest, audit write + enforce deny .env
set -euo pipefail

PKG="${WRITE_GUARD_SRC:-/workspace/examples/write-guard-mcp/pkg}"
VENV="${WG_VENV:-/workspace/.venvs/write-guard-smoke}"
WORK="${WG_WORK:-/workspace/wg-smoke-work}"

echo "== write-guard-mcp in-cage smoke =="
echo "  pkg=$PKG venv=$VENV"

if [[ ! -d "$PKG/src/write_guard" ]]; then
  echo "error: package not staged at $PKG (make smoke-write-guard stages it)" >&2
  exit 1
fi

if [[ ! -x "${VENV}/bin/python" ]]; then
  mkdir -p "$(dirname "$VENV")"
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
python -m pip install -q --upgrade pip
python -m pip install -q -e "$PKG"

echo "== selftest =="
python -m write_guard selftest

echo "== unittest =="
python -m unittest discover -s "$PKG/tests" -v

mkdir -p "$WORK"
export WRITE_GUARD_ROOTS="$WORK"
export WRITE_GUARD_POLICY="$PKG/policy.default.yaml"
# rewrite policy roots for work dir via env only — roots from env

echo "== audit mode: write ok + write .env (allowed) =="
export WRITE_GUARD_MODE=audit
# patch policy roots by using paths under WORK — decide uses WRITE_GUARD_ROOTS
python - <<PY
import os, tempfile
from pathlib import Path
from write_guard.policy import Policy, decide, load_policy, resolve_mode, resolve_roots
from write_guard.audit import append_event, tail_events

work = Path(os.environ["WRITE_GUARD_ROOTS"])
pol = Policy(
    roots=[str(work)],
    deny_globs=["**/.env", "**/auth.json", "**/*secret*"],
    allow_write_globs=[str(work) + "/**"],
    deny_write_globs=[str(work) + "/.write-guard-audit.jsonl"],
    default_mode="audit",
    audit_log=str(work / ".write-guard-audit.jsonl"),
)
mode = "audit"
ok = work / "hello.txt"
d = decide(str(ok), op="write", mode=mode, policy=pol)
assert d.allow, d
ok.write_text("hi", encoding="utf-8")
append_event(pol.audit_log, op="write_file", path=str(ok), allow=True, reason=d.reason, mode=mode)
envp = work / ".env"
d2 = decide(str(envp), op="write", mode=mode, policy=pol)
assert d2.allow, d2  # audit allows
envp.write_text("SECRET=1", encoding="utf-8")
append_event(pol.audit_log, op="write_file", path=str(envp), allow=True, reason=d2.reason, mode=mode)
print("audit writes ok; events=", len(tail_events(pol.audit_log)))
PY

echo "== enforce mode: deny .env, allow normal =="
python - <<PY
from pathlib import Path
from write_guard.policy import Policy, decide
import os
work = Path(os.environ["WRITE_GUARD_ROOTS"])
pol = Policy(
    roots=[str(work)],
    deny_globs=["**/.env", "**/auth.json", "**/*secret*"],
    allow_write_globs=[str(work) + "/**"],
    deny_write_globs=[],
    allow_delete_globs=[],
    default_mode="enforce",
)
mode = "enforce"
d = decide(str(work / "ok2.txt"), op="write", mode=mode, policy=pol)
assert d.allow, d
d2 = decide(str(work / ".env"), op="write", mode=mode, policy=pol)
assert not d2.allow, d2
d3 = decide(str(work / "ok2.txt"), op="delete", mode=mode, policy=pol)
assert not d3.allow, d3
print("enforce deny .env + delete default deny OK")
PY

echo "smoke: PASS (write-guard-mcp)"
