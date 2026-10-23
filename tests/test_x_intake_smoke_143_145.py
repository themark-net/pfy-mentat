"""Entries 143-145 smokes (taste-skill, gitai, Muxin): pins and missing prereqs exit 2; a linter that misses slop or
flags clean copy, a non-deterministic or writing draw, a browser check that passes slop or leaves a profile, a quickstart
that lands the denied change, an MCP server with the wrong tools or answers, and misplaced writes FAIL; timeouts FAIL
with the real-HOME check kept. Every check the smoke records has a test here that turns it false.

Each tool is a small Python stub (shebang = this interpreter) with knobs baked into its text, because the smoke gives
its children a clean env. taste-skill: a fake `node` that answers --version and imitates lint.mjs, draw.mjs and
inspect.mjs by the script name it is given. gitai: a real git repo with stub _build/bin files and a bash quickstart.sh
that calls `make -C <repo> build` and builds the demo bare repo with plain git. Muxin: one fake binary answering
--version, paths, machines --demo --json and mcp --demo (newline JSON-RPC). Parent HOME is a temp dir this test owns;
tests that plant a real-HOME write set PATH to an empty dir so bwrap is not found (children use a fixed system PATH).
Receipts go to a temp $PFY_SMOKE_RECEIPT_DIR.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "examples/x-intake-local/smoke_143_145.py"
_RECEIPTS = tempfile.TemporaryDirectory(prefix="pfy-xintake-143-receipts-")
RECEIPT_DIR = Path(_RECEIPTS.name)
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "init.defaultBranch=main"]


def tearDownModule() -> None:
    _RECEIPTS.cleanup()


def _write_stub(path: Path, knobs: dict, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!{sys.executable}\nK = {knobs!r}\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _git_repo(d: Path) -> str:
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run([*GIT, "init", "-q", str(d)], check=True)
    (d / "README.md").write_text("stub\n")
    subprocess.run([*GIT, "-C", str(d), "add", "-A"], check=True)
    subprocess.run([*GIT, "-C", str(d), "commit", "-qm", "stub"], check=True)
    return subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


PRELUDE = r'''
import json, os, random, sys, time
if K.get("plant"):
    exec(K["plant"])
a = sys.argv[1:]
'''

# fake node for taste-skill
TASTE_NODE = PRELUDE + r'''
if a == ["--version"]:
    print("v" + K.get("node", "24.14.1"))
    sys.exit(0)
time.sleep(K.get("sleep", 0))
script, args = os.path.basename(a[0]), a[1:]


def opt(name):
    return args[args.index(name) + 1] if name in args else None


def findings(html, ids):
    rules = {"gradient": "linear-gradient", "emoji": "\U0001F680", "eyebrow": "eyebrow", "lorem": "Lorem",
             "purple": "#a855f7"}
    return [{"level": "FAIL", "id": k} for k, v in rules.items() if k in ids and v in html and k not in K.get("drop", [])]


if script == "lint.mjs":
    root = args[0]
    if not os.path.isdir(root):
        sys.exit(K.get("missing_rc", 2))
    html = open(os.path.join(root, "index.html"), encoding="utf-8").read()
    if K.get("mutate") and root == "slop":
        open(os.path.join(root, "index.html"), "a").write("<!-- x -->")
    f = findings(html, ["gradient", "emoji", "eyebrow", "lorem", "purple"])
    if root == "clean" and K.get("clean_finding"):
        f.append({"level": "WARN", "id": "measure"})
    print(json.dumps({"files": 1, "findings": f}))
    sys.exit(1 if any(x["level"] == "FAIL" for x in f) else 0)
if script == "draw.mjs":
    if opt("--options"):
        extra = str(random.random()) if K.get("random_menu") else ""
        if K.get("menu_writes"):
            open("menu.txt", "w").write("x")
        print("# OPTIONS\n" + "1. One motif, Switzer, sky and sand. " * 10 + extra)
        sys.exit(0)
    out = opt("--out") or ".taste-skill"
    if not K.get("no_direction"):
        os.makedirs(out, exist_ok=True)
        open(os.path.join(out, "direction.json"), "w").write(json.dumps({"direction": "one-motif"}))
    hist = os.path.join(os.environ["HOME"], ".taste-skill/history.json") if K.get("hist_home") \
        else os.environ["TASTE_SKILL_HISTORY"]
    os.makedirs(os.path.dirname(hist), exist_ok=True)
    open(hist, "w").write("[]")
    print("# DIRECTION SHEET - One motif")
    sys.exit(0)
if script == "inspect.mjs":
    html = open(args[0], encoding="utf-8").read()
    out = opt("--out")
    os.makedirs(out, exist_ok=True)
    if not K.get("no_shot"):
        open(os.path.join(out, "tablet-fold.jpg"), "wb").write(b"\xff\xd8")
    pki = os.path.join(os.environ["HOME"], ".local/share/pki/nssdb")
    os.makedirs(pki, exist_ok=True)
    if K.get("leave_profile"):
        os.makedirs(os.path.join(os.environ["TASTE_SKILL_TMP"], "ad-chrome-123"), exist_ok=True)
    if K.get("home_stray"):
        open(os.path.join(os.environ["HOME"], ".stray"), "w").write("x")
    f = findings(html, ["gradient", "emoji", "eyebrow"] if not K.get("inspect_clean") else [])
    print(json.dumps({"url": args[0], "findings": f}))
    sys.exit(K.get("inspect_rc", 1 if f else 0))
sys.exit(9)
'''

# fake muxin
MUXIN = PRELUDE + r'''
if a == ["--version"]:
    print("muxin " + K.get("version", "0.6.0"))
    sys.exit(K.get("version_rc", 0))
time.sleep(K.get("sleep", 0))
mh = os.environ["MUXIN_HOME"] if not K.get("paths_home") else os.environ["HOME"] + "/.config/muxin"
if a == ["paths"]:
    print(f"config dir  {mh}\nconfig      {mh}/config.toml\nstate       {mh}/state.json")
    sys.exit(0)
NAMES = ["forge", "orbit", "beacon", "pebble", "dev-1", "harbor", "vault", "win-test", "sandbox"]
if a == ["machines", "--demo", "--json"]:
    print(json.dumps([{"id": n} for n in NAMES[:K.get("machines", 9)]]))
    sys.exit(0)
if a != ["mcp", "--demo"]:
    sys.exit(9)
if K.get("home_write"):
    os.makedirs(os.environ["HOME"] + "/.local/state/gh", exist_ok=True)
    open(os.environ["HOME"] + "/.local/state/gh/device-id", "w").write("x")
tools = [{"name": f"tool_{i}", "annotations": {"readOnlyHint": True}} for i in range(K.get("tools", 86))]
tools += [{"name": "status", "annotations": {"readOnlyHint": not K.get("status_rw")}},
          {"name": "run_on_machines", "annotations": {"destructiveHint": True}},
          {"name": "cloud_destroy", "annotations": {"destructiveHint": not K.get("undestructive")}}]


def text(obj):
    return {"content": [{"type": "text", "text": json.dumps(obj)}]}


def call(name, args):
    if name == "status":
        return text({"summary": K.get("summary", "9 machines, 8 runners: 4 working, 3 idle, 1 offline.")})
    if name == "get_machine":
        if "machine_id" not in args:
            return text({"error": {"code": "ok" if K.get("lax_args") else "invalid"}})
        mid = args["machine_id"]
        if mid == "forge" and not K.get("forge_missing"):
            return text({"id": "forge", "name": "Forge"})
        if K.get("unknown_ok"):
            return text({"id": mid})
        return text({"error": {"code": "not_found", "hint": "known ids: " + ", ".join(NAMES)}})
    if name == "run_on_machines":
        return text({"status": K.get("run_status", "succeeded")})
    return {"isError": True, "content": []}


for line in sys.stdin:
    m = json.loads(line)
    if "id" not in m:
        continue
    if m["method"] == "initialize":
        res = {"serverInfo": {"name": "muxin", "version": K.get("server_version", "0.6.0")}}
    elif m["method"] == "tools/list":
        res = {"tools": tools}
    else:
        res = call(m["params"]["name"], m["params"].get("arguments") or {})
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": m["id"], "result": res}) + "\n")
    sys.stdout.flush()
if K.get("ignore_eof"):
    time.sleep(30)
'''

# gitai quickstart stand-in; __KNOBS__ lines are replaced per test
QUICKSTART = r'''#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
work="$1"
__MAKE__
__PLANT__
g() { git -c user.name=seed -c user.email=seed@example.com "$@"; }
mkdir -p "$work/repos"
git init -q --bare "$work/repos/demo.git"
git init -q "$work/seed"
cd "$work/seed"
git symbolic-ref HEAD refs/heads/main
printf '__MAIN__' > README.md
g add README.md && g commit -qm seed
git push -q "$work/repos/demo.git" HEAD:refs/heads/main
printf '__FEATURE__' > feature.txt
g add feature.txt && g commit -qm feature
git push -q "$work/repos/demo.git" HEAD:refs/heads/feature/demo
echo "__DENIED__"
exit __RC__
'''


class Base(unittest.TestCase):
    PREFIXES = ("TASTE_", "GITAI_", "MUXIN_")

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="pfy-xintake-143-test-")
        self.base = Path(self._td.name)
        self.home = self.base / "realhome"
        self.home.mkdir()
        self.nobwrap = self.base / "emptypath"
        self.nobwrap.mkdir()

    def tearDown(self) -> None:
        self._td.cleanup()

    def env(self, *, no_bwrap: bool = False, **extra: str) -> dict[str, str]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith(self.PREFIXES) or key == "PFY_XINTAKE_TIMEOUT":
                env.pop(key, None)
        env["HOME"] = str(self.home)
        env["PFY_SMOKE_RECEIPT_DIR"] = str(RECEIPT_DIR)
        env["PATH"] = str(self.nobwrap) if no_bwrap else env.get("PATH", "/usr/bin:/bin")
        env.update(extra)
        return env

    def run_entry(self, entry: str, env: dict[str, str]) -> tuple[int, dict]:
        p = subprocess.run([sys.executable, SCRIPT, "--entry", entry], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, timeout=180)
        self.assertNotIn("Traceback", p.stderr + p.stdout)
        receipt = json.loads((RECEIPT_DIR / entry / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["exit_code"], p.returncode)
        return p.returncode, receipt

    def plant_home(self, rel: str) -> str:
        target = self.home / rel
        return f"import pathlib; p = pathlib.Path({str(target)!r}); p.mkdir(parents=True, exist_ok=True); " \
               "(p / 'x').write_text('planted')"

    def assert_failed(self, code: int, r: dict, check: str) -> None:
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"][check], r)
        self.assertIn(check, r["reason"])

    def assert_passed(self, code: int, r: dict) -> None:
        self.assertEqual(code, 0, r)
        self.assertTrue(r["checks"] and all(r["checks"].values()), r)


# ---------------------------------------------------------------- taste-skill
class TasteTests(Base):
    def stub(self, skill_name: str = "design-taste-frontend", **knobs) -> dict[str, str]:
        d = self.base / "taste"
        s = d / "skills/taste-skill"
        (s / "scripts").mkdir(parents=True)
        for f in ("lint.mjs", "draw.mjs", "inspect.mjs"):
            (s / "scripts" / f).write_text("// stub\n")
        (s / "SKILL.md").write_text(f"---\nname: {skill_name}\ndescription: x\n---\n# body\n")
        sha = _git_repo(d)
        node = _write_stub(self.base / "bin/node", knobs, TASTE_NODE)
        chrome = _write_stub(self.base / "bin/chrome", {}, "")
        return {"TASTE_SKILL_DIR": str(d), "TASTE_NODE": str(node), "TASTE_CHROME": str(chrome),
                "TASTE_SKILL_COMMIT": sha}

    def go(self, *, no_bwrap: bool = False, skill_name: str = "design-taste-frontend", **knobs) -> tuple[int, dict]:
        extra = self.stub(skill_name, **knobs)
        extra.update(knobs.pop("_env", {}) if "_env" in knobs else {})
        return self.run_entry("taste-skill", self.env(no_bwrap=no_bwrap, **extra))

    def test_happy_path_passes(self) -> None:
        code, r = self.go()
        self.assert_passed(code, r)
        self.assertEqual(r["lint"]["slop_ids"], ["emoji", "eyebrow", "gradient", "lorem", "purple"])
        self.assertIn(".local/share/pki", r["home_files"])

    def test_missing_checkout_exits_2(self) -> None:
        code, r = self.run_entry("taste-skill", self.env(TASTE_SKILL_DIR=str(self.base / "nope")))
        self.assertEqual(code, 2)
        self.assertIn("taste-skill not found", r["reason"])

    def test_commit_pin_mismatch_exits_2(self) -> None:
        extra = self.stub()
        extra["TASTE_SKILL_COMMIT"] = "0" * 40
        code, r = self.run_entry("taste-skill", self.env(**extra))
        self.assertEqual(code, 2)
        self.assertIn("not " + "0" * 40, r["reason"])

    def test_default_pin_mismatch_exits_2(self) -> None:
        extra = self.stub()
        del extra["TASTE_SKILL_COMMIT"]
        code, r = self.run_entry("taste-skill", self.env(**extra))
        self.assertEqual(code, 2)
        self.assertIn("6010f91a", r["reason"])

    def test_old_node_exits_2(self) -> None:
        code, r = self.go(node="20.19.2")
        self.assertEqual(code, 2)
        self.assertIn("Node 22+", r["reason"])

    def test_bad_override_exits_2(self) -> None:
        extra = self.stub()
        extra["TASTE_CHROME"] = str(self.base / "no-chrome")
        code, r = self.run_entry("taste-skill", self.env(**extra))
        self.assertEqual(code, 2)
        self.assertIn("$TASTE_CHROME", r["reason"])

    def test_wrong_skill_name_fails(self) -> None:
        self.assert_failed(*self.go(skill_name="something-else"), "skill_frontmatter_name")

    def test_lint_misses_slop_fails(self) -> None:
        self.assert_failed(*self.go(drop=["lorem"]), "lint_slop_fails")

    def test_lint_flags_clean_fails(self) -> None:
        self.assert_failed(*self.go(clean_finding=True), "lint_clean_passes")

    def test_lint_missing_path_rc_fails(self) -> None:
        self.assert_failed(*self.go(missing_rc=0), "lint_missing_exit_2")

    def test_random_menu_fails(self) -> None:
        self.assert_failed(*self.go(random_menu=True), "draw_menu_deterministic")

    def test_menu_writing_fails(self) -> None:
        self.assert_failed(*self.go(menu_writes=True), "draw_menu_writes_nothing")

    def test_no_direction_fails(self) -> None:
        self.assert_failed(*self.go(no_direction=True), "draw_writes_direction")

    def test_history_in_home_fails(self) -> None:
        code, r = self.go(hist_home=True)
        self.assert_failed(code, r, "draw_history_in_temp")
        self.assertFalse(r["checks"]["home_only_chrome_leftovers"])

    def test_inspect_passing_slop_fails(self) -> None:
        self.assert_failed(*self.go(inspect_clean=True), "inspect_fails_slop")

    def test_inspect_wrong_rc_fails(self) -> None:
        self.assert_failed(*self.go(inspect_rc=0), "inspect_fails_slop")

    def test_no_screenshot_fails(self) -> None:
        self.assert_failed(*self.go(no_shot=True), "inspect_screenshot")

    def test_profile_left_fails(self) -> None:
        code, r = self.go(leave_profile=True)
        self.assert_failed(code, r, "no_profile_left")
        self.assertEqual(r["profiles_left"], ["ad-chrome-123"])

    def test_fixture_mutation_fails(self) -> None:
        self.assert_failed(*self.go(mutate=True), "fixtures_untouched")

    def test_stray_home_file_fails(self) -> None:
        self.assert_failed(*self.go(home_stray=True), "home_only_chrome_leftovers")

    def test_real_home_write_fails(self) -> None:
        code, r = self.go(no_bwrap=True, plant=self.plant_home(".taste-skill"))
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"]["real_home_untouched"])
        self.assertIn("~/.taste-skill", r["reason"])

    def test_timeout_fails_with_home_check(self) -> None:
        extra = self.stub(sleep=5)
        code, r = self.run_entry("taste-skill", self.env(PFY_XINTAKE_TIMEOUT="1", **extra))
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"]["body_completed"])
        self.assertTrue(r["checks"]["real_home_untouched"])
        self.assertIn("timeout after", r["reason"])

    def test_bad_timeout_exits_2(self) -> None:
        code, r = self.run_entry("taste-skill", self.env(PFY_XINTAKE_TIMEOUT="abc", **self.stub()))
        self.assertEqual(code, 2)
        self.assertIn("PFY_XINTAKE_TIMEOUT", r["reason"])


# ---------------------------------------------------------------- gitai
class GitaiTests(Base):
    def stub(self, *, make: str = 'make -C "$repo_root" build', plant: str = "", main: str = "hello graft\\n",
             feature: str = "feature\\n", denied: str = "denied as expected", rc: int = 0,
             bins: tuple = ("gitaly", "gitaly-hooks", "gitaly-ssh", "graft", "graft-cache")) -> dict[str, str]:
        d = self.base / "gitai"
        qs = d / "examples/graft/quickstart.sh"
        qs.parent.mkdir(parents=True)
        qs.write_text(QUICKSTART.replace("__MAKE__", make).replace("__PLANT__", plant).replace("__MAIN__", main)
                      .replace("__FEATURE__", feature).replace("__DENIED__", denied).replace("__RC__", str(rc)))
        for b in bins:
            _write_stub(d / "_build/bin" / b, {}, "")
        sha = _git_repo(d)
        return {"GITAI_DIR": str(d), "GITAI_COMMIT": sha}

    def go(self, no_bwrap: bool = False, timeout: str = "", **kw) -> tuple[int, dict]:
        extra = self.stub(**kw)
        if timeout:
            extra["PFY_XINTAKE_TIMEOUT"] = timeout
        return self.run_entry("gitai", self.env(no_bwrap=no_bwrap, **extra))

    def test_happy_path_passes(self) -> None:
        self.assert_passed(*self.go())

    def test_missing_checkout_exits_2(self) -> None:
        code, r = self.run_entry("gitai", self.env(GITAI_DIR=str(self.base / "nope")))
        self.assertEqual(code, 2)
        self.assertIn("gitai not found", r["reason"])

    def test_unbuilt_exits_2(self) -> None:
        code, r = self.go(bins=("gitaly",))
        self.assertEqual(code, 2)
        self.assertIn("graft-cache", r["reason"])
        self.assertIn("never builds", r["reason"])

    def test_commit_pin_mismatch_exits_2(self) -> None:
        extra = self.stub()
        extra["GITAI_COMMIT"] = "f" * 40
        code, r = self.run_entry("gitai", self.env(**extra))
        self.assertEqual(code, 2)
        self.assertIn("not " + "f" * 40, r["reason"])

    def test_make_shim_refuses_other_targets(self) -> None:
        code, r = self.go(make='make -C "$repo_root" install')
        self.assert_failed(code, r, "quickstart_exit_0")
        self.assertIn("refusing", r["tail"])

    def test_nonzero_exit_fails(self) -> None:
        self.assert_failed(*self.go(rc=3), "quickstart_exit_0")

    def test_no_denial_fails(self) -> None:
        self.assert_failed(*self.go(denied="landed"), "policy_denied_builder")

    def test_denied_change_on_main_fails(self) -> None:
        self.assert_failed(*self.go(main="hello graft\\nnope\\n"), "planner_landed_on_main")

    def test_missing_feature_fails(self) -> None:
        self.assert_failed(*self.go(feature="other\\n"), "builder_landed_feature")

    def test_temp_home_write_fails(self) -> None:
        self.assert_failed(*self.go(plant='touch "$HOME/x"'), "home_untouched")

    def test_real_home_write_fails(self) -> None:
        code, r = self.go(no_bwrap=True, plant=f'mkdir -p "{self.home}/.config/graft" && touch "{self.home}/.config/graft/x"')
        self.assertEqual(code, 1, r)
        self.assertIn("~/.config/graft", r["reason"])

    def test_timeout_fails(self) -> None:
        code, r = self.go(timeout="1", plant="sleep 5")
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"]["body_completed"])
        self.assertIn("timeout after", r["reason"])


# ---------------------------------------------------------------- muxin
class MuxinTests(Base):
    def stub(self, **knobs) -> dict[str, str]:
        b = _write_stub(self.base / "bin/muxin", knobs, MUXIN)
        return {"MUXIN_BIN": str(b), "MUXIN_SHA256": hashlib.sha256(b.read_bytes()).hexdigest()}

    def go(self, no_bwrap: bool = False, **knobs) -> tuple[int, dict]:
        return self.run_entry("muxin", self.env(no_bwrap=no_bwrap, **self.stub(**knobs)))

    def test_happy_path_passes(self) -> None:
        code, r = self.go()
        self.assert_passed(code, r)
        self.assertEqual(r["tool_count"], 89)

    def test_missing_binary_exits_2(self) -> None:
        code, r = self.run_entry("muxin", self.env())
        self.assertEqual(code, 2)
        self.assertIn("muxin not found", r["reason"])

    def test_bad_override_exits_2(self) -> None:
        code, r = self.run_entry("muxin", self.env(MUXIN_BIN=str(self.base / "nope")))
        self.assertEqual(code, 2)
        self.assertIn("$MUXIN_BIN", r["reason"])

    def test_bad_lib_dir_exits_2(self) -> None:
        code, r = self.run_entry("muxin", self.env(MUXIN_LIB_DIR=str(self.base / "nolib"), **self.stub()))
        self.assertEqual(code, 2)
        self.assertIn("MUXIN_LIB_DIR", r["reason"])

    def test_sha_mismatch_exits_2(self) -> None:
        extra = self.stub()
        del extra["MUXIN_SHA256"]
        code, r = self.run_entry("muxin", self.env(**extra))
        self.assertEqual(code, 2)
        self.assertIn("b51e6fda", r["reason"])

    def test_version_mismatch_exits_2(self) -> None:
        code, r = self.go(version="0.5.9")
        self.assertEqual(code, 2)
        self.assertIn("0.5.9", r["reason"])

    def test_version_crash_fails(self) -> None:
        self.assert_failed(*self.go(version_rc=127), "version_runs")

    def test_paths_outside_fails(self) -> None:
        self.assert_failed(*self.go(paths_home=True), "paths_under_muxin_home")

    def test_machines_short_fails(self) -> None:
        self.assert_failed(*self.go(machines=8), "demo_machines_exact")

    def test_server_version_fails(self) -> None:
        self.assert_failed(*self.go(server_version="0.5.0"), "server_pinned")

    def test_few_tools_fails(self) -> None:
        self.assert_failed(*self.go(tools=10), "tools_listed")

    def test_unmarked_destructive_fails(self) -> None:
        self.assert_failed(*self.go(undestructive=True), "destructive_marked")

    def test_status_not_read_only_fails(self) -> None:
        self.assert_failed(*self.go(status_rw=True), "status_read_only")

    def test_status_summary_fails(self) -> None:
        self.assert_failed(*self.go(summary="8 machines"), "status_summary")

    def test_forge_missing_fails(self) -> None:
        self.assert_failed(*self.go(forge_missing=True), "get_machine_forge")

    def test_unknown_ok_fails(self) -> None:
        self.assert_failed(*self.go(unknown_ok=True), "unknown_not_found")

    def test_lax_args_fails(self) -> None:
        self.assert_failed(*self.go(lax_args=True), "bad_arg_invalid")

    def test_run_failed_fails(self) -> None:
        self.assert_failed(*self.go(run_status="failed"), "demo_run_succeeded")

    def test_ignore_eof_fails(self) -> None:
        self.assert_failed(*self.go(ignore_eof=True), "stopped_on_eof")

    def test_temp_home_write_fails(self) -> None:
        self.assert_failed(*self.go(home_write=True), "home_untouched")

    def test_driver_error_fails(self) -> None:
        self.assert_failed(*self.go(plant="import sys\nif sys.argv[1:] == ['mcp', '--demo']: sys.exit(3)"),
                           "driver_report")

    def test_real_home_write_fails(self) -> None:
        code, r = self.go(no_bwrap=True, plant=self.plant_home(".config/muxin"))
        self.assertEqual(code, 1, r)
        self.assertIn("~/.config/muxin", r["reason"])

    def test_timeout_fails(self) -> None:
        extra = self.stub(sleep=5)
        code, r = self.run_entry("muxin", self.env(PFY_XINTAKE_TIMEOUT="1", **extra))
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"]["body_completed"])
        self.assertIn("timeout after", r["reason"])


if __name__ == "__main__":
    unittest.main()
