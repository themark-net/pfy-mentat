#!/usr/bin/env python3
"""Verify first-party Grok skills are complete, consistent, and (optionally) installed.

Exit 0 = all checks pass. Use from repo root or any cwd:

  python3 bootstrap/grok-cli/scripts/verify_skills.py
  python3 bootstrap/grok-cli/scripts/verify_skills.py --installed
  make smoke-grok-skills

Checks (structural — no LLM calls):
  1. manifest.json first_party_skills.skills[] each has a source SKILL.md
  2. Directory name matches frontmatter ``name:``
  3. Frontmatter has non-empty description
  4. Every skills/* dir with SKILL.md is listed in the manifest (no orphans)
  5. project-process sibling skill present
  6. Optional: ~/.grok/skills/<name>/SKILL.md exists and name matches
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*[\"']?([a-z0-9][a-z0-9-]*)[\"']?\s*$", re.M)
DESC_RE = re.compile(r"^description:\s*(.+)$", re.M)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, str] = {}
    nm = NAME_RE.search(block)
    if nm:
        out["name"] = nm.group(1)
    # description may be folded YAML (>) — require the key exists
    if re.search(r"^description:\s*", block, re.M):
        out["description"] = "present"
        # crude: if single-line description, capture value
        dm = re.search(r"^description:\s*[>|]?\s*(.*)$", block, re.M)
        if dm and dm.group(1).strip() and dm.group(1).strip() not in (">", "|", ">-", "|-"):
            if len(dm.group(1).strip()) > 8:
                out["description"] = "ok"
        else:
            # multi-line folded: any non-empty body line after description:
            lines = block.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("description:"):
                    rest = "\n".join(lines[i + 1 :])
                    if re.search(r"\S", rest.split("\nname:")[0] if False else rest[:400]):
                        out["description"] = "ok"
                    break
    return out


def check_skill_file(path: Path, expected_name: str) -> list[str]:
    errs: list[str] = []
    if not path.is_file():
        return [f"missing {path}"]
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return [f"empty {path}"]
    fm = parse_frontmatter(text)
    if not fm.get("name"):
        errs.append(f"{path}: missing frontmatter name:")
    elif fm["name"] != expected_name:
        errs.append(f"{path}: name {fm['name']!r} != dir/manifest {expected_name!r}")
    if fm.get("description") != "ok":
        errs.append(f"{path}: missing or empty description frontmatter")
    if "Iron Law" not in text and expected_name in ("investigate", "agent-loops"):
        # soft signal only for known iron-law skills — not a hard fail
        pass
    if len(text) < 200:
        errs.append(f"{path}: body suspiciously short ({len(text)} bytes)")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--installed",
        action="store_true",
        help="Also require skills under $GROK_HOME/skills (default ~/.grok/skills)",
    )
    ap.add_argument(
        "--grok-home",
        default=os.environ.get("GROK_HOME", str(Path.home() / ".grok")),
        help="Grok home for --installed checks",
    )
    args = ap.parse_args()
    root = repo_root()
    manifest_path = root / "bootstrap/grok-cli/manifest.json"
    skills_src = root / "bootstrap/grok-cli/skills"
    project_process = root / "bootstrap/project-process/skills/project-process/SKILL.md"

    errors: list[str] = []
    ok_lines: list[str] = []

    if not manifest_path.is_file():
        print(f"FAIL: no manifest at {manifest_path}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    listed = manifest.get("first_party_skills", {}).get("skills", [])
    listed_names = [s["name"] for s in listed if "name" in s]
    if not listed_names:
        errors.append("manifest first_party_skills.skills is empty")

    # Resolve source path per skill
    for name in listed_names:
        if name == "project-process":
            path = project_process
        else:
            path = skills_src / name / "SKILL.md"
        errs = check_skill_file(path, name)
        if errs:
            errors.extend(errs)
        else:
            ok_lines.append(f"  OK source {name}")

    # Orphan dirs under skills/ (have SKILL.md but not in manifest)
    if skills_src.is_dir():
        for d in sorted(skills_src.iterdir()):
            if not d.is_dir() or d.name.startswith("_"):
                continue
            skill_md = d / "SKILL.md"
            if skill_md.is_file() and d.name not in listed_names:
                errors.append(
                    f"orphan skill dir {d.relative_to(root)} not listed in manifest.json"
                )

    # Manifest entry without directory (except project-process)
    for name in listed_names:
        if name == "project-process":
            continue
        if not (skills_src / name).is_dir():
            errors.append(f"manifest lists {name} but no dir {skills_src / name}")

    if args.installed:
        dest = Path(args.grok_home) / "skills"
        for name in listed_names:
            path = dest / name / "SKILL.md"
            errs = check_skill_file(path, name)
            if errs:
                errors.extend([f"[installed] {e}" for e in errs])
            else:
                ok_lines.append(f"  OK installed {name}")

    print("==> verify_skills (first-party Grok skills)")
    print(f"    repo: {root}")
    print(f"    manifest skills: {len(listed_names)}")
    for line in ok_lines:
        print(line)

    if errors:
        print("FAIL:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: all first-party skill checks ok")
    if not args.installed:
        print("note: pass --installed (or make smoke-grok-skills INSTALLED=1) to check ~/.grok/skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
