#!/usr/bin/env bash
# Local pre-gate for themark-net/pfy-mentat.
# Catch Tester/Reviewer failure classes before spending bot gate rounds.
#
# Usage:
#   ./scripts/pregate.sh [REF]
#   ./scripts/pregate.sh --in-place [REF]   # run in current checkout (must be clean or --allow-dirty)
#   ./scripts/pregate.sh --help
#
# REF defaults to HEAD. Creates an isolated worktree under ~/DEVELOP/pfy-mentat/tmp/pg/
# unless --in-place. Writes tmp/pregate-summary.md and exits nonzero on FAIL.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REF="HEAD"
IN_PLACE=0
ALLOW_DIRTY=0
KEEP_WORKTREE=0
SKIP_FULL=0
FORCE_SUITE=0
ONLY=""

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --in-place) IN_PLACE=1; shift ;;
    --allow-dirty) ALLOW_DIRTY=1; shift ;;
    --keep-worktree) KEEP_WORKTREE=1; shift ;;
    --skip-full-suite) SKIP_FULL=1; shift ;;
    --force-suite) FORCE_SUITE=1; shift ;;
    --only) ONLY="${2:-}"; shift 2 ;;
    --) shift; break ;;
    -*)
      echo "unknown flag: $1" >&2
      usage 2
      ;;
    *)
      REF="$1"
      shift
      ;;
  esac
done

cd "$REPO_ROOT"
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "FAIL: not a git repo: $REPO_ROOT" >&2
  exit 2
fi

SHA="$(git rev-parse --verify "${REF}^{commit}")"
SHORT="$(git rev-parse --short "$SHA")"
STAMP="$(date -u +%Y%m%dT%H%M%S%N | cut -c1-20)Z"
HOST="$(hostname -s 2>/dev/null || hostname)"

RUN_ROOT=""
CLEANUP_WORKTREE=""
if [[ "$IN_PLACE" -eq 1 ]]; then
  RUN_ROOT="$REPO_ROOT"
  if [[ "$ALLOW_DIRTY" -eq 0 ]]; then
    if [[ -n "$(git status --porcelain)" ]]; then
      echo "FAIL: working tree dirty; commit, stash, or pass --allow-dirty" >&2
      exit 2
    fi
  fi
  # Ensure we are on the requested SHA when in-place and clean.
  HEAD_SHA="$(git rev-parse HEAD)"
  if [[ "$HEAD_SHA" != "$SHA" ]]; then
    echo "FAIL: --in-place HEAD ($HEAD_SHA) != REF $SHA; check out the REF or omit --in-place" >&2
    exit 2
  fi
else
  # Canonical product tmp/ keeps paths short enough for sun_path / bwrap sockets.
  GIT_COMMON="$(git rev-parse --path-format=absolute --git-common-dir)"
  MAIN_ROOT="$(dirname "$GIT_COMMON")"
  # Keep under ~55 chars so harness2/bwrap sockets stay < sun_path (108).
  # Example: /home/mark/DEVELOP/pfy-mentat/tmp/pg/997d892-064812
  STAMP_SHORT="$(date -u +%H%M%S)"
  RUN_ROOT="$MAIN_ROOT/tmp/pg/${SHORT}-${STAMP_SHORT}"
  mkdir -p "$MAIN_ROOT/tmp/pg"
  git worktree add --detach "$RUN_ROOT" "$SHA"
  CLEANUP_WORKTREE="$RUN_ROOT"
fi

OUT_DIR="$RUN_ROOT/tmp"
mkdir -p "$OUT_DIR"
SUMMARY="$OUT_DIR/pregate-summary.md"
LOG_DIR="$OUT_DIR/pregate-logs"
mkdir -p "$LOG_DIR"
GIT_COMMON="$(git rev-parse --path-format=absolute --git-common-dir)"
MAIN_ROOT="$(dirname "$GIT_COMMON")"
# Scratch shares the short stamp; stays under product tmp/.
STAMP_SHORT="${STAMP_SHORT:-$(date -u +%H%M%S)}"
SHORT_SCRATCH="$MAIN_ROOT/tmp/pgs/${SHORT}-${STAMP_SHORT}"
mkdir -p "$SHORT_SCRATCH"

