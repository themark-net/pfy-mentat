"""Entries 146-147 smokes (skill-up, HiRoute): pins and missing prereqs exit 2; a validate that rejects the fixture, a
run that grades wrong, skips the agent or writes the temp HOME, an installer that lands outside the temp HOME, a daemon
that never gets ready, a gateway off loopback or forwarding without a grant, missing routing/decision commands and a
daemon that ignores SIGTERM FAIL; real-HOME writes FAIL. Every check the smoke records has a test here that turns it
false.

Each tool is a small Python stub (shebang = this interpreter) with knobs baked into its text, because the smoke gives
its children a clean env. skill-up: a fake binary answering --version, validate and run (it reads the case files,
calls the smoke's stub agent through $STUB_AGENT_BIN and writes iteration-1/result.json). HiRoute: a fake standalone.py
whose install writes a fake `hiroute` CLI and marker into the temp HOME; the CLI's `service run` serves a tiny HTTP
gateway on 127.0.0.1 and answers the status/gateway/schema commands. Parent HOME is a temp dir this test owns; the
skill-up real-HOME test sets PATH to an empty dir so bwrap is not found (children use a fixed system PATH). HiRoute
needs bwrap, so its real-HOME watch is tested in-process on `watched`. Receipts go to a temp $PFY_SMOKE_RECEIPT_DIR.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "examples/x-intake-local/smoke_146_147.py"
_RECEIPTS = tempfile.TemporaryDirectory(prefix="pfy-xintake-146-receipts-")
RECEIPT_DIR = Path(_RECEIPTS.name)
ARCHIVE = "hiroute-0.3.1-13856abd873d-x86_64-unknown-linux-gnu.tar.gz"


def tearDownModule() -> None:
    _RECEIPTS.cleanup()


def _write_stub(path: Path, knobs: dict, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!{sys.executable}\nK = {knobs!r}\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _bwrap_works() -> bool:
    if not shutil.which("bwrap"):
        return False
    p = subprocess.run(["bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--unshare-net", "true"],
                       capture_output=True)
    return p.returncode == 0


SKILLUP = r'''
import json, os, pathlib, re, subprocess, sys
a = sys.argv[1:]
if a == ["--version"]:
    print("skill-up version " + K.get("version", "0.14.0"))
    sys.exit(0)
if a[0] == "validate":
    if K.get("validate_bad"):
        print("Error: failed to load config")
        sys.exit(1)
    print("\u2713 eval.yaml is valid (loaded 2 case(s))")
    sys.exit(0)
if a[0] == "run":
    skill = pathlib.Path(a[1])
    out = pathlib.Path(a[a.index("--output-dir") + 1]) / "iteration-1"
    out.mkdir(parents=True, exist_ok=True)
    if K.get("write_home"):
        pathlib.Path(os.environ["HOME"], ".skill-up").mkdir()
    results, passed, failed = [], 0, 0
    for f in sorted((skill / "evals" / "cases").glob("*.yaml"), reverse=True):
        t = f.read_text()
        cid = re.search(r"^id: (.+)$", t, re.M).group(1)
        prompt = re.search(r"prompt: (.+)$", t, re.M).group(1)
        if K.get("no_call"):
            resp = "pong-7" if "ping" in prompt else "no-ping"
        else:
            inp = pathlib.Path(os.environ["TMPDIR"]) / f"skill-up-session-{cid}.json"
            keys = {"case_id": cid, "messages": [{"role": "user", "content": prompt}], "variant": "with_skill"}
            if K.get("no_messages"):
                keys.pop("messages")
            inp.write_text(json.dumps(keys))
            p = subprocess.run([os.environ["STUB_AGENT_BIN"], str(inp)], capture_output=True, text=True)
            resp = json.loads(p.stdout)["final_message"]
        ok = "pong-7" in resp or K.get("all_pass")
        if K.get("flip_response"):
            resp = "pong-7" if resp == "no-ping" else "no-ping"
        passed, failed = passed + bool(ok), failed + (not ok)
        ev = "all checks passed" if ok else 'output does not contain "pong-7"'
        if K.get("no_evidence"):
            ev = ""
        results.append({"case_id": cid, "status": "PASS" if ok else "FAIL", "response": resp,
                        "grading": {"assertion_results": [{"passed": bool(ok), "evidence": ev}]}})
    if not K.get("no_result"):
        (out / "result.json").write_text(json.dumps({"case_results": results}))
    print(K.get("summary", f"Results: {passed} passed, {failed} failed, 0 errors"))
    if K.get("touch_fixture"):
        (skill / "extra.txt").write_text("x")
    sys.exit(K.get("rc", 1 if failed else 0))
sys.exit(64)
'''

HIROUTE_CLI = r'''
import http.server, json, os, pathlib, signal, sys, threading, time
a = [x for x in sys.argv[1:] if x not in ("--output", "json")]
state = pathlib.Path(os.environ["XDG_RUNTIME_DIR"]) / "stub-hiroute.json"


def emit(data):
    print(json.dumps({"status": "succeeded", "data": data}))


if a == ["service", "run"]:
    if K.get("never_ready"):
        time.sleep(600)
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def reply(self, code, body):
            b = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            self.reply(*K.get("models", (503, {"code": "GATEWAY_PUBLICATION_UNAVAILABLE"})))

        def do_POST(self):
            self.rfile.read(int(self.headers.get("content-length") or 0))
            self.reply(*K.get("chat", (401, {"code": "GATEWAY_GRANT_UNAUTHORIZED"})))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    if K.get("ignore_term"):
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    else:
        signal.signal(signal.SIGTERM, lambda *x: sys.exit(0))
    state.write_text(json.dumps({"port": srv.server_address[1]}))
    while True:
        time.sleep(0.2)
up = state.is_file()
if a == ["service", "status"]:
    emit({"local_control_ready": up})
elif a == ["system", "status"]:
    emit({"daemon": K.get("role", "role_all") if up else None, "gateway": "ready" if up else None})
elif a == ["gateway", "show"]:
    port = json.loads(state.read_text())["port"] if up else None
    host = K.get("show_host", "127.0.0.1")
    emit({"ready": up, "connect_address": f"{host}:{port}" if up else None})
    if K.get("show_host"):
        pass
elif a == ["schema", "list"]:
    ids = ["routing.list", "routing.preview", "decision.services.list", "decision.services.test"]
    for d in K.get("drop", []):
        ids.remove(d)
    emit({"commands": [{"command_id": i} for i in ids]})
else:
    sys.exit(64)
'''

INSTALLER = r'''
import json, os, pathlib, sys
a = sys.argv[1:]
assert a[0] == "install" and "--manifest" in a and "--archive" in a, a
home = pathlib.Path(os.environ["HOME"])
if K.get("fail"):
    print("install failed")
    sys.exit(1)
b = home / ".local/bin"
b.mkdir(parents=True)
cli = b / "hiroute"
cli.write_text(K["cli"])
cli.chmod(0o755)
share = home / ".local/share/hiroute"
share.mkdir(parents=True)
root = K.get("root_override") or str(home / ".local/lib/hiroute/0.3.1")
marker = {"cpa_binary": str(share / "0.3.1/libexec/cliproxyapi"), "install_root": root,
          "service_definition": str(home / ".config/systemd/user/ai.hiroute.cli.service"),
          "installed_skills": [str(home / ".agents/skills/hiroute-management")], "version": "0.3.1"}
(share / "standalone.json").write_text(json.dumps(marker))
print(json.dumps({"installed": True, "marker": str(share / "standalone.json"), "version": K.get("version", "0.3.1")}))
'''


class Base(unittest.TestCase):
    PREFIXES = ("SKILLUP_", "HIROUTE_")

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory(prefix="pfy-xintake-146-test-")
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
                           capture_output=True, text=True, timeout=300)
        self.assertNotIn("Traceback", p.stderr + p.stdout)
        receipt = json.loads((RECEIPT_DIR / entry / "latest.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["exit_code"], p.returncode)
        return p.returncode, receipt

    def assert_failed(self, code: int, r: dict, check: str) -> None:
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"][check], r)
        self.assertIn(check, r["reason"])

    def assert_passed(self, code: int, r: dict) -> None:
        self.assertEqual(code, 0, r)
        self.assertTrue(r["checks"] and all(r["checks"].values()), r)


# ---------------------------------------------------------------- skill-up
class SkillUpTests(Base):
    def stub(self, **knobs) -> dict[str, str]:
        b = _write_stub(self.base / "bin/skill-up", knobs, SKILLUP)
        return {"SKILLUP_BIN": str(b), "SKILLUP_SHA256": _sha(b)}

    def go(self, no_bwrap: bool = False, **knobs) -> tuple[int, dict]:
        return self.run_entry("skill-up", self.env(no_bwrap=no_bwrap, **self.stub(**knobs)))

    def test_happy_path_passes(self) -> None:
        code, r = self.go()
        self.assert_passed(code, r)
        self.assertEqual(r["cases"]["ping-pass"], {"status": "PASS", "response": "pong-7"})

    def test_missing_binary_exits_2(self) -> None:
        code, r = self.run_entry("skill-up", self.env(PATH=str(self.nobwrap)))
        self.assertEqual(code, 2, r)
        self.assertIn("skill-up not found", r["reason"])

    def test_bad_override_exits_2(self) -> None:
        code, r = self.run_entry("skill-up", self.env(SKILLUP_BIN=str(self.base / "nope")))
        self.assertEqual(code, 2, r)
        self.assertIn("not an executable file", r["reason"])

    def test_sha_mismatch_exits_2(self) -> None:
        extra = self.stub()
        extra["SKILLUP_SHA256"] = "0" * 64
        code, r = self.run_entry("skill-up", self.env(**extra))
        self.assertEqual(code, 2, r)
        self.assertIn("sha256", r["reason"])

    def test_pinned_sha_without_override_exits_2(self) -> None:
        extra = self.stub()
        extra.pop("SKILLUP_SHA256")
        code, r = self.run_entry("skill-up", self.env(**extra))
        self.assertEqual(code, 2, r)

    def test_wrong_version_exits_2(self) -> None:
        code, r = self.go(version="0.13.9")
        self.assertEqual(code, 2, r)
        self.assertIn("skill-up version 0.14.0", r["reason"])

    def test_bad_timeout_exits_2(self) -> None:
        code, r = self.run_entry("skill-up", self.env(**self.stub(), PFY_XINTAKE_TIMEOUT="-1"))
        self.assertEqual(code, 2, r)

    def test_validate_rejects(self) -> None:
        self.assert_failed(*self.go(validate_bad=True), "validate_ok")

    def test_all_pass_fails_exit_and_grading(self) -> None:
        code, r = self.go(all_pass=True)
        self.assert_failed(code, r, "run_exit_1")
        self.assertFalse(r["checks"]["hello_fail"])
        self.assertFalse(r["checks"]["run_summary"])

    def test_wrong_summary(self) -> None:
        self.assert_failed(*self.go(summary="Results: done"), "run_summary")

    def test_flipped_responses(self) -> None:
        code, r = self.go(flip_response=True)
        self.assert_failed(code, r, "ping_pass")
        self.assertFalse(r["checks"]["hello_fail"])

    def test_missing_evidence(self) -> None:
        self.assert_failed(*self.go(no_evidence=True), "hello_fail")

    def test_no_result_json(self) -> None:
        code, r = self.go(no_result=True)
        self.assert_failed(code, r, "ping_pass")

    def test_agent_never_called(self) -> None:
        self.assert_failed(*self.go(no_call=True), "stub_got_session_input")

    def test_session_input_without_messages(self) -> None:
        self.assert_failed(*self.go(no_messages=True), "stub_got_session_input")

    def test_temp_home_write(self) -> None:
        self.assert_failed(*self.go(write_home=True), "temp_home_empty")

    def test_fixture_touched(self) -> None:
        self.assert_failed(*self.go(touch_fixture=True), "fixture_unchanged")

    def test_real_home_write_fails(self) -> None:
        b = _write_stub(self.base / "bin/skill-up", {}, SKILLUP.replace(
            'if a[0] == "run":', f'if a[0] == "run":\n    pathlib.Path({str(self.home)!r}, ".skill-up").mkdir()', 1))
        code, r = self.run_entry("skill-up", self.env(no_bwrap=True, SKILLUP_BIN=str(b), SKILLUP_SHA256=_sha(b)))
        self.assertEqual(code, 1, r)
        self.assertFalse(r["checks"]["real_home_untouched"])
        self.assertEqual(r["real_home_changed"], ["~/.skill-up"])
        self.assertIn("real HOME ~/.skill-up changed", r["reason"])


# ---------------------------------------------------------------- hiroute
@unittest.skipUnless(_bwrap_works(), "the hiroute smoke needs a working bwrap")
class HiRouteTests(Base):
    def stage(self, cli: dict | None = None, **knobs) -> dict[str, str]:
        d = self.base / "hrstage"
        d.mkdir(exist_ok=True)
        (d / ARCHIVE).write_bytes(b"archive")
        (d / (ARCHIVE + ".json")).write_text("{}")
        cli_text = f"#!{sys.executable}\nK = {(cli or {})!r}\n" + HIROUTE_CLI
        _write_stub(d / "standalone.py", {"cli": cli_text, **knobs}, INSTALLER)
        return {"HIROUTE_DIR": str(d), "HIROUTE_ARCHIVE_SHA256": _sha(d / ARCHIVE),
                "HIROUTE_MANIFEST_SHA256": _sha(d / (ARCHIVE + ".json")),
                "HIROUTE_INSTALLER_SHA256": _sha(d / "standalone.py"), "HIROUTE_TERM_WAIT": "3"}

    def go(self, cli: dict | None = None, **knobs) -> tuple[int, dict]:
        return self.run_entry("hiroute", self.env(**self.stage(cli, **knobs)))

    def test_happy_path_passes(self) -> None:
        code, r = self.go()
        self.assert_passed(code, r)

    def test_not_staged_exits_2(self) -> None:
        code, r = self.run_entry("hiroute", self.env(HIROUTE_DIR=str(self.base / "none")))
        self.assertEqual(code, 2, r)
        self.assertIn("not staged", r["reason"])

    def test_no_bwrap_exits_2(self) -> None:
        code, r = self.run_entry("hiroute", self.env(no_bwrap=True, **self.stage()))
        self.assertEqual(code, 2, r)
        self.assertIn("bwrap", r["reason"])

    def test_sha_mismatch_exits_2(self) -> None:
        for var in ("HIROUTE_ARCHIVE_SHA256", "HIROUTE_MANIFEST_SHA256", "HIROUTE_INSTALLER_SHA256"):
            with self.subTest(var=var):
                extra = self.stage()
                extra[var] = "f" * 64
                code, r = self.run_entry("hiroute", self.env(**extra))
                self.assertEqual(code, 2, r)
                self.assertIn("sha256", r["reason"])

    def test_pinned_shas_reject_stub(self) -> None:
        extra = self.stage()
        extra.pop("HIROUTE_ARCHIVE_SHA256")
        code, r = self.run_entry("hiroute", self.env(**extra))
        self.assertEqual(code, 2, r)

    def test_install_fails(self) -> None:
        code, r = self.go(fail=True)
        self.assert_failed(code, r, "installed")

    def test_wrong_version(self) -> None:
        self.assert_failed(*self.go(version="0.3.0"), "installed")

    def test_install_outside_temp_home(self) -> None:
        self.assert_failed(*self.go(root_override="/opt/hiroute"), "install_under_temp_home")

    def test_never_ready(self) -> None:
        code, r = self.go(cli={"never_ready": True})
        self.assert_failed(code, r, "local_control_ready")

    def test_wrong_role(self) -> None:
        self.assert_failed(*self.go(cli={"role": "role_gateway"}), "daemon_role_all")

    def test_gateway_not_loopback(self) -> None:
        self.assert_failed(*self.go(cli={"show_host": "0.0.0.0"}), "gateway_loopback")

    def test_models_published(self) -> None:
        self.assert_failed(*self.go(cli={"models": [200, {"data": []}]}), "unpublished_models_503")

    def test_chat_forwarded(self) -> None:
        self.assert_failed(*self.go(cli={"chat": [200, {"choices": []}]}), "ungranted_chat_401")

    def test_chat_wrong_error_code(self) -> None:
        self.assert_failed(*self.go(cli={"chat": [401, {"code": "OTHER"}]}), "ungranted_chat_401")

    def test_schema_missing_decision(self) -> None:
        self.assert_failed(*self.go(cli={"drop": ["decision.services.test"]}), "schema_routing_decision")

    def test_ignores_sigterm(self) -> None:
        self.assert_failed(*self.go(cli={"ignore_term": True}), "sigterm_exit")


class HiRouteWatchTests(unittest.TestCase):
    """The hiroute smoke needs bwrap, whose read-only root stops a stub from writing the parent's HOME, so the real-HOME
    watch is checked in-process: `watched` must FAIL for a write to any watched path."""

    def test_real_home_write_fails_for_each_watched_path(self) -> None:
        sys.path.insert(0, str(ROOT / "examples/x-intake-local"))
        try:
            mod = importlib.import_module("smoke_146_147")
        finally:
            sys.path.pop(0)
        old = os.environ.get("HOME")
        for rel in mod.WATCH["hiroute"]:
            with self.subTest(rel=rel), tempfile.TemporaryDirectory() as h:
                os.environ["HOME"] = h

                def body(r, checks, rel=rel, h=h):
                    t = Path(h) / rel
                    t.parent.mkdir(parents=True, exist_ok=True)
                    t.write_text("planted")
                    checks["ok"] = True
                    r["_ok_reason"] = "ok"
                    return None
                r: dict = {}
                try:
                    code = mod.watched("hiroute", body, r)
                finally:
                    if old is None:
                        os.environ.pop("HOME", None)
                    else:
                        os.environ["HOME"] = old
                self.assertEqual(code, 1, r)
                self.assertEqual(r["real_home_changed"], ["~/" + rel])
                self.assertIn("real HOME", r["reason"])


if __name__ == "__main__":
    unittest.main()
