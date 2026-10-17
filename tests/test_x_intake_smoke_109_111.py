"""Entry 110 (brigade) smoke run as a subprocess with a stub binary: env stripping and timeout cleanup.

Parent HOME is a temp dir this test owns so a stub cannot touch the operator's real home.
Receipts go to PFY_SMOKE_RECEIPT_DIR, never pipelines/smoke in the repo.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOLVM_PIN = "alpine:3.22@sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8"
SMOLVM_PIN_DIGEST = "sha256:5291449c3df73caf6ed85e649dec1b9e818b39a5d8c871e97afc13e9cd5e8fa8"

# Upstream smolvm v1.26.1 (093852e8), checked in source:
# A plain `machine run --image <ref>` calls pull_with_progress on every run
# (src/cli/machine.rs:2010), not only the first. pull_with_progress
# (src/cli/mod.rs:172-214) writes stderr only, in order:
#   1. eprint!("Pulling image {ref}...") with no newline
#   2. progress redraws "\rPulling image {ref}... [" + 20 chars of =/>/space + "] {pct}%"
#   3. optionally "\rPulling image {ref}... [====================] 100% — syncing..."
#   4. eprintln!("\rPulling image {ref}... done." + 30 spaces)
# "Caching image <16hex> (one-time; reused on later runs)" and
# "Using cached image <16hex> (host cache hit; no pull)" are stdout from
# ensure_init_layer (machine.rs:1068/1082), gated by init or --oci-cache
# (machine.rs:1570). The smoke's plain command never prints them.
# PFY_SMOLVM_STUB_MODE=no-evidence prints neither. guest-blob also echoes a
# guest sha256. wrong-ref names alpine:3.21@sha256: + 64 a's instead of --image.
SMOLVM_STUB = r'''#!/usr/bin/env python3
import os, sys
from pathlib import Path
args = sys.argv[1:]
if args[:2] != ["machine", "run"]:
    sys.stderr.write("unhandled\n")
    raise SystemExit(2)
image = args[args.index("--image") + 1]
mode = os.environ.get("PFY_SMOLVM_STUB_MODE", "")
count_path = Path(__file__).resolve().parent / "smolvm-runs"
n = int(count_path.read_text() or "0") + 1 if count_path.exists() else 1
count_path.write_text(str(n))
(Path(__file__).resolve().parent / "smolvm-env-names").write_text("\n".join(sorted(os.environ)) + "\n")

def pull(ref):
    err = sys.stderr
    err.write("Pulling image " + ref + "...")
    err.write("\rPulling image " + ref + "... [=====>              ] 25%")
    err.write("\rPulling image " + ref + "... [===========>        ] 60%")
    err.write("\rPulling image " + ref + "... [====================] 100% — syncing...")
    err.write("\rPulling image " + ref + "... done." + (" " * 30) + "\n")
    err.flush()

if mode == "no-evidence":
    pass
elif mode == "wrong-ref":
    pull("alpine:3.21@sha256:" + ("a" * 64))
else:
    pull(image)
if "--oci-cache" in args and mode != "no-evidence":
    if n == 1:
        print("Caching image 0123456789abcdef (one-time; reused on later runs)")
    else:
        print("Using cached image 0123456789abcdef (host cache hit; no pull)")
print("pfy-smolvm-ok")
print("6.6.0-guest")
if mode == "guest-blob":
    print("blob sha256:" + ("e" * 64))
print("host-hidden")
raise SystemExit(0)
'''

# `--version` records whether GROK_API_KEY reached it; any other command forks a sleeping child and sleeps.
# Fail: a paid key reached the tool, or the forked child outlived the timeout (only the direct child was killed).
# Recover: the key is absent in the tool env, and no process running this stub is left after the smoke exits.
STUB = """#!/bin/sh
if [ "$1" = --version ]; then
  if [ -n "${GROK_API_KEY+x}" ]; then echo present > "$PFY_PROBE_OUT"; else echo absent > "$PFY_PROBE_OUT"; fi
  echo "brigade 0.27.0"
  exit 0
fi
if [ "$1" = --child ]; then sleep 60; exit 0; fi
"$0" --child >/dev/null 2>&1 &
sleep 60
"""

# A brigade that satisfies every check and writes only inside its cwd (the scratch repo).
BRIGADE_OK = r"""#!/usr/bin/env python3
import os, subprocess, sys
args = sys.argv[1:]