RESULTS=()
FAIL_COUNT=0
PASS_COUNT=0
SKIP_COUNT=0
START_EPOCH="$(date +%s)"
STRUCTURAL_RAN_UNITTEST=0

record() {
  # record STATUS NAME DETAIL
  local status="$1" name="$2" detail="${3:-}"
  RESULTS+=("$status|$name|$detail")
  case "$status" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    SKIP) SKIP_COUNT=$((SKIP_COUNT + 1)) ;;
  esac
  printf '[%s] %s%s\n' "$status" "$name" "${detail:+ — $detail}"
}

should_run() {
  local name="$1"
  if [[ -z "$ONLY" ]]; then return 0; fi
  [[ "$ONLY" == "$name" ]]
}

cleanup() {
  if [[ -n "$CLEANUP_WORKTREE" && "$KEEP_WORKTREE" -eq 0 ]]; then
    git -C "$REPO_ROOT" worktree remove --force "$CLEANUP_WORKTREE" >/dev/null 2>&1 || rm -rf "$CLEANUP_WORKTREE"
  fi
  if [[ -n "${SHORT_SCRATCH:-}" && "$KEEP_WORKTREE" -eq 0 ]]; then
    rm -rf "$SHORT_SCRATCH"
  fi
}
trap cleanup EXIT

cd "$RUN_ROOT"

# ---------------------------------------------------------------------------
# Shared env for CI-like steps
# ---------------------------------------------------------------------------
STATE_DIR="$OUT_DIR/pfy-state"
mkdir -p "$STATE_DIR"
export PFY_STATE_DIR="$STATE_DIR"
# Prefer short product tmp/ scratch; never /tmp for project temps.
export TMPDIR="${SHORT_SCRATCH:-$OUT_DIR/scratch}"
mkdir -p "$TMPDIR"

# Curated PATH that hides bwrap (ubuntu runners often lack usable userns/bwrap).
CI_PATH="$OUT_DIR/ci-path"
mkdir -p "$CI_PATH"
for b in python3 git make bash sh true false uname mkdir ls cat cp mv rm chmod \
         head tail grep sed awk tr cut sort uniq find xargs dirname basename \
         mktemp sleep touch date env tee wc diff patch tar gzip unzip which id \
         whoami getconf locale ps pgrep; do
  for d in /usr/bin /bin /usr/local/bin; do
    if [[ -x "$d/$b" && ! -e "$CI_PATH/$b" ]]; then
      ln -sfn "$d/$b" "$CI_PATH/$b"
      break
    fi
  done
done
# Deliberately do NOT link bwrap.

# ---------------------------------------------------------------------------
# Check: lint / static contract (what CI actually runs; no ruff in this repo)
# ---------------------------------------------------------------------------
if should_run lint; then
  log="$LOG_DIR/lint.log"
  set +e
  (
    set -euo pipefail
    echo "== filemode =="
    fail=0
    for p in pfy scripts/pfy scripts/detect-local-runtime.sh; do
      mode="$(git ls-files -s -- "$p" | awk '{print $1}')"
      echo "$p gitmode=$mode"
      if [[ "$mode" != "100755" ]]; then echo "FAIL: $p is ${mode:-missing}"; fail=1; fi
      if [[ ! -x "$p" ]]; then echo "FAIL: $p not executable"; fail=1; fi
    done
    echo "== py_compile launchers =="
    python3 -m py_compile scripts/pfy-board.py scripts/pfy-gui.py
    echo "== bash -n scripts/pfy =="
    bash -n scripts/pfy
    echo "== ./pfy help =="
    ./pfy help >/dev/null
    echo "== check_no_encoded_payloads =="
    python3 scripts/check_no_encoded_payloads.py --selftest
    python3 scripts/check_no_encoded_payloads.py
    echo "== smoke_contract_lint =="
    python3 scripts/smoke_contract_lint.py
    echo "== catalog_check =="
    python3 scripts/catalog_check.py
    exit "$fail"
  ) >"$log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    record PASS lint "filemode + encoded-payloads + smoke_contract + catalog"
  else
    record FAIL lint "see $log (exit $rc)"
  fi
