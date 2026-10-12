"""Entries 106-108 smokes: cm sha pin/env, and har temp-HOME containment.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
Har is `node <realpath(HAR_BIN)>`; HAR_NODE is a stub that prints v22.0.0 and HAR_BIN is JavaScript.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "x-intake-local"))
from smoke_106_108 import CM_V050_SHA256  # noqa: E402

OTHER_SHA = "0123456789abcdef" * 4
REAL_NODE = shutil.which("node") or ""


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _node_stub(path: Path) -> None:
    _write_exe(path, f"""#!/bin/sh
if [ "$1" = "--version" ]; then
  echo v22.0.0
  exit 0
fi
exec {REAL_NODE} "$@"
""")


class XIntakeSmoke106108Tests(unittest.TestCase):
    def _base_env(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        for key in (
            "CM_BIN",
            "CM_SHA256",
            "HAR_BIN",
            "HAR_NODE",
            "PFY_XINTAKE_TIMEOUT",
            "PFY_PROBE_OUT",
            "XDG_CONFIG_HOME",
            "XDG_CACHE_HOME",
            "XDG_DATA_HOME",
            "npm_config_cache",
        ):
            env.pop(key, None)
        return env

    def _run(self, entry: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "examples/x-intake-local/smoke_106_108.py", "--entry", entry],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def _receipt(self, entry: str) -> dict:
        path = ROOT / "pipelines" / "smoke" / entry / "latest.json"
        self.assertTrue(path.is_file(), f"missing receipt {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _cm_sha(self, override: str | None) -> None:
        # Fail: a mismatched pin still execs, or the receipt omits expected source/value,
        # or an override is silent. Recover: exit 2, no exec, source pin or env, WARN only for env.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-cm-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            marker = root / "executed-marker"
            stub = root / "cm"
            _write_exe(stub, "#!/bin/sh\ntouch %s\n" % marker)
            env = self._base_env(home)
            env["CM_BIN"] = str(stub)
            if override is not None:
                env["CM_SHA256"] = override
            proc = self._run("cassmemory", env)
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 2, blob)
            self.assertFalse(marker.exists(), "cm stub was executed")
            self.assertNotIn("Traceback", proc.stderr)
            got = (self._receipt("cassmemory").get("expected") or {}).get("CM_SHA256") or {}
            if override is None:
                self.assertNotIn("WARN:", proc.stderr)
                self.assertEqual(got.get("source"), "pin", blob)
                self.assertEqual(got.get("value"), CM_V050_SHA256, blob)
            else:
                warn = f"WARN: $CM_SHA256={override} overrides the pinned {CM_V050_SHA256}"
                self.assertIn(warn, proc.stderr)
                self.assertEqual(got.get("source"), "env", blob)
                self.assertEqual(got.get("value"), override, blob)

    def test_cassmemory_sha_unset_records_pin_and_does_not_exec(self) -> None:
        self._cm_sha(None)

    def test_cassmemory_sha_env_warns_records_override_and_does_not_exec(self) -> None:
        self._cm_sha(OTHER_SHA)

    def _har_bins(self, root: Path, js: str) -> dict[str, str]:
        node = root / "node-stub"
        har = root / "har.js"
        _node_stub(node)
        _write_exe(har, js)
        return {"HAR_NODE": str(node), "HAR_BIN": str(har)}

    def test_har_work_dir_outside_temp_home_fails(self) -> None:
        # Fail: launch's work dir outside the temp HOME is accepted (startswith false-friend).
        # Recover: exit 1 and the reason says the work dir is not under the temp HOME.
        js = r"""
const fs = require('fs');
const args = process.argv.slice(2);
if (args[0] === 'telemetry') process.exit(0);
if (args[0] === 'env' && args[1] === 'init') {
  fs.mkdirSync('.har', {recursive: true});
  fs.writeFileSync('.har/stages.json', '{}\n');
  process.exit(0);
}
if (args[0] === 'env' && args[1] === 'launch') {
  console.log('make ALL file edits under: /tmp/outside-the-temp-home/work');
  process.exit(0);
}
if (args[0] === 'env' && args[1] === 'teardown') process.exit(0);
process.exit(3);
"""
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-har-out-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            env = self._base_env(home)
            env.update(self._har_bins(root, js))
            proc = self._run("har", env)
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 1, blob)
            self.assertNotIn("Traceback", proc.stderr)
            reason = self._receipt("har").get("reason") or ""
            self.assertIn("not under the temp HOME", reason, blob)

    def test_har_env_dirs_are_under_temp_home(self) -> None:
        # Fail: the har process inherits the parent HOME or XDG/npm cache paths outside its HOME.
        # Recover: HOME is a fresh temp dir and the four dirs sit under that HOME.
        js = r"""
