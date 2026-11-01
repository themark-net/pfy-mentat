"""Behavior tests for the harness2-local stage.

Drive stage.sh and check.py as subprocesses. A stub git/uv/npm/bun records the
environment it actually received. Nothing here loads a model or calls harness2-setup.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "examples" / "harness2-local" / "stage.sh"
CHECK = ROOT / "examples" / "harness2-local" / "check.py"
sys.path.insert(0, str(ROOT / "examples" / "harness2-local"))

import common  # noqa: E402

def _scratch() -> Path:
    path = ROOT / "tmp" / "stage-tests"
    path.mkdir(parents=True, exist_ok=True)
    return path


H2_PIN = common.H2_PIN
OC_PIN = common.OC_PIN
CACHE_KEYS = (
    "UV_CACHE_DIR",
    "UV_PYTHON_INSTALL_DIR",
    "UV_PYTHON_BIN_DIR",
    "UV_TOOL_DIR",
    "npm_config_cache",
    "BUN_INSTALL_CACHE_DIR",
    "BUN_INSTALL",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
    "OPENCODE_CONFIG",
)

TOOL_STUB = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
keys = %(keys)s
rec = {"name": name, "argv": sys.argv, "env": {k: os.environ.get(k) for k in keys}}
with Path(os.environ["STUB_LOG"]).open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec) + "\n")
if name == "git":
    args = sys.argv[1:]
    cdir = None
    if "-C" in args:
        i = args.index("-C")
        cdir = args[i + 1]
        rest = args[i + 2:]
    else:
        rest = args
    if rest and rest[0] == "clone":
        dest = Path(rest[-1])
        dest.mkdir(parents=True, exist_ok=True)
        (dest / ".git").mkdir(exist_ok=True)
    elif rest and rest[0] == "init":
        dest = Path(rest[-1])
        dest.mkdir(parents=True, exist_ok=True)
        (dest / ".git").mkdir(exist_ok=True)
    elif "rev-parse" in rest:
        if cdir and "dependencies/opencode" in cdir:
            print(os.environ.get("STUB_OC_HEAD", %(oc)r))
        else:
            print(os.environ.get("STUB_H2_HEAD", %(h2)r))
    if os.environ.get("STUB_TOUCH_HOME") == "1":
        touched = Path(os.environ["HOME"]) / ".npm" / "touched"
        touched.parent.mkdir(parents=True, exist_ok=True)
        touched.write_text("touched", encoding="utf-8")
    write_path = os.environ.get("STUB_WRITE_PATH")
    if write_path:
        Path(write_path).write_text("leak", encoding="utf-8")
    raise SystemExit(0)
if name == "uv":
    if "venv" in sys.argv:
        dest = Path(sys.argv[-1])
        (dest / "bin").mkdir(parents=True, exist_ok=True)
        py = dest / "bin" / "python"
        py.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        py.chmod(0o755)
    raise SystemExit(0)
if name == "npm":
    prefix = Path(sys.argv[sys.argv.index("--prefix") + 1])
    bindir = prefix / "node_modules" / ".bin"
    bindir.mkdir(parents=True, exist_ok=True)
    link = bindir / "bun"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(os.environ["STUB_PY"])
    raise SystemExit(0)
if name == "bun" and "--version" in sys.argv:
    print("local")
raise SystemExit(0)
""" % {
    "keys": repr(list(CACHE_KEYS) + ["UV_PYTHON_DOWNLOADS", "npm_config_update_notifier"]),
    "oc": OC_PIN,
    "h2": H2_PIN,
}

GIT_STUB = textwrap.dedent(
    f"""\
    #!/usr/bin/env python3
    import sys
    args = sys.argv[1:]
    cdir = ""
    if "-C" in args:
        i = args.index("-C")
        cdir = args[i + 1]
        rest = args[i + 2:]
    else:
        rest = args
    if "rev-parse" in rest:
        if "dependencies/opencode" in cdir:
            print("{OC_PIN}")
        else:
            print("{H2_PIN}")
    raise SystemExit(0)
    """
)

