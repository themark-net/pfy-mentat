"""Entries 122-124 smokes: real-HOME writes FAIL, pins exit 2, cleanup timeout keeps the run failure.

Parent HOME is a temp dir this test owns. Children run under run_isolated with a different HOME, so a planted
real-HOME write uses that temp HOME's absolute path inside the stub. llmrouter and squadra pass a bwrap writable
list; bwrap is chosen with shutil.which on the smoke process PATH (there is no disable switch), and a hit makes
the child root read-only outside the smoke temp dir. Those tests set PATH to a directory without bwrap so the
write can land. A temp-HOME write goes to "$HOME/x", which is inside the smoke temp dir bwrap already allows.
"""
from __future__ import annotations

import json
import os
import shlex
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = "examples/x-intake-local/smoke_122_124.py"
CLASSIFY_JSON = (
    '{"query":{"task":"query","complexity":"simple","confident":true},'
    '"code":{"task":"code","complexity":"complex","confident":true}}'
)
# receipts go to a temp dir ($PFY_SMOKE_RECEIPT_DIR), never over a real run's pipelines/smoke/<entry>/latest.json
_RECEIPTS = tempfile.TemporaryDirectory(prefix="pfy-xintake-122-receipts-")
RECEIPT_DIR = Path(_RECEIPTS.name)


def tearDownModule() -> None:
    _RECEIPTS.cleanup()


DOCTOR_JSON = '{"integrity":"passed","pending_ack":["assign-T1"],"events":1}'


def _write_exe(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _env(home: Path, **extra: str) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    for key in list(env):
        if key.startswith(("LLMROUTER_", "SQUADRA_", "HR_", "DOCKER_")) or key == "PFY_XINTAKE_TIMEOUT":
            env.pop(key, None)
    env["PFY_SMOKE_RECEIPT_DIR"] = str(RECEIPT_DIR)
    env.update(extra)
    return env


def _run(entry: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, SCRIPT, "--entry", entry],
        cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=90,
    )


def _receipt(entry: str) -> dict:
    return json.loads((RECEIPT_DIR / entry / "latest.json").read_text(encoding="utf-8"))


def _no_tb(case: unittest.TestCase, proc: subprocess.CompletedProcess[str]) -> None:
    case.assertNotIn("Traceback", proc.stderr)
    case.assertNotIn("Traceback", proc.stdout)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _skip_unless_py312(case: unittest.TestCase) -> None:
    py = "/usr/bin/python3"
    if not os.access(py, os.X_OK):
        case.skipTest("/usr/bin/python3 < 3.12")
    probe = subprocess.run(
        [py, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)"],
        timeout=30,
    )
    if probe.returncode != 0:
        case.skipTest("/usr/bin/python3 < 3.12")