fi

# ---------------------------------------------------------------------------
# Check: eval-structural (reproduce .github/workflows/eval-structural.yml G0)
# ---------------------------------------------------------------------------
if should_run eval-structural; then
  log="$LOG_DIR/eval-structural.log"
  set +e
  (
    set -euo pipefail
    # Mark before run_structural so a failing unittest does not re-run via suite.
    touch "$LOG_DIR/structural-did-unittest"
    python3 examples/eval-harness/run_structural.py --write-md pipelines/eval/structural.latest.md
    python3 examples/eval-harness/run_golden.py --write-md pipelines/eval/golden.latest.md
    PFY_GAB_OFFLINE=1 python3 scripts/pfy_gab_228.py --selftest
    PFY_JEV_OFFLINE=1 python3 scripts/pfy_jev_230.py --selftest
    python3 scripts/pfy_launch_wizard_225.py --selftest
    # Unittest discover is owned by the "suite" check (same command CI uses).
    # Re-running it here would double wall time; suite failure fails pregate.
    python3 scripts/catalog_check.py
    ./pfy toolset matrix
    ./pfy toolset plan jev --harness opencode
    ./pfy hedge decide --task bulk --local ready --budget 0
    git ls-files -s -- pfy scripts/pfy
    test -x pfy && test -x scripts/pfy
    bash -n scripts/pfy
    python3 -m py_compile scripts/pfy-board.py scripts/pfy-gui.py
    ./pfy help >/dev/null
    python3 scripts/check_no_encoded_payloads.py --selftest
    python3 scripts/check_no_encoded_payloads.py
  ) >"$log" 2>&1
  rc=$?
  set -e
  if [[ -f "$LOG_DIR/structural-did-unittest" ]]; then
    STRUCTURAL_RAN_UNITTEST=1
  fi
  if [[ $rc -eq 0 ]]; then
    record PASS eval-structural "G0 ubuntu steps (structural/golden/selftests/toolset/hedge)"
  else
    record FAIL eval-structural "see $log (exit $rc)"
  fi
fi

# ---------------------------------------------------------------------------
# Check: full test suite the way CI does (sandbox tests included on nimo)
# ---------------------------------------------------------------------------
if should_run suite; then
  if [[ "$SKIP_FULL" -eq 1 ]]; then
    record SKIP suite "--skip-full-suite"
  elif [[ "$FORCE_SUITE" -eq 0 && "$STRUCTURAL_RAN_UNITTEST" -eq 1 ]]; then
    record SKIP suite "covered by eval-structural run_structural (pass --force-suite to re-run)"
  else
    log="$LOG_DIR/suite.log"
    BEFORE_ORPHANS="$LOG_DIR/orphans-before.txt"
    ps -u "$(id -un)" -o pid=,ppid=,pgid=,cmd= >"$BEFORE_ORPHANS" 2>/dev/null || true
    set +e
    PFY_STATE_DIR="$STATE_DIR" TMPDIR="$TMPDIR" \
      python3 -m unittest discover -s tests -t . >"$log" 2>&1
    rc=$?
    set -e
    AFTER_ORPHANS="$LOG_DIR/orphans-after.txt"
    ps -u "$(id -un)" -o pid=,ppid=,pgid=,cmd= >"$AFTER_ORPHANS" 2>/dev/null || true
    if [[ $rc -eq 0 ]]; then
      # Summarize counts from unittest output
      tail_line="$(tail -n 5 "$log" | tr '\n' ' ')"
      record PASS suite "$tail_line"
    else
      record FAIL suite "unittest exit $rc; see $log"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Check: CI-parity (bwrap unavailable + PFY_STATE_DIR like ubuntu job)
