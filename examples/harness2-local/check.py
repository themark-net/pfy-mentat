#!/usr/bin/env python3
"""Local stage check. Does not import harness2.preflight and does not run harness2-check.

Upstream harness2-check only accepts --bench jb|lab|wb, and preflight.check()
raises KeyError for any other adapter name. This wrapper checks the pins, the
OpenCode version files, the local-only .env, and OpencodeSubstrate().preflight().
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import common  # noqa: E402


def _fail(msg: str) -> int:
    print(f"check: {msg}", file=sys.stderr)
    return 2


def _root(argv: list[str]) -> Path:
    if "--root" in argv:
        return Path(argv[argv.index("--root") + 1]).resolve()
    env = os.environ.get("HARNESS2_ROOT")
    if env:
        return Path(env).resolve()
    return common.harness_root()


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def _add_venv(root: Path) -> None:
    if os.environ.get("HARNESS2_CHECK_NO_VENV") == "1":
        return
    lib = root / ".venv" / "lib"
    if not lib.is_dir():
        return
    import site

    for sp in sorted(lib.glob("python*/site-packages")):
        site.addsitedir(str(sp))


def _reexec_venv(root: Path) -> None:
    """Run under the stage's Python 3.12. A stub python that prints no version is ignored."""
    if os.environ.get("HARNESS2_CHECK_NO_VENV") == "1":
        return
    if os.environ.get("HARNESS2_CHECK_REEXEC") == "1":
        return
    py = root / ".venv" / "bin" / "python"
    if not py.is_file():
        return
    probe = subprocess.run(
        [str(py), "-c", "import sys; print(sys.version)"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or not (probe.stdout or "").startswith("3."):
        return
    os.environ["HARNESS2_CHECK_REEXEC"] = "1"
    os.execv(str(py), [str(py), str(Path(__file__).resolve()), *sys.argv[1:]])


def version_output_ok(text: str) -> bool:
    """A source run prints ``local``. A packaged binary may print the pin version."""
    return "local" in text or common.OC_VERSION in text


def _bun_env() -> dict[str, str]:
    env = common.scrub_env(dict(os.environ))
    for name in common.OPENCODE_DISABLE:
        env[name] = "1"
    return env


def _check_version_commands(bun: str, oc: Path) -> str | None:
    proc = subprocess.run([bun, "--version"], capture_output=True, text=True, env=_bun_env())
    text = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return f"bun --version exit {proc.returncode}: {text.strip()}"
    # The bun binary prints its own version (1.3.11). OpenCode's version comes from
    # the source run below, which prints "local" when OPENCODE_VERSION is unset.
    index = oc / "packages" / "opencode" / "src" / "index.ts"
    if not index.is_file():
        return None
    src = oc / "packages" / "opencode"
    proc = subprocess.run(
        [bun, "run", "--cwd", str(src), "--conditions=browser", "src/index.ts", "--version"],
        capture_output=True,
        text=True,
        env=_bun_env(),
    )
    text = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        return f"opencode --version exit {proc.returncode}: {text.strip()}"
    if not version_output_ok(text):
        return f"opencode --version printed {text.strip()!r}"
    return None


def _substrate(root: Path) -> str | None:
    _add_venv(root)
    try:
        import harness2.config as config
        from harness2.substrate.opencode import OpencodeSubstrate
    except Exception as exc:  # import error is a failed check, not a traceback
        return f"cannot import OpencodeSubstrate: {exc}"
    ocdir = Path(config.OPENCODE_DIR)
    if not ocdir.exists():
        return f"config.OPENCODE_DIR missing: {ocdir}"
    bun = config.BUN
    bun_path = Path(bun) if isinstance(bun, Path) else Path(str(bun))
    if not bun_path.is_file():
        return f"config.BUN missing: {bun}"
    try:
        OpencodeSubstrate().preflight()
    except Exception as exc:
        return f"OpencodeSubstrate preflight: {type(exc).__name__}: {exc}"
    err = _check_version_commands(str(bun_path), ocdir)
    if err:
        return err
    return None


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = _root(args)
    _reexec_venv(root)
    etc = Path("/etc/opencode")
    if etc.exists():
        return _fail("/etc/opencode is present")
    env_path = root / ".env"
    if not env_path.is_file():
        return _fail(f"missing {env_path}")
    env = common.parse_dotenv(env_path.read_text(encoding="utf-8"))
    err = common.check_dotenv(env)
    if err:
        return _fail(err)
    head = _git(["git", "-C", str(root), "rev-parse", "HEAD"])
    if head.returncode != 0 or head.stdout.strip() != common.H2_PIN:
        got = head.stdout.strip() or head.stderr.strip()
        return _fail(f"harness2 pin {got or 'missing'} != {common.H2_PIN}")
    oc = root / "dependencies" / "opencode"
    ohead = _git(["git", "-C", str(oc), "rev-parse", "HEAD"])
    if ohead.returncode != 0 or ohead.stdout.strip() != common.OC_PIN:
        got = ohead.stdout.strip() or ohead.stderr.strip()
        return _fail(f"opencode pin {got or 'missing'} != {common.OC_PIN}")
    patch = root / "third_party" / "patches" / "opencode-compat.diff"
    if not patch.is_file():
        return _fail(f"opencode patch missing: {patch}")
    applied = _git(["git", "-C", str(oc), "apply", "--reverse", "--check", str(patch)])
    if applied.returncode != 0:
        return _fail("opencode patch not applied")
    pkg_path = oc / "packages" / "opencode" / "package.json"
    if not pkg_path.is_file():
        return _fail(f"opencode package.json missing: {pkg_path}")
    try:
        version = json.loads(pkg_path.read_text(encoding="utf-8")).get("version")
    except json.JSONDecodeError as exc:
        return _fail(f"opencode package.json: {exc}")
    if version != common.OC_VERSION:
        return _fail(f"opencode version {version} != {common.OC_VERSION}")
    err = _substrate(root)
    if err:
        return _fail(err)
    print("check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