def emit(obj, code=0):
    sys.stdout.write(__import__("json").dumps(obj) + "\n")
    raise SystemExit(code)

if args[:1] == ["--version"]:
    print("brigade 0.27.0")
    raise SystemExit(0)
if args[:1] == ["init"]:
    os.makedirs(".brigade", exist_ok=True)
    open(".brigade/config.json", "w", encoding="utf-8").write("{}\n")
    raise SystemExit(0)
if args[:3] == ["work", "task", "add"]:
    raise SystemExit(0)
if args[:2] == ["work", "ready"]:
    emit({"ready_count": 1, "ready": [{"id": "t1"}]})
if args[:2] == ["work", "claim"]:
    actor = args[args.index("--actor") + 1]
    if actor == "smoke-a":
        emit({"task_id": "t1", "status": "in_progress", "assignee": "smoke-a"})
    emit({"reason": "no_ready", "exit_code": 1}, 1)
if args[:3] == ["work", "verify", "run"]:
    log = os.path.abspath("stdout.log")
    open(log, "w", encoding="utf-8").write("ok\n")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    failed = "sys.exit(3)" in " ".join(args)
    body = {
        "status": "failed" if failed else "completed",
        "git": {"head": head},
        "commands": [{"exit_code": 3 if failed else 0, "stdout_log_path": log}],
    }
    emit(body, 1 if failed else 0)
if args[:2] == ["receipts", "verify"]:
    counter = os.path.abspath(".verify-count")
    n = int(open(counter, encoding="utf-8").read()) + 1 if os.path.exists(counter) else 1
    open(counter, "w", encoding="utf-8").write(str(n))
    if n == 1:
        emit({"summary": {"ok": 1, "total": 1, "mismatch": 0, "missing": 0}})
    emit({"summary": {"ok": 0, "total": 1, "mismatch": 1, "missing": 0}}, 1)