# ---------------------------------------------------------------------------
if should_run ci-parity; then
  log="$LOG_DIR/ci-parity.log"
  set +e
  (
    set -euo pipefail
    echo "== PATH without bwrap =="
    export PATH="$CI_PATH"
    command -v bwrap && { echo "FAIL: bwrap still on PATH"; exit 1; } || echo "bwrap hidden OK"
    command -v python3
    export PFY_STATE_DIR="$STATE_DIR/ci-parity"
    mkdir -p "$PFY_STATE_DIR"
    export TMPDIR="${SHORT_SCRATCH:-$OUT_DIR}/scratch-ci"
    mkdir -p "$TMPDIR"
    # Static guard from GATE-NOTES / fix2: runtime-dir tests must not auto-add
    # --unsafe-no-sandbox (2fadea1 failed ubuntu CI because they did).
    static_rc=0
    python3 - <<'PY' || static_rc=1
from pathlib import Path
import re, sys
p = Path("tests/test_pfy_build_local.py")
if not p.exists():
    print("SKIP: no tests/test_pfy_build_local.py")
    sys.exit(0)
text = p.read_text(encoding="utf-8")
needed = [
    "test_missing_runtime_dir_is_not_reported_as_missing_bwrap",
    "test_runtime_dir_under_system_tmp_is_blocked",
]
fail = []
for name in needed:
    m = re.search(rf"def {name}\(self\).*?(?=\n    def |\nclass |\Z)", text, re.S)
    if not m:
        fail.append(f"missing {name}")
        continue
    body = m.group(0)
    if "auto_unsafe=False" not in body:
        fail.append(f"{name} does not pass auto_unsafe=False (CI will auto-add --unsafe-no-sandbox when bwrap is unusable)")
if fail:
    print("FAIL ci-parity static:", "; ".join(fail))
    sys.exit(1)
print("PASS static: runtime-dir tests pin auto_unsafe=False")
PY
    # Behavioral: run those two tests with bwrap hidden. On a bad tip they FAIL
    # (wrong exit/reason) or incorrectly PASS under --unsafe-no-sandbox.
    if [[ -f tests/test_pfy_build_local.py ]]; then
      # Need git etc already in CI_PATH. Also need /proc for unittest.
      # Run even when the static pin failed, so the log shows the real CI symptom.
      python3 -m unittest \
        tests.test_pfy_build_local.LocalBuildTests.test_missing_runtime_dir_is_not_reported_as_missing_bwrap \
        tests.test_pfy_build_local.LocalBuildTests.test_runtime_dir_under_system_tmp_is_blocked \
        -v
    fi
    exit "$static_rc"
  ) >"$log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    record PASS ci-parity "bwrap-hidden PATH + runtime-dir auto_unsafe pin"
  else
    record FAIL ci-parity "see $log (exit $rc)"
  fi
fi