const fs = require('fs');
const keys = ['HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'npm_config_cache'];
const out = {};
for (const k of keys) out[k] = process.env[k] || '';
fs.writeFileSync(process.env.PFY_PROBE_OUT, JSON.stringify(out));
process.exit(0);
"""
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-har-env-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            probe = root / "probe.json"
            env = self._base_env(home)
            env["PFY_PROBE_OUT"] = str(probe)
            env["XDG_CONFIG_HOME"] = str(home / ".config")
            env["XDG_CACHE_HOME"] = str(home / ".cache")
            env["XDG_DATA_HOME"] = str(home / ".local" / "share")
            env["npm_config_cache"] = str(home / ".npm")
            env.update(self._har_bins(root, js))
            proc = self._run("har", env)
            blob = proc.stdout + proc.stderr
            self.assertTrue(probe.is_file(), blob)
            data = json.loads(probe.read_text(encoding="utf-8"))
            seen = Path(data["HOME"]).resolve()
            self.assertNotEqual(seen, home.resolve(), data)
            for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "npm_config_cache"):
                got = Path(data[key]).resolve()
                self.assertTrue(got.is_relative_to(seen), f"{key}={data[key]} HOME={data['HOME']}")

    def test_har_otel_hooks_in_temp_home_fails(self) -> None:
        # Fail: $HOME/.har/otel-hooks written with telemetry off is ignored, so the smoke passes.
        # Recover: exit 1 and the reason names .har/otel-hooks, same as the other hook files.
        js = r"""
const fs = require('fs');
const path = require('path');
const args = process.argv.slice(2);
const home = process.env.HOME;
function done(code, text) {
  if (text) process.stdout.write(text.endsWith('\n') ? text : text + '\n');
  process.exit(code);
}
if (args[0] === 'telemetry') {
  fs.mkdirSync(path.join(home, '.har'), {recursive: true});
  fs.writeFileSync(path.join(home, '.har', 'otel-hooks'), '');
  done(0);
}
if (args[0] === 'env' && args[1] === 'init') {
  fs.mkdirSync('.har', {recursive: true});
  fs.writeFileSync('.har/stages.json', '{}\n');
  done(0);
}
if (args[0] === 'env' && args[1] === 'launch') {
  const work = path.join(home, 'slot-1');
  fs.mkdirSync(work, {recursive: true});
  fs.writeFileSync(path.join(home, 'work-path'), work);
  done(0, 'make ALL file edits under: ' + work);
}
if (args[0] === 'env' && args[1] === 'verify') {
  const marker = path.join(home, 'verify-seen');
  const seen = fs.existsSync(marker);
  fs.writeFileSync(marker, '1');
  if (!seen) done(0, JSON.stringify({status: 'pass', stages: [{name: 'unit-tests', pass: true}]}));
  done(1, JSON.stringify({status: 'fail', stages: [{name: 'unit-tests', pass: false}]}));
}
if (args[0] === 'env' && args[1] === 'teardown') {
  const work = fs.readFileSync(path.join(home, 'work-path'), 'utf8').trim();
  fs.rmSync(work, {recursive: true, force: true});
  done(0);
}
done(3, 'unexpected ' + args.join(' '));
"""
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-har-otel-") as td:
            root = Path(td)
            home = root / "home"
            home.mkdir()
            env = self._base_env(home)
            env.update(self._har_bins(root, js))
            proc = self._run("har", env)
            blob = proc.stdout + proc.stderr
            receipt = self._receipt("har")
            self.assertEqual(proc.returncode, 1, blob + "\n" + json.dumps(receipt))
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn(".har/otel-hooks", receipt.get("reason") or "", blob)


if __name__ == "__main__":
    unittest.main()
