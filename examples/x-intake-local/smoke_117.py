#!/usr/bin/env python3
"""Entry 117 NVIDIA AI-Q (Deep Researcher Agent) local smoke. Stdlib only.

Exit 0 PASS, 1 FAIL, 2 can't run here.
Receipt: pipelines/smoke/aiq/latest.json (override with AIQ_RECEIPT; unit tests set it)

Staging is a separate step. A plain run never installs or clones.

  python3 examples/x-intake-local/smoke_117.py --stage
  python3 examples/x-intake-local/smoke_117.py --entry aiq

The child environment is built from scratch (PATH, HOME, TERM, LANG, NO_COLOR,
and the explicit extras below). Parent *_API_KEY / NGC / TAVILY values are not
copied. The only API key is the literal ``local-dummy`` written into the
generated YAML, which the blueprint treats as "no env var required".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO_URL = "https://github.com/NVIDIA-AI-Blueprints/aiq.git"
PIN_SHA = "951a1a1114e9818073ddbe2a5fdbfa824751f4d3"
NAT_VERSION = "1.8.0"
AIQ_VERSION = "2.2.0"
NEMO_RELAY_REV = "ffb24817442bac99212da0971b13bdad5bc4d84d"
MODEL = "qwen3.6:35b"
OLLAMA_BASE = "http://localhost:11434"
OPENAI_BASE = OLLAMA_BASE + "/v1"
DUMMY_API_KEY = "local-dummy"
QUERY = (
    "What is one recent news headline about the Rust programming language? "
    "Answer in two or three sentences and cite the news source. "
    "This is a single factual question, not a deep report."
)
ENTRY = "aiq"

# None until the first probe. Empty tuple means bubblewrap is unusable here.
_BWRAP_FLAGS: tuple[str, ...] | None = None
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def stage_root() -> Path:
    raw = (os.environ.get("AIQ_ROOT") or "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / "DEVELOP/pfy-mentat/tmp/aiq"


def develop_root() -> Path:
    return Path.home() / "DEVELOP"


def receipt_path() -> Path:
    """Operator receipt, unless AIQ_RECEIPT points at a unit-test file."""
    override = os.environ.get("AIQ_RECEIPT", "").strip()
    if override:
        return Path(override)
    return ROOT / "pipelines/smoke" / ENTRY / "latest.json"


def write(receipt: dict, code: int) -> int:
    receipt["exit_code"] = code
    receipt["verdict"] = {0: "PASS", 1: "FAIL", 2: "FAIL_CANNOT_RUN_HERE"}[code]
    out = receipt_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: receipt.get(k) for k in ("verdict", "reason")}, ensure_ascii=False))
    print(f"receipt: {out}")
    return code


def _child_env(home: str, path: str = "/usr/bin:/bin", extra: dict | None = None) -> dict[str, str]:
    """An environment with nothing copied from this process. HOME is always `home`."""
    env = {"PATH": path, "TERM": "dumb", "LANG": "C.UTF-8", "NO_COLOR": "1"}
    for key, value in (extra or {}).items():
        if key != "HOME":
            env[str(key)] = str(value)
    env["HOME"] = home
    return env


def _spawn(cmd: list[str], env: dict, cwd: str | None, timeout: float) -> subprocess.CompletedProcess:
    """New session. On timeout SIGKILL the process group so a forked grandchild dies too."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        raise subprocess.TimeoutExpired(cmd, timeout)
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def _probe_bwrap() -> tuple[str, ...]:
    bw = shutil.which("bwrap")
    if not bw:
        return ()
    flags = ["--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--unshare-net", "--die-with-parent"]
    with tempfile.TemporaryDirectory(prefix="pfy-bwrap-probe-") as home:
        env = _child_env(home)
        for extra in (["--unshare-pid"], []):
            try:
                probe = _spawn([bw, *flags, *extra, "/bin/true"], env, None, 10)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if probe.returncode == 0:
                return tuple([bw, *flags, *extra])
    return ()