# ---------------------------------------------------------------------------
# Check: leftover child processes after suite (cheap scan)
# ---------------------------------------------------------------------------
if should_run orphans; then
  log="$LOG_DIR/orphans.log"
  set +e
  (
    # Look for leftover processes (local-build, stub agents, opencode) whose argv names this run's paths.
    # Ignore this pregate process and its direct pipeline.
    leak=0
    while read -r pid cmd; do
      [[ -z "${pid:-}" ]] && continue
      case "$cmd" in
        *pregate.sh*|*pregate-logs*) continue ;;
      esac
      # Match processes whose cwd or argv references our run root tmp receipts/agents.
      # Only this run's paths: never flag (or touch) other worktrees' live runs.
      if [[ "$cmd" == *"$RUN_ROOT/"* ]] || [[ -n "${SHORT_SCRATCH:-}" && "$cmd" == *"$SHORT_SCRATCH"* ]]; then
        # Still alive?
        if kill -0 "$pid" 2>/dev/null; then
          echo "LEAK pid=$pid cmd=$cmd"
          leak=1
        fi
      fi
    done < <(ps -u "$(id -un)" -o pid=,cmd= 2>/dev/null || true)
    # Heartbeat / orphan pid files left under run tmp
    if find "$OUT_DIR" ${SHORT_SCRATCH:+"$SHORT_SCRATCH"} \( -name 'orphan*.pid' -o -name 'orphan*.heartbeat' \) 2>/dev/null | grep -q .; then
      echo "LEAK: orphan pid/heartbeat files under $OUT_DIR"
      find "$OUT_DIR" ${SHORT_SCRATCH:+"$SHORT_SCRATCH"} \( -name 'orphan*.pid' -o -name 'orphan*.heartbeat' \) 2>/dev/null || true
      leak=1
    fi
    exit "$leak"
  ) >"$log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    record PASS orphans "no live processes referencing this run root; no orphan pid/heartbeat files"
  else
    record FAIL orphans "see $log"
  fi
fi

# ---------------------------------------------------------------------------
# Check: protected / gate-file hash integrity vs git tree
# ---------------------------------------------------------------------------
if should_run gate-hash; then
  log="$LOG_DIR/gate-hash.log"
  set +e
  (
    set -euo pipefail
    python3 - <<'PY'
"""Fail if gate basenames in the worktree differ from git HEAD blobs.

Mirrors scripts/pfy_build_local._GATE_BASENAMES: conftest/pytest.ini/sitecustomize
etc. must match the committed tree. Also flag untracked gate files (test cheats).
"""
from __future__ import annotations
import hashlib, subprocess, sys
from pathlib import Path

GATE = {
    "conftest.py", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml",
    "sitecustomize.py", "usercustomize.py", ".gitignore", ".gitattributes",
}
root = Path(".").resolve()

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# Tracked files
tracked = subprocess.check_output(
    ["git", "ls-files", "-z"], text=False
).split(b"\0")
fail = []
seen = []
for raw in tracked:
    if not raw:
        continue
    rel = raw.decode("utf-8", "surrogateescape")
    name = Path(rel).name
    if name not in GATE and not rel.startswith("tests/"):
        continue
    # Hash all tests/ plus gate basenames anywhere
    if name in GATE or rel.startswith("tests/"):
        data = Path(rel).read_bytes()
        blob = subprocess.check_output(["git", "show", f"HEAD:{rel}"])
        if data != blob:
            fail.append(f"modified vs HEAD: {rel}")
        seen.append(rel)

# Untracked gate basenames (classic cheat: drop sitecustomize.py)
untracked = subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard", "-z"], text=False
).split(b"\0")
for raw in untracked:
    if not raw:
        continue
    rel = raw.decode("utf-8", "surrogateescape")
    # Ignore our own pregate outputs under tmp/
    if rel.startswith("tmp/"):
        continue
    name = Path(rel).name
    if name in GATE:
        fail.append(f"untracked gate file: {rel}")
    if rel.startswith("tests/") and rel.endswith(".py"):
        fail.append(f"untracked test file: {rel}")

print(f"checked {len(seen)} tracked test/gate paths")
if fail:
    print("FAIL gate-hash:")
    for line in fail:
        print(" ", line)
    sys.exit(1)
print("PASS gate-hash: worktree matches git for tests/ and gate basenames; no untracked gate/test cheats")
PY
  ) >"$log" 2>&1
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    record PASS gate-hash "tests/ + gate basenames match HEAD; no untracked cheats"
  else
    record FAIL gate-hash "see $log"
  fi