sys.stderr.write("unhandled brigade args\n")
raise SystemExit(2)
"""

# Records argv, rejects a missing --unshare-pid, and execs the first real binary (the brigade stub).
# PFY_BWRAP_REJECT_UNSHARE=1 makes the probe fail the way an unsupported --unshare-pid does.
BWRAP_FAKE = r"""#!/usr/bin/env python3
import os, sys
log = os.environ.get("PFY_BWRAP_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("\n".join(sys.argv[1:]) + "\n---\n")
if "--unshare-pid" not in sys.argv[1:]:
    raise SystemExit(1)
if os.environ.get("PFY_BWRAP_REJECT_UNSHARE") == "1":
    raise SystemExit(1)
for index, arg in enumerate(sys.argv[1:], 1):
    if os.path.isfile(arg) and os.access(arg, os.X_OK):
        os.execv(arg, sys.argv[index:])
raise SystemExit(0)
"""


def _write_exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _smoke_tree_sig() -> dict[str, tuple[int, int]]:
    root = ROOT / "pipelines" / "smoke"
    found: dict[str, tuple[int, int]] = {}
    if not root.exists():
        return found
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = Path(dirpath, name)
            st = path.stat()
            found[str(path)] = (st.st_mtime_ns, st.st_size)
    return found


class XIntakeSmoke109111Tests(unittest.TestCase):
    def _run(self, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "examples/x-intake-local/smoke_109_111.py", "--entry", "brigade"],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120,
        )

    def _assert_repo_smoke_unchanged(self, before: dict[str, tuple[int, int]]) -> None:
        self.assertEqual(_smoke_tree_sig(), before, "pipelines/smoke in the repo changed")
        porcelain = subprocess.run(
            ["git", "status", "--porcelain", "pipelines/smoke"],
            cwd=str(ROOT), capture_output=True, text=True, check=False,
        )
        self.assertEqual(porcelain.stdout, "")

    def test_brigade_strips_grok_key_and_kills_process_group_on_timeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-parent-") as td:
            home, stub, probe = Path(td, "home"), Path(td, "brigade-stub-109"), Path(td, "probe")
            receipts = Path(td, "receipts")
            home.mkdir()
            _write_exe(stub, STUB)
            env = {k: v for k, v in os.environ.items() if not k.startswith("BRIGADE_")}
            env.update(HOME=str(home), BRIGADE_BIN=str(stub), PFY_PROBE_OUT=str(probe),
                       GROK_API_KEY="must-not-leak", PFY_XINTAKE_TIMEOUT="1",
                       PFY_SMOKE_RECEIPT_DIR=str(receipts))
            before = _smoke_tree_sig()
            p = self._run(env)
            time.sleep(0.5)
            left = subprocess.run(["pgrep", "-f", str(stub)], capture_output=True, text=True).stdout.split()
            for pid in left:
                try:
                    os.kill(int(pid), 9)
                except OSError:
                    pass
            self.assertEqual(probe.read_text().strip(), "absent")
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
            self.assertNotIn("Traceback", p.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertIn("timeout", receipt["reason"])
            self.assertEqual(left, [], "a forked tool child outlived the smoke timeout")
            self._assert_repo_smoke_unchanged(before)

    def _tool_path(self, bindir: Path, *extra: str) -> None:
        bindir.mkdir()
        git = shutil.which("git")
        py = shutil.which("python3")
        self.assertTrue(git and py, "git and python3 are required on PATH for the brigade smoke")
        os.symlink(git, bindir / "git")
        os.symlink(py, bindir / "python3")
        for name in extra:
            _write_exe(bindir / name, {"bwrap": BWRAP_FAKE}[name])

    def _ok_env(self, home: Path, stub: Path, receipts: Path, path: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("BRIGADE_", "PFY_"))}
        env.update(HOME=str(home), PATH=path, BRIGADE_BIN=str(stub),
                   PFY_SMOKE_RECEIPT_DIR=str(receipts))
        return env

    def test_no_bwrap_records_real_home_snapshot(self) -> None:
        # Fail: bwrap missing and the smoke still claims the bwrap containment, or it skips the real-HOME check.
        # Recover: exit 0, containment real-home-snapshot, real_home_state_unchanged true. A changed snapshot FAILs.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-nobwrap-") as td:
            root = Path(td)
            home, receipts = root / "home", root / "receipts"
            home.mkdir()
            stub = root / "brigade"
            _write_exe(stub, BRIGADE_OK)
            bindir = root / "bin"
            self._tool_path(bindir)
            self.assertIsNone(shutil.which("bwrap", path=str(bindir)))
            env = self._ok_env(home, stub, receipts, str(bindir))
            before = _smoke_tree_sig()
            proc = self._run(env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("containment"), "real-home-snapshot")
            self.assertIs(receipt.get("real_home_state_unchanged"), True)
            self.assertEqual(receipt.get("verdict"), "PASS")
            self._assert_repo_smoke_unchanged(before)

    def test_unshare_pid_is_passed_to_bwrap(self) -> None:
        # Fail: a working bwrap is invoked without --unshare-pid on the tool command.
        # Recover: the wrapped brigade command's argv contains --unshare-pid and the smoke passes.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-unshare-") as td:
            root = Path(td)
            home, receipts = root / "home", root / "receipts"
            home.mkdir()
            stub = root / "brigade"
            _write_exe(stub, BRIGADE_OK)
            bindir = root / "bin"
            self._tool_path(bindir, "bwrap")
            log = root / "bwrap.log"
            env = self._ok_env(home, stub, receipts, str(bindir))
            env["PFY_BWRAP_LOG"] = str(log)
            before = _smoke_tree_sig()
            proc = self._run(env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("containment"), "bwrap-ro-root-no-net")
            text = log.read_text(encoding="utf-8")
            wrapped = [block for block in text.split("---\n") if str(stub) in block]
            self.assertTrue(wrapped, "bwrap never wrapped the brigade binary")
            self.assertIn("--unshare-pid", wrapped[0])
            self._assert_repo_smoke_unchanged(before)

    def test_unshare_pid_unsupported_falls_back(self) -> None:
        # Fail: an unsupported --unshare-pid is retried without the flag, or the tool never runs.
        # Recover: the probe argv contains --unshare-pid, the prefix is dropped, containment is the
        # real-HOME snapshot, and the brigade stub still runs to a pass.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-unshare-no-") as td:
            root = Path(td)
            home, receipts = root / "home", root / "receipts"
            home.mkdir()
            stub = root / "brigade"
            _write_exe(stub, BRIGADE_OK)
            bindir = root / "bin"
            self._tool_path(bindir, "bwrap")
            log = root / "bwrap.log"
            env = self._ok_env(home, stub, receipts, str(bindir))
            env["PFY_BWRAP_LOG"] = str(log)
            env["PFY_BWRAP_REJECT_UNSHARE"] = "1"
            before = _smoke_tree_sig()
            proc = self._run(env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            receipt = json.loads((receipts / "brigade" / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("containment"), "real-home-snapshot")
            self.assertIs(receipt.get("real_home_state_unchanged"), True)
            text = log.read_text(encoding="utf-8")
            self.assertIn("--unshare-pid", text)
            self.assertNotIn(str(stub), text, "tool command was still wrapped after the probe failed")
            self._assert_repo_smoke_unchanged(before)

    def _run_smolvm(self, root: Path, *, image: str | None = None, mode: str | None = None,
                    plant: dict[str, str] | None = None):
        # Fail: the smoke needs /dev/kvm, or it trusts a sha256 printed by the guest.
        # Recover: PFY_SMOLVM_KVM_PATH is a temp file, and the digest is the pinned ref.
        home = root / "home"
        home.mkdir(exist_ok=True)
        kvm = root / "kvm"
        kvm.write_text("")
        kvm.chmod(0o600)
        stub = root / "smolvm"
        if not stub.exists():
            _write_exe(stub, SMOLVM_STUB)
        digest = hashlib.sha256(stub.read_bytes()).hexdigest()
        receipts = root / "receipts"
        env = {k: v for k, v in os.environ.items() if not k.startswith("SMOLVM_")}
        env.update(HOME=str(home), SMOLVM_BIN=str(stub), SMOLVM_SHA256=digest,
                   PFY_SMOKE_RECEIPT_DIR=str(receipts), PFY_SMOLVM_KVM_PATH=str(kvm))
        env.pop("PFY_SMOLVM_STUB_MODE", None)
        if image is not None:
            env["SMOLVM_IMAGE"] = image
        if mode:
            env["PFY_SMOLVM_STUB_MODE"] = mode
        if plant:
            env.update(plant)
        before = _smoke_tree_sig()
        proc = subprocess.run(
            [sys.executable, "examples/x-intake-local/smoke_109_111.py", "--entry", "smolvm"],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60,
        )
        path = receipts / "smolvm" / "latest.json"
        receipt = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        self._assert_repo_smoke_unchanged(before)
        return proc, receipt

    def test_a_smolvm_default_pin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            proc, receipt = self._run_smolvm(Path(td))
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, blob)
            self.assertEqual(receipt.get("image"), SMOLVM_PIN, blob)
            self.assertEqual(receipt.get("image_digest"), SMOLVM_PIN_DIGEST, blob)
            self.assertEqual(receipt.get("image_digest_source"), "pin", blob)
            # Opening eprint: splitlines() breaks on \r and the helper returns the first hit.
            # The "... done." redraw is later in the same upstream sequence. See the decisions log.
            self.assertEqual(receipt.get("image_evidence"), "Pulling image " + SMOLVM_PIN + "...", blob)
            self.assertIn(str(Path(td) / "kvm"), receipt.get("kvm_path") or "", blob)
            self.assertEqual(receipt.get("reason"), "ok: guest kernel 6.6.0-guest, host file hidden", blob)

    def test_b_smolvm_env_override_is_pinned(self) -> None:
        override = "Example.com/alpine:3.19@SHA256:" + ("CD" * 32)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            proc, receipt = self._run_smolvm(Path(td), image=override)
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, blob)
            self.assertEqual(receipt.get("image"), override.lower(), blob)
            self.assertEqual(receipt.get("image_digest"), "sha256:" + ("cd" * 32), blob)
            self.assertEqual(receipt.get("image_digest_source"), "env", blob)

    def test_c_smolvm_unpinned_env_exits_2(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            proc, receipt = self._run_smolvm(Path(td), image="alpine")
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 2, blob)
            self.assertIn("digest-pinned", receipt.get("reason") or "", blob)
            self.assertNotIn("Traceback", proc.stderr, blob)

    def test_d_smolvm_guest_sha_is_not_the_digest(self) -> None:
        guest = "sha256:" + ("e" * 64)
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            proc, receipt = self._run_smolvm(Path(td), mode="guest-blob")
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, blob)
            self.assertEqual(receipt.get("image_digest"), SMOLVM_PIN_DIGEST, blob)
            self.assertNotEqual(receipt.get("image_digest"), guest, blob)
            self.assertNotIn(guest, json.dumps({k: receipt.get(k) for k in ("image_digest", "image")}))

    def test_e_smolvm_missing_evidence_exits_1(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            proc, receipt = self._run_smolvm(Path(td), mode="no-evidence")
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 1, blob)
            self.assertEqual(
                receipt.get("reason"),
                "smolvm did not report pulling or caching the pinned image",
                blob,
            )

    def test_f_smolvm_plain_runs_pull_every_time(self) -> None:
        # Fail: a second plain run is treated as a cache hit and drops the pull line.
        # Recover: upstream pulls on every plain run, so both receipts record the pull line.
        expected = "Pulling image " + SMOLVM_PIN + "..."
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            root = Path(td)
            first, first_receipt = self._run_smolvm(root)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertEqual(first_receipt.get("image_evidence"), expected)
            proc, receipt = self._run_smolvm(root)
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, blob)
            self.assertEqual(receipt.get("image_evidence"), expected, blob)

    def test_g_smolvm_wrong_ref_exits_1(self) -> None:
        # Fail: any "Pulling image " line counts, so a different ref still passes (M21).
        # Recover: exit 1 with the missing-evidence reason when the pull names another ref.
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-") as td:
            proc, receipt = self._run_smolvm(Path(td), mode="wrong-ref")
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 1, blob)
            self.assertEqual(
                receipt.get("reason"),
                "smolvm did not report pulling or caching the pinned image",
                blob,
            )
            self.assertNotIn("Traceback", proc.stderr, blob)

    def test_h_oci_cache_stdout_branch(self) -> None:
        # Fail: smolvm_image_evidence ignores stdout cache lines (M19b).
        # Recover: --oci-cache prints Caching on the first run and Using cached later,
        # and the helper returns those lines. Direct call is the one allowed here.
        import importlib.util
        local = ROOT / "examples" / "x-intake-local"
        if str(local) not in sys.path:
            sys.path.insert(0, str(local))
        spec = importlib.util.spec_from_file_location(
            "smoke_109_111_evidence", local / "smoke_109_111.py",
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        evidence = module.smolvm_image_evidence
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-oci-") as td:
            stub = Path(td) / "smolvm"
            _write_exe(stub, SMOLVM_STUB)
            seen = []
            for _ in range(2):
                proc = subprocess.run(
                    [str(stub), "machine", "run", "--oci-cache", "--image", SMOLVM_PIN, "--", "true"],
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                self.assertNotIn("Pulling image", proc.stdout)
                seen.append(evidence(proc.stdout, proc.stderr, SMOLVM_PIN))
        self.assertEqual(seen[0], "Caching image 0123456789abcdef (one-time; reused on later runs)")
        self.assertEqual(seen[1], "Using cached image 0123456789abcdef (host cache hit; no pull)")

    def test_i_smolvm_child_drops_secret_shaped_env(self) -> None:
        # Fail: clean_env keeps secret-shaped names that are not in PAID_KEYS.
        # Recover: the smolvm child runs, those names are absent, and PATH is present.
        secret_names = (
            "NPM_TOKEN", "GITHUB_PAT", "GH_ENTERPRISE_TOKEN", "HF_TOKEN",
            "FOO_API_KEY", "DB_PASSWORD", "MY_SECRET", "AWS_CREDENTIALS",
        )
        with tempfile.TemporaryDirectory(prefix="pfy-xintake-smolvm-env-") as td:
            root = Path(td)
            proc, _receipt = self._run_smolvm(root, plant={key: "pfy-test-dummy" for key in secret_names})
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, blob)
            seen = (root / "smolvm-env-names").read_text(encoding="utf-8").splitlines()
            self.assertFalse(any("=" in line for line in seen), "env dump included values")
            leaked = [key for key in secret_names if key in seen]
            self.assertEqual(leaked, [], f"smolvm child saw secret names {leaked}")
            self.assertIn("PATH", seen)


if __name__ == "__main__":
    unittest.main()