def _bwrap_prefix(writable: list[str]) -> list[str]:
    global _BWRAP_FLAGS
    if _BWRAP_FLAGS is None:
        _BWRAP_FLAGS = _probe_bwrap()
    if not _BWRAP_FLAGS:
        return []
    prefix = list(_BWRAP_FLAGS)
    for directory in writable:
        prefix += ["--bind", directory, directory]
    return prefix


def run_isolated(
    cmd: list[str],
    *,
    home: str,
    cwd: str | None = None,
    timeout: float = 120,
    path: str = "/usr/bin:/bin",
    extra: dict | None = None,
    bwrap_writable: list[str] | None = None,
) -> subprocess.CompletedProcess:
    """Start the one kind of child this smoke is allowed to start.

    `home` is the child's HOME. PATH, TERM, LANG, NO_COLOR, and the explicit
    `extra` keys are the only other variables. This process's environment is
    not copied. The child is a new session; a timeout SIGKILLs that process
    group, grandchildren included. `bwrap_writable=None` skips bubblewrap.
    The research run needs Ollama and DuckDuckGo, so it does not pass bwrap.
    """
    argv = list(cmd)
    if bwrap_writable is not None:
        prefix = _bwrap_prefix(bwrap_writable)
        if prefix:
            argv = prefix + argv
    return _spawn(argv, _child_env(home, path, extra), cwd, timeout)


def timeout_reason(tag: str) -> str:
    return f"{tag} timeout"