fi

# ---------------------------------------------------------------------------
# Write summary
# ---------------------------------------------------------------------------
END_EPOCH="$(date +%s)"
WALL=$((END_EPOCH - START_EPOCH))
OVERALL="PASS"
if [[ "$FAIL_COUNT" -gt 0 ]]; then OVERALL="FAIL"; fi

{
  echo "# Pregate summary"
  echo
  echo "- **overall:** $OVERALL"
  echo "- **ref:** \`$REF\` (\`$SHA\`)"
  echo "- **host:** $HOST (America/Los_Angeles box clock)"
  echo "- **run root:** \`$RUN_ROOT\`"
  echo "- **wall seconds:** $WALL"
  echo "- **counts:** pass=$PASS_COUNT fail=$FAIL_COUNT skip=$SKIP_COUNT"
  echo
  echo "## Checks"
  echo
  echo "| status | check | detail |"
  echo "|---|---|---|"
  for row in "${RESULTS[@]}"; do
    IFS='|' read -r st name detail <<<"$row"
    # escape pipes in detail
    detail="${detail//|/\\|}"
    echo "| $st | $name | $detail |"
  done
  echo
  echo "## What each check covers"
  echo
  echo "| check | covers |"
  echo "|---|---|"
  echo "| lint | Operator filemode 100755, \`./pfy help\`, \`check_no_encoded_payloads\`, \`smoke_contract_lint\`, \`catalog_check\`, py_compile of board/gui (CI has no ruff; this is the lint surface). |"
  echo "| eval-structural | Steps from \`.github/workflows/eval-structural.yml\` G0 ubuntu job, including run_structural's full unittest discover: structural + golden, gab/jev/launch-wizard selftests, toolset matrix/plan, hedge decide, launcher exec, encoded-payload scan. |"
  echo "| suite | Full \`python3 -m unittest discover -s tests -t .\` with \`PFY_STATE_DIR\` under the run tmp (sandbox tests run when bwrap works). |"
  echo "| ci-parity | Hides bwrap via curated PATH; sets \`PFY_STATE_DIR\` like the ubuntu job; static+behavioral pin that runtime-dir tests pass \`auto_unsafe=False\` (catches 2fadea1-class ubuntu CI failures). |"
  echo "| orphans | After tests, scan for live processes whose argv references this run root or scratch dir, and orphan pid/heartbeat files there. |"
  echo "| gate-hash | Worktree \`tests/\` and gate basenames (\`conftest.py\`, \`sitecustomize.py\`, …) must match git HEAD; no untracked gate/test files (test-runner cheat class). |"
  echo
  echo "## Logs"
  echo
  echo "Per-check logs: \`$LOG_DIR/\`"
  echo
  echo "## Rule"
  echo
  echo "Attach this summary before any Tester/Reviewer gate request. See \`docs/ops/PREGATE.md\`."
} >"$SUMMARY"

# Also copy summary path to a stable pointer under repo tmp when using nested run
STABLE_DIR="${MAIN_ROOT:-$REPO_ROOT}/tmp"
mkdir -p "$STABLE_DIR"
STABLE="$STABLE_DIR/pregate-latest-summary.md"
cp "$SUMMARY" "$STABLE" 2>/dev/null || true
if [[ -n "${MAIN_ROOT:-}" && "$MAIN_ROOT" != "$REPO_ROOT" ]]; then
  mkdir -p "$REPO_ROOT/tmp"
  cp "$SUMMARY" "$REPO_ROOT/tmp/pregate-latest-summary.md" 2>/dev/null || true
fi

echo
echo "Wrote $SUMMARY"
echo "OVERALL=$OVERALL wall=${WALL}s pass=$PASS_COUNT fail=$FAIL_COUNT skip=$SKIP_COUNT"

if [[ "$OVERALL" != "PASS" ]]; then
  exit 1
fi
exit 0
