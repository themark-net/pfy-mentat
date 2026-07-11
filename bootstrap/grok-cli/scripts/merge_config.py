#!/usr/bin/env python3
"""Idempotent surgical merge of owned Grok config.toml keys.

Does not re-serialize the whole file (preserves comments, [[array.tables]],
and unrelated sections). Only upserts:

  [memory] enabled = true
  [ui] permission_mode = "..."
  [mcp_servers.codebase-memory] (full owned block)
  [skills] paths += ponytail path (creates [skills] if missing)

Creates a timestamped backup by default.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

HEADER_RE = re.compile(r"^\[([^\[\]]+)\]\s*$")  # single [section] only
AOT_RE = re.compile(r"^\[\[.+\]\]\s*$")  # [[array.of.tables]]


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = path.with_suffix(path.suffix + f".bak.{stamp}")
    shutil.copy2(path, dest)
    return dest


def section_header(line: str) -> str | None:
    """Return section name for [name], or None for plain lines / [[aot]]."""
    if AOT_RE.match(line):
        return None  # stay in previous logical table-array context; caller treats as non-header
    m = HEADER_RE.match(line)
    return m.group(1) if m else None


def parse_string_array(rhs: str) -> list[str]:
    return re.findall(r'"([^"]*)"', rhs)


def format_string_array(items: list[str]) -> str:
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


def paths_contain(items: list[str], wanted: str) -> bool:
    wanted_exp = str(Path(wanted).expanduser())
    for e in items:
        if e == wanted or e == wanted_exp:
            return True
        try:
            if Path(e).expanduser().resolve() == Path(wanted).expanduser().resolve():
                return True
        except OSError:
            continue
    return False


def merge(
    text: str,
    *,
    ponytail_path: str | None,
    permission_mode: str | None,
) -> str:
    lines = text.splitlines(keepends=True)
    if text and not text.endswith("\n"):
        # normalize: we'll rejoin with preserved endings
        pass

    out: list[str] = []
    current: str | None = None
    seen_memory = False
    seen_ui = False
    seen_mcp = False
    seen_skills = False
    # When replaying mcp section, skip old body until next real header
    skip_mcp_body = False
    memory_has_enabled = False
    ui_has_permission = False
    skills_has_paths = False
    skills_has_ignore = False
    skills_has_disabled = False

    def flush_section_tail(sec: str | None) -> None:
        nonlocal memory_has_enabled, ui_has_permission
        nonlocal skills_has_paths, skills_has_ignore, skills_has_disabled
        if sec == "memory" and not memory_has_enabled:
            out.append("enabled = true\n")
            memory_has_enabled = True
        if sec == "ui" and permission_mode and not ui_has_permission:
            out.append(f'permission_mode = "{permission_mode}"\n')
            ui_has_permission = True
        if sec == "skills":
            if ponytail_path and not skills_has_paths:
                out.append(f'paths = ["{ponytail_path}"]\n')
                skills_has_paths = True
            if not skills_has_ignore:
                out.append("ignore = []\n")
                skills_has_ignore = True
            if not skills_has_disabled:
                out.append("disabled = []\n")
                skills_has_disabled = True

    i = 0
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip("\n")
        hdr = section_header(raw)

        if skip_mcp_body:
            if hdr is not None:
                skip_mcp_body = False
                # fall through to handle this header
            elif AOT_RE.match(raw):
                skip_mcp_body = False
                out.append(line)
                i += 1
                continue
            else:
                i += 1
                continue

        if hdr is not None:
            # Leaving previous section — ensure required keys
            flush_section_tail(current)
            current = hdr

            if hdr == "memory":
                seen_memory = True
                memory_has_enabled = False
                out.append(line)
            elif hdr == "ui":
                seen_ui = True
                ui_has_permission = False
                out.append(line)
            elif hdr == "mcp_servers.codebase-memory":
                seen_mcp = True
                # Replace entire section with owned block; skip old body
                out.append("[mcp_servers.codebase-memory]\n")
                out.append('command = "codebase-memory-mcp"\n')
                out.append("args = []\n")
                out.append("enabled = true\n")
                out.append("\n")
                skip_mcp_body = True
                current = None  # already fully written
            elif hdr == "skills":
                seen_skills = True
                skills_has_paths = False
                skills_has_ignore = False
                skills_has_disabled = False
                out.append(line)
            else:
                out.append(line)
            i += 1
            continue

        # Non-header line
        if current == "memory":
            if re.match(r"^enabled\s*=", raw):
                out.append("enabled = true\n")
                memory_has_enabled = True
            else:
                out.append(line)
        elif current == "ui":
            if re.match(r"^permission_mode\s*=", raw):
                if permission_mode:
                    out.append(f'permission_mode = "{permission_mode}"\n')
                    ui_has_permission = True
                else:
                    out.append(line)
                    ui_has_permission = True
            else:
                out.append(line)
        elif current == "skills":
            if re.match(r"^paths\s*=", raw):
                skills_has_paths = True
                if ponytail_path:
                    items = parse_string_array(raw)
                    if not paths_contain(items, ponytail_path):
                        items.append(ponytail_path)
                    out.append(f"paths = {format_string_array(items)}\n")
                else:
                    out.append(line)
            elif re.match(r"^ignore\s*=", raw):
                skills_has_ignore = True
                out.append(line)
            elif re.match(r"^disabled\s*=", raw):
                skills_has_disabled = True
                out.append(line)
            else:
                out.append(line)
        else:
            out.append(line)
        i += 1

    # EOF flush
    flush_section_tail(current)

    # Append missing owned sections
    def ensure_trailing_nl() -> None:
        if out and not out[-1].endswith("\n"):
            out[-1] = out[-1] + "\n"

    if not seen_memory:
        ensure_trailing_nl()
        out.append("\n[memory]\n")
        out.append("enabled = true\n")

    if permission_mode and not seen_ui:
        ensure_trailing_nl()
        out.append("\n[ui]\n")
        out.append(f'permission_mode = "{permission_mode}"\n')
    elif permission_mode and seen_ui and not ui_has_permission:
        # edge: empty [ui] section already flushed — already handled in flush
        pass

    if not seen_mcp:
        ensure_trailing_nl()
        out.append("\n[mcp_servers.codebase-memory]\n")
        out.append('command = "codebase-memory-mcp"\n')
        out.append("args = []\n")
        out.append("enabled = true\n")

    if ponytail_path and not seen_skills:
        ensure_trailing_nl()
        out.append("\n[skills]\n")
        out.append(f'paths = ["{ponytail_path}"]\n')
        out.append("ignore = []\n")
        out.append("disabled = []\n")

    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--ponytail-path", default=None)
    ap.add_argument(
        "--permission-mode",
        default="always-approve",
        help='ui.permission_mode; pass empty string "" to skip',
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    path = args.config.expanduser()
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    perm = args.permission_mode if args.permission_mode != "" else None
    new = merge(text, ponytail_path=args.ponytail_path, permission_mode=perm)

    if new == text:
        print(f"config unchanged: {path}")
        return 0

    if args.dry_run:
        print(f"would update: {path}")
        print("--- preview ---")
        print(new, end="" if new.endswith("\n") else "\n")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    if not args.no_backup and path.exists():
        b = backup(path)
        if b:
            print(f"backup: {b}")
    path.write_text(new, encoding="utf-8")
    print(f"updated: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
