"""CLI entry: python -m write_guard | write-guard-mcp"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from write_guard.policy import decide, load_policy, resolve_mode, resolve_roots


def cmd_selftest() -> int:
    """Policy self-test without MCP (always runnable)."""
    # Use in-memory policy defaults + temp paths
    from write_guard.policy import Policy

    pol = Policy(
        roots=["/workspace"],
        deny_globs=["**/.env", "**/auth.json", "**/*secret*"],
        allow_write_globs=["/workspace/**"],
        deny_write_globs=["/workspace/.write-guard-audit.jsonl"],
        allow_delete_globs=[],
        default_mode="enforce",
    )
    cases = [
        ("write", "/workspace/ok.txt", "enforce", True),
        ("write", "/workspace/.env", "enforce", False),
        ("write", "/etc/passwd", "enforce", False),
        ("write", "/workspace/foo/secret_key.txt", "enforce", False),
        ("write", "/workspace/ok.txt", "audit", True),
        ("write", "/workspace/.env", "audit", True),  # audit allows but flags
        ("delete", "/workspace/ok.txt", "enforce", False),
        ("read", "/workspace/ok.txt", "enforce", True),
    ]
    failed = 0
    for op, path, mode, expect in cases:
        d = decide(path, op=op, mode=mode, policy=pol)
        ok = d.allow == expect
        status = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  {status} {op:6} {mode:7} {path} -> allow={d.allow} ({d.reason})")
    if failed:
        print(f"selftest: FAIL ({failed} cases)")
        return 1
    print("selftest: PASS")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    pol = load_policy(args.policy)
    mode = args.mode or resolve_mode(pol)
    roots = resolve_roots(pol)
    d = decide(args.path, op=args.op, mode=mode, policy=pol, roots=roots)
    print(json.dumps({"allow": d.allow, "reason": d.reason, "mode": d.mode, "path": d.path}))
    return 0 if d.allow else 2


def cmd_serve() -> int:
    from write_guard.server import run_stdio

    run_stdio()
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="write-guard-mcp")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("selftest", help="Run policy unit self-test")
    sub.add_parser("serve", help="Run MCP server on stdio (default)")

    c = sub.add_parser("check", help="Check one path decision")
    c.add_argument("--path", required=True)
    c.add_argument("--op", default="write", choices=["read", "write", "delete", "list"])
    c.add_argument("--mode", default=None)
    c.add_argument("--policy", default=None)

    args = p.parse_args(argv)
    cmd = args.cmd or "serve"
    if cmd == "selftest":
        return cmd_selftest()
    if cmd == "check":
        return cmd_check(args)
    if cmd == "serve":
        return cmd_serve()
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