def _calls(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _assert_no_rm_run(case: unittest.TestCase, calls: Path) -> None:
    text = _calls(calls)
    for line in text.splitlines():
        padded = f" {line.strip()} "
        case.assertNotIn(" run ", padded, text)
        case.assertNotIn(" rm ", padded, text)
        case.assertNotIn(" volume rm ", padded, text)


def _lr_python(version: str, *, classify: bool) -> str:
    if not classify:
        return f"#!/bin/sh\necho {shlex.quote(version)}\n"
    quoted = shlex.quote(CLASSIFY_JSON)
    return (
        "#!/bin/sh\n"
        'case "$*" in\n'
        "  *classify_signals*)\n"
        f"    echo {quoted}\n"
        "    ;;\n"
        "  *)\n"
        f"    echo {shlex.quote(version)}\n"
        "    ;;\n"
        "esac\n"
    )


def _lr_demo(
    log: Path | None = None,
    *,
    temp_home: bool = False,
    real_home: Path | None = None,
    sleep_s: int = 0,
) -> str:
    lines = ["#!/bin/sh"]
    if log is not None:
        lines.append(f'echo "$@" >> {shlex.quote(str(log))}')
    if temp_home:
        lines.append('echo planted > "$HOME/x"')
    if real_home is not None:
        dest = real_home / ".llm-router"
        lines.append(f"mkdir -p {shlex.quote(str(dest))}")
        lines.append(f"echo planted > {shlex.quote(str(dest / 'x'))}")
    if sleep_s:
        lines.append(f"sleep {int(sleep_s)}")
    else:
        lines.append('echo "Complexity Model"')
    lines.append("exit 0")
    return "\n".join(lines) + "\n"


def _lr_bin(bin_dir: Path, python_body: str, demo_body: str) -> Path:
    _write_exe(bin_dir / "python", python_body)
    binary = bin_dir / "llm-router"
    _write_exe(binary, demo_body)
    return binary


def _squadra_py(version: str, plant: Path | None) -> str:
    lines = [
        "import sys",
        "from pathlib import Path",
        "args = sys.argv[1:]",
        "cmd = args[0] if args else ''",
        "if cmd == '--version':",
        f"    print({version!r})",
        "    raise SystemExit(0)",
        "if cmd in ('init', 'agent', 'task'):",
    ]
    if plant is not None:
        lines.append(f"    target = Path({str(plant)!r})")
        lines.append("    target.parent.mkdir(parents=True, exist_ok=True)")
        lines.append("    target.write_text('planted\\n')")
    lines += [
        "    raise SystemExit(0)",
        "if cmd == 'doctor':",
        f"    print({DOCTOR_JSON!r})",
        "    raise SystemExit(0)",
        "if cmd == 'status':",
        "    print('pfy smoke task')",
        "    raise SystemExit(0)",
        "raise SystemExit(0)",
        "",
    ]
    return "\n".join(lines)


def _squadra_failing_py(step: str) -> str:
    """Prints 3.10.1 for --version and exits 3 on the named step (init, agent_coordinator, agent_builder, task)."""
    return "\n".join([
        "import sys",
        "args = sys.argv[1:]",
        "cmd = args[0] if args else ''",
        "if cmd == '--version':",
        "    print('3.10.1')",
        "    raise SystemExit(0)",
        "step = cmd",
        "if cmd == 'agent':",
        "    step = 'agent_' + args[args.index('--role') + 1]",
        f"if step == {step!r}:",
        "    print('boom', file=sys.stderr)",
        "    raise SystemExit(3)",
        "raise SystemExit(0)",
        "",
    ])


def _squadra_custom(on_init: str = "", doctor: str = DOCTOR_JSON) -> str:
    """A passing Squadra stub; `on_init` is Python run during `init`, `doctor` is what `doctor` prints."""
    body = "\n".join("    " + ln for ln in on_init.splitlines()) or "    pass"
    return "\n".join([
        "import os, sys",
        "from pathlib import Path",
        "args = sys.argv[1:]",
        "cmd = args[0] if args else ''",
        "if cmd == '--version':",
        "    print('3.10.1')",
        "    raise SystemExit(0)",
        "if cmd == 'init':",
        body,
        "if cmd == 'doctor':",
        f"    print({doctor!r})",
        "if cmd == 'status':",
        "    print('pfy smoke task')",
        "raise SystemExit(0)",
        "",
    ])


def _plant(path: Path) -> str:
    return f"p = Path({str(path)!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text('planted\\n')"


def _squadra_tree(root: Path, body: str) -> Path:
    script = root / "scripts" / "squadra.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(body, encoding="utf-8")
    return root


def _docker_stub(path: Path, calls: Path, cases: str) -> None:
    _write_exe(path, f"""#!/bin/sh
echo "$@" >> {shlex.quote(str(calls))}
case " $* " in
{cases}esac
exit 0
""")


class XIntakeSmoke122124Tests(unittest.TestCase):
    def test_llmrouter_missing_binary_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-122-") as td:
            home = Path(td, "home")
            home.mkdir()
            empty = Path(td, "emptybin")
            empty.mkdir()
            proc = _run("llmrouter", _env(home, PATH=str(empty)))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("llm-router", _receipt("llmrouter")["reason"])

    def test_llmrouter_pin_mismatch_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-122-") as td:
            home, bindir = Path(td, "home"), Path(td, "bin")
            home.mkdir()
            calls = Path(td, "calls")
            binary = _lr_bin(bindir, _lr_python("9.9.9", classify=False), _lr_demo(calls))
            proc = _run("llmrouter", _env(home, LLMROUTER_BIN=str(binary)))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("9.9.9", _receipt("llmrouter")["reason"])
            self.assertNotIn("demo", _calls(calls))

    def test_llmrouter_clean_passes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-122-") as td:
            home, bindir = Path(td, "home"), Path(td, "bin")
            home.mkdir()
            binary = _lr_bin(bindir, _lr_python("15.4.0", classify=True), _lr_demo())
            proc = _run("llmrouter", _env(home, LLMROUTER_BIN=str(binary)))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIs(_receipt("llmrouter")["checks"]["real_home_untouched"], True)

    def test_llmrouter_temp_home_write_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-122-") as td:
            home, bindir = Path(td, "home"), Path(td, "bin")
            home.mkdir()
            binary = _lr_bin(bindir, _lr_python("15.4.0", classify=True), _lr_demo(temp_home=True))
            proc = _run("llmrouter", _env(home, LLMROUTER_BIN=str(binary)))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIs(_receipt("llmrouter")["checks"]["home_untouched"], False)

    def test_llmrouter_real_home_write_fails(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-122-") as td:
            home, bindir = Path(td, "home"), Path(td, "bin")
            home.mkdir()
            binary = _lr_bin(
                bindir, _lr_python("15.4.0", classify=True), _lr_demo(real_home=home))
            proc = _run("llmrouter", _env(home, PATH=str(bindir), LLMROUTER_BIN=str(binary)))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIs(_receipt("llmrouter")["checks"]["real_home_untouched"], False)
            self.assertTrue((home / ".llm-router" / "x").is_file())

    def test_llmrouter_timeout_keeps_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-122-") as td:
            home, bindir = Path(td, "home"), Path(td, "bin")
            home.mkdir()
            binary = _lr_bin(
                bindir, _lr_python("15.4.0", classify=True), _lr_demo(real_home=home, sleep_s=30))
            proc = _run("llmrouter", _env(
                home, PATH=str(bindir), LLMROUTER_BIN=str(binary), PFY_XINTAKE_TIMEOUT="2"))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            receipt = _receipt("llmrouter")
            self.assertIn("checks", receipt)
            self.assertIs(receipt["checks"]["classify_query_simple"], True)
            self.assertIs(receipt["checks"]["classify_code"], True)
            self.assertIs(receipt["checks"]["real_home_untouched"], False)
            self.assertIn("real HOME", receipt["reason"])
            self.assertTrue((home / ".llm-router" / "x").is_file())

    def test_squadra_missing_checkout_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            missing = Path(td, "no-squadra")
            missing.mkdir()
            proc = _run("squadra", _env(home, SQUADRA_DIR=str(missing)))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("missing", _receipt("squadra")["reason"])

    def test_squadra_pin_mismatch_exits_2(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            repo = _squadra_tree(Path(td, "squadra"), _squadra_py("0.0.1", None))
            proc = _run("squadra", _env(home, SQUADRA_DIR=str(repo)))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("0.0.1", _receipt("squadra")["reason"])

    def test_squadra_failed_step_writes_fresh_fail_receipt(self) -> None:
        _skip_unless_py312(self)
        receipt = RECEIPT_DIR / "squadra/latest.json"
        for step in ("init", "agent_coordinator", "agent_builder", "task"):
            with self.subTest(step=step), tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
                home = Path(td, "home")
                home.mkdir()
                empty = Path(td, "emptybin")
                empty.mkdir()
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({"entry": "squadra", "verdict": "PASS", "reason": "stale"}),
                                   encoding="utf-8")
                repo = _squadra_tree(Path(td, "squadra"), _squadra_failing_py(step))
                proc = _run("squadra", _env(home, PATH=str(empty), SQUADRA_DIR=str(repo)))
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
                _no_tb(self, proc)
                got = _receipt("squadra")
                self.assertEqual(got["verdict"], "FAIL", got)
                self.assertNotEqual(got.get("reason"), "stale", got)
                self.assertIs(got["checks"][f"{step}_exit_0"], False, got)
                self.assertIs(got["checks"]["real_home_untouched"], True, got)
                self.assertIn(f"{step}_exit_0", got["reason"], got)

    def test_squadra_real_home_write_fails(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            empty = Path(td, "emptybin")
            empty.mkdir()
            plant = home / ".local" / "state" / "squadra" / "x"
            repo = _squadra_tree(Path(td, "squadra"), _squadra_py("3.10.1", plant))
            proc = _run("squadra", _env(home, PATH=str(empty), SQUADRA_DIR=str(repo)))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIs(_receipt("squadra")["checks"]["real_home_untouched"], False)
            self.assertTrue(plant.is_file())

    def test_harnessrouter_missing_docker_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-123-") as td:
            home = Path(td, "home")
            home.mkdir()
            empty = Path(td, "emptybin")
            empty.mkdir()
            proc = _run("harnessrouter", _env(home, PATH=str(empty), HR_SMOKE_PORT=str(_free_port())))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("docker", _receipt("harnessrouter")["reason"])

    def test_harnessrouter_existing_container_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-123-") as td:
            home = Path(td, "home")
            home.mkdir()
            calls, docker = Path(td, "calls"), Path(td, "docker")
            _docker_stub(docker, calls, '  *" version "*) exit 0 ;;\n  *" container inspect "*) exit 0 ;;\n')
            proc = _run("harnessrouter", _env(
                home, DOCKER_BIN=str(docker), HR_SMOKE_PORT=str(_free_port())))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("container", _receipt("harnessrouter")["reason"])
            _assert_no_rm_run(self, calls)

    def test_harnessrouter_existing_volume_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-123-") as td:
            home = Path(td, "home")
            home.mkdir()
            calls, docker = Path(td, "calls"), Path(td, "docker")
            _docker_stub(
                docker, calls,
                '  *" version "*) exit 0 ;;\n'
                '  *" container inspect "*) exit 1 ;;\n'
                '  *" volume inspect "*) exit 0 ;;\n',
            )
            proc = _run("harnessrouter", _env(  # short timeout: a missing volume check fails fast, not at 90 s
                home, DOCKER_BIN=str(docker), HR_SMOKE_PORT=str(_free_port()), PFY_XINTAKE_TIMEOUT="2"))
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            self.assertIn("volume", _receipt("harnessrouter")["reason"])
            _assert_no_rm_run(self, calls)

    def test_harnessrouter_image_override_warns(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-123-") as td:
            home = Path(td, "home")
            home.mkdir()
            docker = Path(td, "docker")
            _write_exe(docker, "#!/bin/sh\nexit 1\n")
            proc = _run("harnessrouter", _env(
                home, DOCKER_BIN=str(docker), HR_IMAGE="hr-test-override:local",
                HR_SMOKE_PORT=str(_free_port())))
            _no_tb(self, proc)
            self.assertIn("WARN", proc.stderr)

    def test_harnessrouter_run_fail_cleanup_timeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-123-") as td:
            home = Path(td, "home")
            home.mkdir()
            calls, docker = Path(td, "calls"), Path(td, "docker")
            _docker_stub(
                docker, calls,
                '  *" version "*) exit 0 ;;\n'
                '  *" container inspect "*) exit 1 ;;\n'
                '  *" volume inspect "*) exit 1 ;;\n'
                '  *" volume rm "*) exit 0 ;;\n'
                '  *" rm "*) sleep 30 ;;\n'
                '  *" run "*) exit 1 ;;\n',
            )
            proc = _run("harnessrouter", _env(
                home, DOCKER_BIN=str(docker), HR_SMOKE_PORT=str(_free_port()),
                PFY_XINTAKE_TIMEOUT="2"))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            receipt = _receipt("harnessrouter")
            self.assertEqual(receipt["reason"], "docker run failed")
            self.assertTrue(receipt.get("cleanup_reason"))
            self.assertIn("volume rm", _calls(calls))

    # ---- follow-ups to #298 ----
    def _squadra(self, td: str, home: Path, body: str, **extra: str) -> tuple[subprocess.CompletedProcess, dict]:
        empty = Path(td, "emptybin")
        empty.mkdir(exist_ok=True)
        repo = _squadra_tree(Path(td, "squadra"), body)
        proc = _run("squadra", _env(home, PATH=str(empty), SQUADRA_DIR=str(repo), **extra))
        _no_tb(self, proc)
        return proc, _receipt("squadra")

    def test_squadra_clean_stub_passes(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            proc, got = self._squadra(td, home, _squadra_custom())
            self.assertEqual(proc.returncode, 0, got)
            self.assertIs(got["checks"]["real_home_untouched"], True)

    def test_squadra_unexpected_exception_fails(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            (RECEIPT_DIR / "squadra").mkdir(parents=True, exist_ok=True)
            (RECEIPT_DIR / "squadra/latest.json").write_text('{"verdict": "PASS", "reason": "stale"}')
            # doctor printing a JSON list makes dj.get raise AttributeError: only the catch-all handles it
            proc, got = self._squadra(td, home, _squadra_custom(doctor="[]"))
            self.assertEqual(proc.returncode, 1, got)
            self.assertEqual(got["verdict"], "FAIL")
            self.assertIn("unexpected AttributeError", got["reason"])
            self.assertIs(got["checks"]["real_home_untouched"], True)

    def test_squadra_unexpected_exception_names_real_home(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            body = _squadra_custom(on_init=_plant(home / ".local/state/squadra/x"), doctor="[]")
            proc, got = self._squadra(td, home, body)
            self.assertEqual(proc.returncode, 1, got)
            self.assertIs(got["checks"]["real_home_untouched"], False)
            self.assertIn("unexpected AttributeError", got["reason"])
            self.assertIn("real HOME", got["reason"])

    def test_squadra_cache_write_fails(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            proc, got = self._squadra(td, home, _squadra_custom(on_init=_plant(home / ".cache/squadra/usage-v1/x")))
            self.assertEqual(proc.returncode, 1, got)
            self.assertIs(got["checks"]["real_home_untouched"], False)

    def test_squadra_plugin_store_write_fails(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            home.mkdir()
            proc, got = self._squadra(td, home, _squadra_custom(on_init=_plant(home / ".squadra/plugins/x")))
            self.assertEqual(proc.returncode, 1, got)
            self.assertIs(got["checks"]["real_home_untouched"], False)

    def test_squadra_in_place_edit_fails(self) -> None:
        _skip_unless_py312(self)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-124-") as td:
            home = Path(td, "home")
            existing = home / ".local/state/squadra/state.json"
            existing.parent.mkdir(parents=True)
            existing.write_text("aaaa\n")
            # same size, mtime restored: only a content hash sees it
            edit = (f"p = Path({str(existing)!r})\nst = p.stat()\np.write_text('bbbb\\n')\n"
                    "os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))")
            proc, got = self._squadra(td, home, _squadra_custom(on_init=edit))
            self.assertEqual(existing.read_text(), "bbbb\n")
            self.assertEqual(proc.returncode, 1, got)
            self.assertIs(got["checks"]["real_home_untouched"], False)

    def test_harnessrouter_cleanup_timeout_keeps_happy_path_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-123-") as td:
            home = Path(td, "home")
            home.mkdir()
            calls, docker = Path(td, "calls"), Path(td, "docker")
            # run succeeds but nothing listens, so the probes fail; then `docker rm` times out
            _docker_stub(
                docker, calls,
                '  *" version "*) exit 0 ;;\n'
                '  *" container inspect "*) exit 1 ;;\n'
                '  *" volume inspect "*) exit 1 ;;\n'
                '  *" volume rm "*) exit 0 ;;\n'
                '  *" rm "*) sleep 30 ;;\n'
                '  *" run "*) exit 0 ;;\n',
            )
            proc = _run("harnessrouter", _env(
                home, DOCKER_BIN=str(docker), HR_SMOKE_PORT=str(_free_port()), PFY_XINTAKE_TIMEOUT="2"))
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            _no_tb(self, proc)
            got = _receipt("harnessrouter")
            self.assertTrue(got["reason"].startswith("failed checks:"), got["reason"])
            self.assertIn("console_answers", got["reason"])
            self.assertEqual(got.get("cleanup_reason"), "docker rm timeout")
            self.assertIs(got["checks"]["cleanup_ok"], False)
            self.assertIn("volume rm", _calls(calls))


if __name__ == "__main__":
    unittest.main()