CHECK_CHILD = textwrap.dedent(
    """\
    import importlib.util
    import os
    import sys
    from pathlib import Path
    sys.path.insert(0, os.environ["STUB_PKG"])
    spec = importlib.util.spec_from_file_location("h2check", os.environ["CHECK"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rc = mod.main(["--root", os.environ["STAGE"]])
    Path(os.environ["MODS"]).write_text("\\n".join(sorted(sys.modules)), encoding="utf-8")
    raise SystemExit(rc)
    """
)


def _write_exec(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class HomeWatch(unittest.TestCase):
    """Fingerprint a private home, never the operator ~/.cache/uv.

    tearDown used to hash Path.home(), so a concurrent uv (CI 41262832115,
    pregate 16f17d8) changed .cache/uv while the digest was taken. HOME and
    UV_CACHE_DIR for the test process stay under the scratch dir. The
    operator cache is a separate stand-in the watch does not read.
    """

    def setUp(self):
        self._watch_dir = tempfile.TemporaryDirectory(dir=_scratch())
        root = Path(self._watch_dir.name)
        self.private_home = root / "home"
        self.private_uv_cache = root / "uv-cache"
        self.private_home.mkdir()
        self.private_uv_cache.mkdir()
        self._saved_home = os.environ.get("HOME")
        self._saved_uv = os.environ.get("UV_CACHE_DIR")
        os.environ["HOME"] = str(self.private_home)
        os.environ["UV_CACHE_DIR"] = str(self.private_uv_cache)
        self.home_before = common.home_snapshot(self.private_home)

    def tearDown(self):
        try:
            changed = common.snapshot_diff(
                self.home_before, common.home_snapshot(self.private_home)
            )
            self.assertEqual(changed, [])
        finally:
            if self._saved_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = self._saved_home
            if self._saved_uv is None:
                os.environ.pop("UV_CACHE_DIR", None)
            else:
                os.environ["UV_CACHE_DIR"] = self._saved_uv
            self._watch_dir.cleanup()


class HomeWatchIsolationTests(HomeWatch):
    def test_operator_cache_churn_does_not_fail_and_a_sealed_write_is_refused(self):
        # Fail: tearDown hashes the operator uv stand-in, or the test can
        # write that path. Recover: the private home stays empty, the sealed
        # stand-in rejects a write, and the private UV cache still accepts one.
        operator = Path(self._watch_dir.name) / "operator-home"
        real_uv = operator / ".cache" / "uv"
        real_uv.mkdir(parents=True)
        (real_uv / "seed").write_text("seed", encoding="utf-8")
        before_operator = common.home_snapshot(operator)
        stop = threading.Event()

        def churn() -> None:
            for n in range(40):
                if stop.is_set():
                    return
                (real_uv / f"c{n}").write_text("x", encoding="utf-8")
                if stop.wait(0.02):
                    return

        thr = threading.Thread(target=churn, daemon=True)
        thr.start()
        try:
            self.assertEqual(os.environ["HOME"], str(self.private_home))
            self.assertEqual(os.environ["UV_CACHE_DIR"], str(self.private_uv_cache))
            self.assertFalse(str(self.private_uv_cache).startswith(str(operator)))
            self.assertEqual(
                common.snapshot_diff(
                    self.home_before, common.home_snapshot(self.private_home)
                ),
                [],
            )
        finally:
            stop.set()
            thr.join(timeout=2)
        self.assertIn(
            ".cache/uv",
            common.snapshot_diff(before_operator, common.home_snapshot(operator)),
        )
        os.chmod(real_uv, 0o555)
        try:
            with self.assertRaises(PermissionError):
                (real_uv / "leak").write_text("no", encoding="utf-8")
        finally:
            os.chmod(real_uv, 0o755)
        (self.private_uv_cache / "ok").write_text("ok", encoding="utf-8")
        self.assertEqual((self.private_uv_cache / "ok").read_text(encoding="utf-8"), "ok")


class CheckTests(HomeWatch):
    def _stage(self, root: Path, version: str, solver: str | None = "llamacpp/qwen3.6-35b") -> None:
        oc = root / "dependencies" / "opencode"
        pkg_dir = oc / "packages" / "opencode"
        pkg_dir.joinpath("src").mkdir(parents=True)
        (pkg_dir / "src" / "index.ts").write_text("// stub\n", encoding="utf-8")
        (pkg_dir / "package.json").write_text(
            json.dumps({"name": "opencode", "version": version}) + "\n", encoding="utf-8"
        )
        bindir = root / "dependencies" / "tools" / "node_modules" / ".bin"
        bindir.mkdir(parents=True)
        _write_exec(
            bindir / "bun",
            "#!/usr/bin/env python3\nimport sys\n"
            "if '--version' in sys.argv:\n    print('local')\nraise SystemExit(0)\n",
        )
        patch = root / "third_party" / "patches"
        patch.mkdir(parents=True)
        (patch / "opencode-compat.diff").write_text("# stub patch\n", encoding="utf-8")
        lines = [
            "HARNESS2_IMPROVER_MODEL=llamacpp/qwen3.6-35b",
            "HARNESS2_RUNS_DIR=/tmp/harness2-runs-stub",
        ]
        if solver is not None:
            lines.insert(0, f"HARNESS2_SOLVER_MODEL={solver}")
        (root / ".env").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _pkg(self, pkg: Path, root: Path) -> None:
        sub = pkg / "harness2" / "substrate"
        sub.mkdir(parents=True)
        (pkg / "harness2" / "__init__.py").write_text("", encoding="utf-8")
        (sub / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "harness2" / "config.py").write_text(
            "import pathlib\n"
            f"ROOT = pathlib.Path({str(root)!r})\n"
            "BUN = ROOT / 'dependencies/tools/node_modules/.bin/bun'\n"
            "OPENCODE_DIR = ROOT / 'dependencies/opencode'\n",
            encoding="utf-8",
        )
        (sub / "opencode.py").write_text(
            "import pathlib\n"
            "from harness2 import config\n"
            "class OpencodeSubstrate:\n"
            "    def preflight(self):\n"
            "        if not isinstance(config.BUN, pathlib.Path):\n"
            "            raise AttributeError('config.BUN is not a Path')\n"
            "        if not config.BUN.is_file():\n"
            "            raise SystemExit('bun missing')\n"
            "        if not pathlib.Path(config.OPENCODE_DIR).exists():\n"
            "            raise SystemExit('opencode missing')\n"
            "        return None\n",
            encoding="utf-8",
        )

    def _run(self, stage: Path, pkg: Path) -> subprocess.CompletedProcess[str]:
        bindir = stage.parent / "bin"
        bindir.mkdir(exist_ok=True)
        _write_exec(bindir / "git", GIT_STUB)
        marker = stage.parent / "harness2-check.marker"
        _write_exec(
            bindir / "harness2-check",
            "#!/bin/sh\necho called >> \"$H2CHECK_MARKER\"\nexit 99\n",
        )
        mods = stage.parent / "modules.txt"
        env = os.environ.copy()
        env["PATH"] = f"{bindir}:/usr/bin:/bin"
        env["STUB_PKG"] = str(pkg)
        env["CHECK"] = str(CHECK)
        env["STAGE"] = str(stage)
        env["MODS"] = str(mods)
        env["H2CHECK_MARKER"] = str(marker)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["HARNESS2_CHECK_NO_VENV"] = "1"
        return subprocess.run(
            [sys.executable, "-c", CHECK_CHILD],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_stub_stage_exits_0_without_preflight_module_or_harness2_check(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            root = Path(tmp)
            stage = root / "stage"
            self._stage(stage, "1.14.18")
            pkg = root / "pkg"
            self._pkg(pkg, stage)
            proc = self._run(stage, pkg)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("check: ok", proc.stdout)
            mods = (root / "modules.txt").read_text(encoding="utf-8")
            self.assertNotIn("harness2.preflight", mods.splitlines())
            self.assertIn("harness2.substrate.opencode", mods.splitlines())
            self.assertFalse((root / "harness2-check.marker").exists())

    def test_package_json_117_exits_2_naming_the_version(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            root = Path(tmp)
            stage = root / "stage"
            self._stage(stage, "1.14.17")
            pkg = root / "pkg"
            self._pkg(pkg, stage)
            proc = self._run(stage, pkg)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("1.14.17", proc.stderr)
            self.assertIn("1.14.18", proc.stderr)

    def test_missing_solver_model_exits_2_and_restore_passes(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            root = Path(tmp)
            stage = root / "stage"
            self._stage(stage, "1.14.18")
            pkg = root / "pkg"
            self._pkg(pkg, stage)
            env_path = stage / ".env"
            original = env_path.read_text(encoding="utf-8")
            env_path.write_text(
                original.replace("HARNESS2_SOLVER_MODEL=llamacpp/qwen3.6-35b\n", ""),
                encoding="utf-8",
            )
            broken = self._run(stage, pkg)
            self.assertEqual(broken.returncode, 2, broken.stdout + broken.stderr)
            self.assertIn("HARNESS2_SOLVER_MODEL", broken.stderr)
            env_path.write_text(original, encoding="utf-8")
            restored = self._run(stage, pkg)
            self.assertEqual(restored.returncode, 0, restored.stderr)

    def test_vertex_model_exits_2(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            root = Path(tmp)
            stage = root / "stage"
            self._stage(stage, "1.14.18", solver="google-vertex/gemini-x")
            pkg = root / "pkg"
            self._pkg(pkg, stage)
            proc = self._run(stage, pkg)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("Vertex is not allowed", proc.stderr)


class StageScriptTests(unittest.TestCase):
    """The stage script is checked against its private HOME.

    HomeWatch hashes the operator ~/.cache/uv and ~/.npm. Other jobs rewrite
    those trees while a suite runs, so tearDown failed this class even when
    stage.sh never wrote them (pregate 16f17d8, assertion on .cache/uv).
    """

    def _stub_env(self, work: Path) -> dict[str, str]:
        bindir = work / "bin"
        bindir.mkdir(parents=True, exist_ok=True)
        stub = work / "toolstub.py"
        _write_exec(stub, TOOL_STUB)
        for name in ("git", "uv", "npm", "bun"):
            link = bindir / name
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(stub)
        home = work / "home"
        py_link = (
            home / ".local/share/uv/python/cpython-3.12.9-linux-x86_64-gnu/bin/python3.12"
        )
        py_link.parent.mkdir(parents=True, exist_ok=True)
        py_link.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        py_link.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{bindir}:/usr/bin:/bin"
        env["HOME"] = str(home)
        env["HARNESS2_W"] = str(work / "wt")
        env["HARNESS2_PY312"] = str(py_link)
        env["STUB_LOG"] = str(work / "stub.log")
        env["STUB_PY"] = str(stub)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # env.sh fills these only when unset. A caller value must not leak in.
        env.pop("XDG_DATA_HOME", None)
        env.pop("XDG_STATE_HOME", None)
        (work / "stub.log").write_text("", encoding="utf-8")
        return env

    def _records(self, work: Path) -> list[dict]:
        text = (work / "stub.log").read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]

    def test_dry_run_picks_another_312_patch_without_the_override(self):
        # No HARNESS2_PY312 and no 3.12.12: the glob fallback must find 3.12.9.
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            env = self._stub_env(work)
            env.pop("HARNESS2_PY312")
            other = Path(env["HOME"]) / ".local/share/uv/python/cpython-3.12.9-linux-x86_64-gnu/bin/python3.12"
            self.assertTrue(other.is_file())
            proc = subprocess.run(
                ["bash", str(STAGE), "--dry-run"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            step = [line for line in proc.stdout.splitlines() if line.startswith("2. ")]
            self.assertEqual(len(step), 1, proc.stdout)
            self.assertIn(f"realpath {other}", step[0])
            self.assertNotIn("cpython-3.12.12", step[0])

    def _assert_cache_contract(self, work: Path, env: dict[str, str], blob: str) -> None:
        state = str(Path(env["HARNESS2_W"]) / "tmp" / "state")
        records = self._records(work)
        names = {rec["name"] for rec in records}
        self.assertTrue({"git", "uv", "npm", "bun"} <= names, blob + "\n" + str(names))
        for rec in records:
            got = rec["env"]
            self.assertEqual(got.get("UV_PYTHON_DOWNLOADS"), "never", rec["name"])
            self.assertEqual(got.get("npm_config_update_notifier"), "false", rec["name"])
            for key in CACHE_KEYS:
                value = got.get(key)
                self.assertTrue(
                    isinstance(value, str) and value.startswith(state),
                    f"{rec['name']} {key}={value!r}\n{blob}",
                )

    def test_stub_tools_see_state_caches_and_home_stays(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            env = self._stub_env(work)
            home = Path(env["HOME"])
            before = common.home_snapshot(home)
            proc = subprocess.run(
                ["bash", str(STAGE)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            blob = f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            # step 6 can exit 2 when the git stub skips the real patch file.
            # The contract here is the tool environment and the private HOME.
            self.assertNotIn("BLOCKED: home-write", proc.stderr, blob)
            self._assert_cache_contract(work, env, blob)
            changed = common.snapshot_diff(before, common.home_snapshot(home))
            self.assertEqual(changed, [], blob)

    def test_private_home_write_blocks_then_clean_rerun_recovers(self):
        # A tool that writes the private HOME must fail closed. The same tree
        # with that write removed must then pass the cache contract.
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            env = self._stub_env(work)
            env["STUB_TOUCH_HOME"] = "1"
            home = Path(env["HOME"])
            before = common.home_snapshot(home)
            blocked = subprocess.run(
                ["bash", str(STAGE)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            blocked_blob = f"stdout:\n{blocked.stdout}\nstderr:\n{blocked.stderr}"
            self.assertEqual(blocked.returncode, 2, blocked_blob)
            self.assertIn("BLOCKED: home-write", blocked.stderr)
            self.assertIn(".npm", common.snapshot_diff(before, common.home_snapshot(home)))
            touched = home / ".npm" / "touched"
            touched.unlink()
            env.pop("STUB_TOUCH_HOME")
            (work / "stub.log").write_text("", encoding="utf-8")
            recovered_before = common.home_snapshot(home)
            recovered = subprocess.run(
                ["bash", str(STAGE)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            recovered_blob = f"stdout:\n{recovered.stdout}\nstderr:\n{recovered.stderr}"
            self.assertNotIn("BLOCKED: home-write", recovered.stderr, recovered_blob)
            self._assert_cache_contract(work, env, recovered_blob)
            changed = common.snapshot_diff(recovered_before, common.home_snapshot(home))
            self.assertEqual(changed, [], recovered_blob)

    def _run_stage(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(STAGE)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_operator_cache_churn_is_ignored_and_real_cache_write_fails(self):
        # Fail: the contract fingerprints a stand-in of the operator uv cache,
        # or a tool writes that path. Recover: churn there while stage.sh runs
        # against a private HOME and the state UV cache, then a sealed write
        # fails the tool, then a clean rerun passes.
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            operator = work / "operator-home"
            real_uv = operator / ".cache" / "uv"
            real_uv.mkdir(parents=True)
            (real_uv / "seed").write_text("seed", encoding="utf-8")
            before_operator = common.home_snapshot(operator)
            stop = threading.Event()

            def churn() -> None:
                for n in range(40):
                    if stop.is_set():
                        return
                    (real_uv / f"c{n}").write_text("x", encoding="utf-8")
                    if stop.wait(0.05):
                        return

            thr = threading.Thread(target=churn, daemon=True)
            thr.start()
            try:
                env = self._stub_env(work)
                env["UV_CACHE_DIR"] = str(real_uv)
                home = Path(env["HOME"])
                self.assertNotEqual(home.resolve(), operator.resolve())
                before_private = common.home_snapshot(home)
                passed = self._run_stage(env)
                blob = f"stdout:\n{passed.stdout}\nstderr:\n{passed.stderr}"
                self.assertNotIn("BLOCKED: home-write", passed.stderr, blob)
                self._assert_cache_contract(work, env, blob)
                self.assertEqual(
                    common.snapshot_diff(before_private, common.home_snapshot(home)),
                    [],
                    blob,
                )
                for rec in self._records(work):
                    seen = rec["env"].get("UV_CACHE_DIR")
                    self.assertFalse(
                        str(seen).startswith(str(real_uv)),
                        f"{rec['name']} leaked the operator cache: {seen}",
                    )
            finally:
                stop.set()
                thr.join(timeout=2)

            changed_operator = common.snapshot_diff(
                before_operator, common.home_snapshot(operator)
            )
            self.assertIn(".cache/uv", changed_operator)

            leak = real_uv / "leak"
            os.chmod(real_uv, 0o555)
            try:
                with self.assertRaises(PermissionError):
                    leak.write_text("leak", encoding="utf-8")
                env = self._stub_env(work)
                env["STUB_WRITE_PATH"] = str(leak)
                (work / "stub.log").write_text("", encoding="utf-8")
                blocked = self._run_stage(env)
                blocked_blob = f"stdout:\n{blocked.stdout}\nstderr:\n{blocked.stderr}"
                self.assertNotEqual(blocked.returncode, 0, blocked_blob)
                self.assertIn("PermissionError", blocked.stderr, blocked_blob)
                self.assertFalse(leak.exists())
            finally:
                os.chmod(real_uv, 0o755)

            env = self._stub_env(work)
            env.pop("STUB_WRITE_PATH", None)
            (work / "stub.log").write_text("", encoding="utf-8")
            home = Path(env["HOME"])
            recovered_before = common.home_snapshot(home)
            recovered = self._run_stage(env)
            recovered_blob = f"stdout:\n{recovered.stdout}\nstderr:\n{recovered.stderr}"
            self.assertNotIn("BLOCKED: home-write", recovered.stderr, recovered_blob)
            self._assert_cache_contract(work, env, recovered_blob)
            self.assertEqual(
                common.snapshot_diff(recovered_before, common.home_snapshot(home)),
                [],
                recovered_blob,
            )
            self.assertFalse(leak.exists())

    def test_existing_env_file_is_kept_byte_identical(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            env = self._stub_env(work)
            h2 = Path(env["HARNESS2_W"]) / "tmp" / "harness2"
            h2.mkdir(parents=True)
            (h2 / ".git").mkdir()
            payload = (
                "HARNESS2_SOLVER_MODEL=llamacpp/qwen3.6-35b\n"
                "HARNESS2_IMPROVER_MODEL=llamacpp/qwen3.6-35b\n"
                "HARNESS2_RUNS_DIR=/keep/this\n"
                "KEEP=1\n"
            ).encode()
            (h2 / ".env").write_bytes(payload)
            oc = h2 / "dependencies" / "opencode"
            pkg = oc / "packages" / "opencode"
            pkg.mkdir(parents=True)
            (pkg / "package.json").write_text(
                '{"version": "1.14.18"}\n', encoding="utf-8"
            )
            patch = h2 / "third_party" / "patches"
            patch.mkdir(parents=True)
            (patch / "opencode-compat.diff").write_text("diff --git a/a b/a\n", encoding="utf-8")
            fake = work / "fakeh2"
            (fake / "harness2" / "substrate").mkdir(parents=True)
            (fake / "harness2" / "__init__.py").write_text("", encoding="utf-8")
            (fake / "harness2" / "substrate" / "__init__.py").write_text("", encoding="utf-8")
            (fake / "harness2" / "config.py").write_text(
                "import os\nfrom pathlib import Path\n"
                "OPENCODE_DIR = Path(os.environ['HARNESS2_STUB_OC'])\n"
                "BUN = Path(os.environ['STUB_PY'])\n",
                encoding="utf-8",
            )
            (fake / "harness2" / "substrate" / "opencode.py").write_text(
                "class OpencodeSubstrate:\n"
                "    def preflight(self):\n"
                "        return None\n",
                encoding="utf-8",
            )
            env["PYTHONPATH"] = str(fake)
            env["HARNESS2_STUB_OC"] = str(oc)
            proc = subprocess.run(
                ["bash", str(STAGE)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("env: kept existing .env", proc.stdout)
            self.assertNotIn("BLOCKED: home-write", proc.stderr)
            self.assertEqual((h2 / ".env").read_bytes(), payload)
            self.assertNotIn("env: written from env.local.example", proc.stdout)

    def test_wrong_existing_pin_is_refused(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            env = self._stub_env(work)
            env["STUB_H2_HEAD"] = "deadbeef"
            h2 = Path(env["HARNESS2_W"]) / "tmp" / "harness2"
            h2.mkdir(parents=True)
            (h2 / ".git").mkdir()
            proc = subprocess.run(
                ["bash", str(STAGE)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertIn("refusing existing checkout", proc.stderr)
            self.assertNotIn("BLOCKED: home-write", proc.stderr)


class DryRunTests(unittest.TestCase):
    """Dry-run must not hash the operator home.

    HomeWatch walks ~/.cache/uv (about 21 GiB) and ~/.npm. On nimo those
    trees change while the hash runs, so tearDown failed even though
    stage.sh --dry-run never writes them. The assertion text was only the
    missing step name, so the script stderr was not in the failure.
    This class does not inherit HomeWatch. It still uses the private HOME
    from StageScriptTests._stub_env.
    """

    def test_dry_run_prints_the_pin_steps_and_nothing_upstream(self):
        with tempfile.TemporaryDirectory(dir=_scratch()) as tmp:
            work = Path(tmp)
            env = StageScriptTests._stub_env(None, work)
            leak = work / "leak.sh"
            leak.write_text("echo huggingface\n", encoding="utf-8")
            # A parent BASH_ENV would print before the steps. Drop it.
            env["BASH_ENV"] = str(leak)
            env["ENV"] = str(leak)
            env["CDPATH"] = str(work)
            for key in ("BASH_ENV", "ENV", "CDPATH"):
                env.pop(key, None)
            home = Path(env["HOME"])
            before = common.home_snapshot(home)
            proc = subprocess.run(
                ["bash", str(STAGE), "--dry-run"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            blob = f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            self.assertEqual(proc.returncode, 0, blob)
            text = proc.stdout
            py = env["HARNESS2_PY312"]
            for bit in (
                "git clone https://github.com/google-research/harness2",
                f"checkout --detach {H2_PIN}",
                "uv venv --python",
                "uv pip install --python",
                " -e ",
                "git init -q",
                "https://github.com/anomalyco/opencode.git",
                f"fetch --depth 1 origin {OC_PIN}",
                "checkout --detach FETCH_HEAD",
                "opencode-compat.diff",
                "apply --check",
                "npm install --prefix",
                "bun@1.3.11",
                "--frozen-lockfile --ignore-scripts",
                "check.py",
                "env: written from env.local.example",
                "UV_PYTHON_DOWNLOADS",
                f"realpath {py}",
            ):
                self.assertIn(bit, text, blob)
            for bad in ("harness2-setup", "job-bench-eval", "huggingface", "[render]", "harness2-check"):
                self.assertNotIn(bad, text, blob)
            wt = Path(env["HARNESS2_W"])
            self.assertFalse((wt / "tmp" / "harness2").exists(), blob)
            changed = common.snapshot_diff(before, common.home_snapshot(home))
            self.assertEqual(changed, [], blob)


if __name__ == "__main__":
    unittest.main()
