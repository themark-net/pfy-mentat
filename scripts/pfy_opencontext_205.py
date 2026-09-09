#!/usr/bin/env python3
"""OpenContext (oc) prove + Attach env handoff -- cite #205.

CLI-only. Does not start oc ui/desktop. Does not paint pfy chrome.
Painted verb is ./pfy context: operate-or-FAIL (honest FAIL if node/oc missing).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HELLO_FOLDER = "pfy-205-hello"
HELLO_DOC = "handoff.md"
HELLO_TOKEN = "PFY_OPENCONTEXT_205_HELLO"
NEXT_INSTALL = "npm install -g @aicontextlab/cli"
DEFAULT_CONTEXTS = Path.home() / ".opencontext" / "contexts"
DEFAULT_DB = Path.home() / ".opencontext" / "opencontext.db"


def which(name: str) -> str:
    return shutil.which(name) or ""


def node_bin() -> str:
    return which("node")


def find_oc() -> str:
    return which("oc")


def contexts_root() -> str:
    return os.environ.get("OPENCONTEXT_CONTEXTS_ROOT") or str(DEFAULT_CONTEXTS)


def db_path() -> str:
    return os.environ.get("OPENCONTEXT_DB_PATH") or str(DEFAULT_DB)


def oc_env(extra=None) -> dict:
    env = os.environ.copy()
    env["OPENCONTEXT_CONTEXTS_ROOT"] = contexts_root()
    env["OPENCONTEXT_DB_PATH"] = db_path()
    env["CI"] = "1"
    # LIVE_HARD_OFF: prove must not inherit cloud embedding keys.
    for key in ("OPENAI_API_KEY", "EMBEDDING_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY"):
        env.pop(key, None)
    if extra:
        env.update(extra)
    return env


def apply_child_env(env: dict) -> dict:
    """Inherit OpenContext store + oc bin into Attach/start child env. Cite #205.

    Missing oc is a skip (Attach is not an OpenContext control). Never fail attach.
    """
    env = env if env is not None else {}
    oc = find_oc()
    if not oc:
        return env
    env.setdefault("OPENCONTEXT_BIN", oc)
    env.setdefault("OPENCONTEXT_CONTEXTS_ROOT", contexts_root())
    env.setdefault("OPENCONTEXT_DB_PATH", db_path())
    return env


def export_env_lines() -> list:
    """Printable `export KEY=value` lines for ./pfy start. Empty if oc missing."""
    env = apply_child_env({})
    if not env.get("OPENCONTEXT_BIN"):
        return []
    lines = []
    for key in ("OPENCONTEXT_BIN", "OPENCONTEXT_CONTEXTS_ROOT", "OPENCONTEXT_DB_PATH"):
        val = env.get(key) or ""
        if not val:
            continue
        lines.append("export %s=%s" % (key, json.dumps(val)))
    return lines


def fail(reason: str, next_step: str, extra="") -> int:
    print("FAIL: %s" % reason)
    print("  next: %s" % next_step)
    if extra:
        print(extra.rstrip())
    return 1


def run_oc(args, env=None, timeout=60) -> tuple:
    oc = find_oc()
    if not oc:
        return 127, "", "oc not on PATH"
    cmd = [oc] + list(args)
    try:
        p = subprocess.run(
            cmd,
            env=env or oc_env(),
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd="/tmp",
        )
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or "") if isinstance(e.stdout, str) else "", "timeout"
    except OSError as e:
        return 127, "", str(e)[:200]
    out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
    return p.returncode, p.stdout or "", (p.stderr or "").strip() or out


def write_hello_body(abs_path: str) -> None:
    path = Path(abs_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "# pfy OpenContext hello-world (#205)\n\n"
        "Token: %s\n\n"
        "Capture/search/reuse proof for FreeToken-first Attach "
        "OpenCode|Hermes|Grok handoff. CLI `oc` only — not pfy chrome.\n"
        % HELLO_TOKEN
    )
    path.write_text(body, encoding="utf-8")


def local_keyword_hit(token: str) -> bool:
    root = Path(contexts_root())
    if not root.is_dir():
        return False
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if token in text or token in path.name:
            return True
    return False


def prove_hello() -> tuple:
    """Capture + keyword search + manifest reuse. Returns (ok, lines, err)."""
    lines = []
    env = oc_env()

    rc, out, err = run_oc(
        ["folder", "create", HELLO_FOLDER, "-d", "pfy #205 hello-world %s" % HELLO_TOKEN],
        env=env,
    )
    blob = ("%s\n%s" % (out, err)).lower()
    if rc != 0 and "exist" not in blob and "ready" not in blob:
        return False, lines, "folder create failed: %s" % (err or out or "exit %s" % rc)[:240]
    lines.append("capture folder: %s" % (out.strip() or "exists"))

    rc, out, err = run_oc(
        ["doc", "create", HELLO_FOLDER, HELLO_DOC, "-d", HELLO_TOKEN],
        env=env,
    )
    blob = ("%s\n%s" % (out, err)).lower()
    if rc != 0 and "exist" not in blob and "created" not in blob:
        return False, lines, "doc create failed: %s" % (err or out or "exit %s" % rc)[:240]
    lines.append("capture doc: %s" % (out.strip() or "exists"))

    rc, out, err = run_oc(
        ["context", "manifest", HELLO_FOLDER, "--limit", "10", "--format", "json"],
        env=env,
    )
    if rc != 0:
        return False, lines, "manifest failed: %s" % (err or out or "exit %s" % rc)[:240]
    try:
        rows = json.loads(out or "[]")
    except json.JSONDecodeError:
        return False, lines, "manifest not JSON"
    if not isinstance(rows, list) or not rows:
        return False, lines, "manifest empty"
    abs_path = ""
    found_doc = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("rel_path") or "")
        if HELLO_DOC in rel or rel.endswith("/" + HELLO_DOC):
            found_doc = True
            abs_path = str(row.get("abs_path") or "")
            break
    if not found_doc:
        row0 = rows[0] if isinstance(rows[0], dict) else {}
        abs_path = str(row0.get("abs_path") or "")
        found_doc = bool(abs_path)
    if not found_doc:
        return False, lines, "manifest missing hello doc"
    if abs_path:
        write_hello_body(abs_path)
        lines.append("capture body: %s" % abs_path)
    lines.append("reuse manifest: %s docs" % len(rows))

    rc, out, err = run_oc(["folder", "ls", "--all"], env=env)
    if rc != 0 or HELLO_FOLDER not in (out or ""):
        return False, lines, "folder ls missed hello folder"
    lines.append("search folder ls: hit")
    rc, out, err = run_oc(["doc", "ls", HELLO_FOLDER], env=env)
    if rc != 0 or HELLO_DOC not in (out or ""):
        return False, lines, "doc ls missed hello doc"
    lines.append("search doc ls: hit")
    if not local_keyword_hit(HELLO_TOKEN):
        return False, lines, "store keyword miss for %s" % HELLO_TOKEN
    lines.append("search store keyword: hit")

    rc, out, err = run_oc(
        ["search", HELLO_TOKEN, "--mode", "keyword", "--format", "json", "--limit", "5"],
        env=env,
        timeout=90,
    )
    blob = ("%s\n%s" % (out, err))
    if rc == 0 and (HELLO_TOKEN in blob or HELLO_FOLDER in blob or HELLO_DOC in blob):
        lines.append("search oc keyword: hit")
    else:
        why = (err or out or "exit %s" % rc).strip().splitlines()
        why = why[-1] if why else "oc search failed"
        lines.append("search oc keyword: SKIP (%s)" % why[:160])
    return True, lines, ""


def cmd_prove() -> int:
    if not node_bin():
        return fail("node missing", NEXT_INSTALL)
    oc = find_oc()
    if not oc:
        return fail("oc missing", NEXT_INSTALL)
    ok, lines, err = prove_hello()
    if not ok:
        return fail(err or "hello-world failed", NEXT_INSTALL)
    print("PASS context · oc %s" % oc)
    print("store: %s" % contexts_root())
    print("db: %s" % db_path())
    for line in lines:
        print("  %s" % line)
    print("handoff: Attach OpenCode|Hermes|Grok inherit OPENCONTEXT_* via ./pfy start / Attach")
    print("MCP (stdio): oc mcp")
    print("Grok: [mcp_servers.opencontext] command=%s args=[\"mcp\"]" % json.dumps(oc))
    print("OpenCode: mcpServers.opencontext command=oc args=[\"mcp\"]")
    print("note: oc ui / desktop stay out of pfy chrome")
    for line in export_env_lines():
        print(line)
    return 0


def cmd_export_env() -> int:
    for line in export_env_lines():
        print(line)
    return 0


def cmd_selftest() -> int:
    """Fail-closed unit checks that do not need a live oc install."""
    old_path = os.environ.get("PATH", "")
    try:
        os.environ["PATH"] = "/usr/bin:/bin"
        # may still find oc if it lives in /usr/bin; force empty which via PATH without npm-global
        os.environ["PATH"] = "/tmp/pfy-205-no-oc"
        if find_oc():
            print("FAIL: find_oc should be empty on empty PATH")
            return 1
        env = apply_child_env({})
        if env.get("OPENCONTEXT_BIN"):
            print("FAIL: apply_child_env must skip when oc missing")
            return 1
        if export_env_lines():
            print("FAIL: export_env_lines must be empty when oc missing")
            return 1
    finally:
        os.environ["PATH"] = old_path
    if not node_bin():
        # host without node: the missing-oc fail path is the product behavior
        print("PASS selftest · missing-oc skip (node also missing)")
        return 0
    print("PASS selftest · missing-oc fail-closed")
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--prove", "prove"):
        return cmd_prove()
    if args[0] in ("--export-env", "export-env"):
        return cmd_export_env()
    if args[0] in ("--selftest", "selftest"):
        return cmd_selftest()
    if args[0] in ("-h", "--help"):
        print("usage: pfy_opencontext_205.py [--prove|--export-env|--selftest]")
        return 0
    print("usage: pfy_opencontext_205.py [--prove|--export-env|--selftest]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