def research_timeout() -> float:
    raw = (os.environ.get("PFY_XINTAKE_TIMEOUT") or "").strip()
    if raw:
        try:
            value = float(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
    return 900.0


def ollama_base() -> str:
    return (os.environ.get("AIQ_OLLAMA_URL") or OLLAMA_BASE).rstrip("/")


def openai_base() -> str:
    return ollama_base() + "/v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _under_develop(path: Path) -> bool:
    try:
        path.resolve().relative_to(develop_root().resolve())
    except ValueError:
        return False
    return True


def resolve_nat(root: Path) -> str | None:
    raw = (os.environ.get("AIQ_BIN") or "").strip()
    if raw:
        if os.path.isfile(raw) and os.access(raw, os.X_OK):
            return raw
        return None
    nat = root / ".venv" / "bin" / "nat"
    if nat.is_file() and os.access(nat, os.X_OK):
        return str(nat)
    return None


def resolve_src(root: Path) -> Path | None:
    """Source checkout to pin. A stub AIQ_BIN with no AIQ_SRC skips the pin."""
    raw = (os.environ.get("AIQ_SRC") or "").strip()
    if raw:
        return Path(raw).expanduser()
    if (os.environ.get("AIQ_BIN") or "").strip():
        return None
    src = root / "src"
    return src if src.exists() else None


def local_config(checkpoint_db: Path) -> str:
    """Every LLM role points at Ollama. The only search tool is DuckDuckGo News."""
    base = openai_base()
    return f"""\
# Generated by examples/x-intake-local/smoke_117.py. Local only. Not a secret.
general:
  telemetry:
    logging:
      console:
        _type: console
        level: WARNING

llms:
  local_llm:
    _type: openai
    model_name: {MODEL}
    base_url: "{base}"
    api_key: {DUMMY_API_KEY}
    temperature: 0.1
    max_retries: 1
    # langchain-openai 1.2.2 has no max_tokens constructor argument.
    model_kwargs:
      max_tokens: 1024
    extra_body:
      think: false

functions:
  data_sources:
    _type: data_source_registry
    sources:
      - id: news_search
        name: "News Search"
        description: "Search recent news articles."
        tools:
          - duckduckgo_news_search_tool

  duckduckgo_news_search_tool:
    _type: duckduckgo_news_search
    max_results: 3
    timelimit: w
    timeout: 20

  intent_classifier:
    _type: intent_classifier
    llm: local_llm
    tools:
      - duckduckgo_news_search_tool
    llm_timeout: 180

  clarifier_agent:
    _type: clarifier_agent
    llm: local_llm
    tools:
      - duckduckgo_news_search_tool
    max_turns: 1

  shallow_research_agent:
    _type: shallow_research_agent
    llm: local_llm
    tools:
      - duckduckgo_news_search_tool
    max_llm_turns: 4
    max_tool_iterations: 2
    enforce_citations: false

  deep_research_agent:
    _type: deep_research_agent
    orchestrator_llm: local_llm
    source_router_llm: local_llm
    researcher_llm: local_llm
    planner_llm: local_llm
    writer_llm: local_llm
    tools:
      - duckduckgo_news_search_tool
    enable_source_router: true
    enable_citation_verification: false
    max_researcher_model_calls: 2
    resource_limits:
      max_execution_seconds: 180

workflow:
  _type: chat_deepresearcher_agent
  enable_escalation: false
  enable_clarifier: false
  checkpoint_db: "{checkpoint_db}"
"""


def ollama_problem(base: str) -> str | None:
    url = base + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            payload = json.loads(resp.read(2_000_000).decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return f"ollama unreachable at {url} ({type(exc).__name__})"
    names = []
    for row in payload.get("models") or []:
        if isinstance(row, dict):
            names.append(str(row.get("name") or row.get("model") or ""))
    if not any(name == MODEL or name.startswith(MODEL + ":") or name.startswith(MODEL) for name in names):
        return f"ollama at {base} has no {MODEL}"
    return None


def extract_report(blob: str) -> str:
    clean = ANSI.sub("", blob)
    marker = "Workflow Result:"
    if marker not in clean:
        return ""
    body = clean.split(marker, 1)[1]
    lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and set(stripped) <= {"-"} and len(stripped) >= 10:
            if lines:
                break
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _tool_path(nat: str) -> str:
    bindir = str(Path(nat).resolve().parent)
    return bindir + ":/usr/bin:/bin"


def _git_sha(src: Path, home: str) -> subprocess.CompletedProcess:
    return run_isolated(
        ["git", "-C", str(src), "rev-parse", "HEAD"],
        home=home, timeout=30, path="/usr/bin:/bin",
    )


def smoke_aiq(receipt: dict) -> int:
    root = stage_root()
    receipt["stage_root"] = str(root)
    receipt["pin"] = PIN_SHA
    receipt["nat_version_pin"] = NAT_VERSION
    receipt["model"] = MODEL
    receipt["openai_base_url"] = openai_base()
    receipt["search_tool"] = "duckduckgo_news_search"
    receipt["dummy_api_key_location"] = "config literal only"
    nat = resolve_nat(root)
    if not nat:
        receipt["reason"] = (
            "AI-Q venv is not staged (missing .venv/bin/nat). "
            "Run: python3 examples/x-intake-local/smoke_117.py --stage"
        )
        return 2
    receipt["nat_bin"] = nat

    with tempfile.TemporaryDirectory(prefix="pfy-aiq-117-") as td:
        home = str(Path(td) / "home")
        scratch = Path(td) / "scratch"
        os.makedirs(home, exist_ok=True)
        scratch.mkdir()
        src = resolve_src(root)
        if src is not None:
            if not (src / ".git").is_dir():
                receipt["reason"] = f"AI-Q source is not a git checkout: {src}"
                return 2
            try:
                probed = _git_sha(src, home)
            except subprocess.TimeoutExpired:
                receipt["reason"] = timeout_reason("aiq git rev-parse")
                return 1
            sha = (probed.stdout or "").strip()
            receipt["source_sha"] = sha
            if probed.returncode != 0 or sha != PIN_SHA:
                receipt["reason"] = f"AI-Q checkout {src} is {sha or 'unreadable'}, pin is {PIN_SHA}"
                return 2

        try:
            version = run_isolated([nat, "--version"], home=home, timeout=60, path=_tool_path(nat))
        except subprocess.TimeoutExpired:
            receipt["reason"] = timeout_reason("aiq version")
            return 1
        receipt["nat_version"] = ((version.stdout or "") + (version.stderr or "")).strip().splitlines()[:2]
        if version.returncode != 0 or NAT_VERSION not in (version.stdout or "") + (version.stderr or ""):
            receipt["reason"] = f"nat --version did not report {NAT_VERSION}"
            return 2

        problem = ollama_problem(ollama_base())
        if problem:
            receipt["reason"] = problem
            return 2

        checkpoint = scratch / "checkpoints.db"
        config_path = scratch / "local-ollama.yml"
        config_path.write_text(local_config(checkpoint), encoding="utf-8")
        # The dummy key stays in the file. It is not copied into the child env.
        if DUMMY_API_KEY not in config_path.read_text(encoding="utf-8"):
            receipt["reason"] = "generated config is missing the dummy api_key literal"
            return 1
        try:
            ran = run_isolated(
                [nat, "run", "--config_file", str(config_path), "--input", QUERY],
                home=home,
                cwd=str(scratch),
                timeout=research_timeout(),
                path=_tool_path(nat),
                extra={
                    "TMPDIR": str(scratch),
                    "NAT_CONFIG_FILE": str(config_path),
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
        except subprocess.TimeoutExpired:
            receipt["reason"] = timeout_reason("aiq research")
            return 1
        blob = (ran.stdout or "") + "\n" + (ran.stderr or "")
        report = extract_report(blob)
        receipt["nat_exit"] = ran.returncode
        receipt["report_chars"] = len(report)
        receipt["report_excerpt"] = report[:500]
        lowered = report.lower()
        bad = (
            "missing required api keys" in lowered
            or "an error occurred while researching" in lowered
            or lowered.startswith("error:")
        )
        if ran.returncode != 0 or len(report) < 40 or bad:
            tail = (ran.stderr or ran.stdout or "").strip().splitlines()
            receipt["reason"] = "research did not return a non-empty report"
            receipt["output_tail"] = tail[-20:]
            return 1
        receipt["reason"] = "non-empty local research report"
        return 0


def _uv_bin() -> str | None:
    return shutil.which("uv")


def _stage_env_extra(root: Path) -> dict[str, str]:
    return {
        "UV_CACHE_DIR": str(root / "uv-cache"),
        "UV_PYTHON_INSTALL_DIR": str(root / "python"),
        "UV_PROJECT_ENVIRONMENT": str(root / ".venv"),
        "UV_LINK_MODE": "copy",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
    }


def _freeze_record(root: Path, home: str, uv: str) -> dict:
    python = root / ".venv" / "bin" / "python"
    freeze = run_isolated(
        [uv, "pip", "freeze", "--python", str(python)],
        home=home, timeout=120, path=_tool_path(uv), extra=_stage_env_extra(root),
    )
    text = freeze.stdout or ""
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    lock = root / "src" / "uv.lock"
    cache = root / "uv-cache"
    wheels = sorted(path for path in cache.rglob("*") if path.is_file() and ".whl" in path.name) if cache.is_dir() else []
    wheel_rows = []
    for path in wheels:
        wheel_rows.append({"name": path.name, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    return {
        "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
        "uv_pip_freeze_sha256": sha256_text(text),
        "uv_pip_freeze_count": len(lines),
        "wheel_files": len(wheel_rows),
        "wheel_sha256": [
            {"name": row["name"], "sha256": row["sha256"], "bytes": row["bytes"]} for row in wheel_rows
        ],
        "freeze_exit": freeze.returncode,
    }


def stage(receipt: dict) -> int:
    root = stage_root()
    if not _under_develop(root):
        receipt["reason"] = f"stage root must be under {develop_root()}"
        return 2
    root.mkdir(parents=True, exist_ok=True)
    for name in ("home", "uv-cache", "python", "logs"):
        (root / name).mkdir(exist_ok=True)
    uv = _uv_bin()
    if not uv:
        receipt["reason"] = "uv is not on PATH; staging cannot download a toolchain into the system"
        return 2
    home = str(root / "home")
    src = root / "src"
    extra = _stage_env_extra(root)
    path = _tool_path(uv)
    if not (src / ".git").is_dir():
        try:
            cloned = run_isolated(
                ["git", "clone", "--depth", "1", REPO_URL, str(src)],
                home=home, timeout=300, path="/usr/bin:/bin", extra=extra,
            )
        except subprocess.TimeoutExpired:
            receipt["reason"] = timeout_reason("aiq clone")
            return 1
        if cloned.returncode != 0:
            receipt["reason"] = "git clone of AI-Q failed"
            receipt["output_tail"] = (cloned.stderr or "").strip().splitlines()[-20:]
            return 1
    try:
        probed = _git_sha(src, home)
    except subprocess.TimeoutExpired:
        receipt["reason"] = timeout_reason("aiq git rev-parse")
        return 1
    sha = (probed.stdout or "").strip()
    receipt["source_sha"] = sha
    if sha != PIN_SHA:
        receipt["reason"] = f"refusing to move {src} from {sha} to pin {PIN_SHA}"
        return 2
    try:
        synced = run_isolated(
            [uv, "sync", "--python", "3.13", "--frozen", "--group", "dev"],
            home=home, cwd=str(src), timeout=1800, path=path, extra=extra,
        )
    except subprocess.TimeoutExpired:
        receipt["reason"] = timeout_reason("aiq uv sync")
        return 1
    log = root / "logs" / "uv-sync-stage.log"
    log.write_text((synced.stdout or "") + "\n" + (synced.stderr or ""), encoding="utf-8")
    if synced.returncode != 0 or not (root / ".venv" / "bin" / "nat").is_file():
        receipt["reason"] = "uv sync did not produce .venv/bin/nat"
        receipt["output_tail"] = (synced.stderr or synced.stdout or "").strip().splitlines()[-30:]
        return 1
    downloads = _freeze_record(root, home, uv)
    downloads["aiq_commit"] = PIN_SHA
    downloads["aiq_version"] = AIQ_VERSION
    downloads["nemo_relay_rev"] = NEMO_RELAY_REV
    downloads["nat_version"] = NAT_VERSION
    stage_receipt = root / "stage-receipt.json"
    stage_receipt.write_text(json.dumps(downloads, indent=2) + "\n", encoding="utf-8")
    receipt["downloads"] = {
        key: downloads[key]
        for key in (
            "aiq_commit", "uv_lock_sha256", "uv_pip_freeze_sha256", "uv_pip_freeze_count", "wheel_files",
            "nemo_relay_rev", "nat_version",
        )
    }
    receipt["stage_receipt"] = str(stage_receipt)
    receipt["reason"] = f"staged {PIN_SHA} with {downloads['uv_pip_freeze_count']} frozen packages"
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Entry 117 AI-Q local smoke")
    parser.add_argument("--entry", choices=[ENTRY])
    parser.add_argument("--stage", action="store_true", help="Install the pinned AI-Q checkout into the uv venv")
    args = parser.parse_args()
    if not args.stage and args.entry != ENTRY:
        parser.error("pass --entry aiq, or --stage")
    receipt: dict = {"entry": ENTRY, "pin": PIN_SHA}
    if args.stage:
        code = stage(receipt)
        if args.entry != ENTRY:
            return write(receipt, code)
        if code != 0:
            return write(receipt, code)
    code = smoke_aiq(receipt)
    stage_receipt = stage_root() / "stage-receipt.json"
    if stage_receipt.is_file() and "downloads" not in receipt:
        try:
            loaded = json.loads(stage_receipt.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            loaded = {}
        receipt["downloads"] = {
            key: loaded.get(key)
            for key in (
                "aiq_commit", "uv_lock_sha256", "uv_pip_freeze_sha256", "uv_pip_freeze_count", "wheel_files",
                "nemo_relay_rev",
            )
        }
    return write(receipt, code)


if __name__ == "__main__":
    sys.exit(main())
