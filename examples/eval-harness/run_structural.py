#!/usr/bin/env python3
"""Tier S (structural): design/coding assist gates that never call an LLM.

Runs without Ollama/LiteLLM. Exit 0 only if all checks pass.

Checks:
  1. First-party Grok skills (verify_skills.py)
  2. Deterministic text scorers under tasks/*/score.py with fixtures/
  3. data/tools.json parses and has required schema fields
  4. Key design/coding skill SKILL.md files exist (agent-loops, investigate, one-shot, adr)
  5. Voice operator surface (install path files + VOICE_AUTO_AGENT mode map + 008/009)

Write summary to pipelines/eval/structural.latest.md when --write-md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = Path(__file__).resolve().parent
TASKS = HARNESS / "tasks"
VERIFY = ROOT / "bootstrap/grok-cli/scripts/verify_skills.py"
TOOLS_JSON = ROOT / "data/tools.json"
DESIGN_CODING_SKILLS = (
    "agent-loops",
    "investigate",
    "one-shot",
    "adr",
    "hermes-feedback",
    "docs",
    "open-questions",
)


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def check_skills() -> tuple[bool, str]:
    if not VERIFY.is_file():
        return False, "verify_skills.py missing"
    code, out = run([sys.executable, str(VERIFY)])
    lines = [ln for ln in out.splitlines() if ln.strip()]
    summary = next((ln for ln in lines if ln.startswith("PASS") or ln.startswith("FAIL")), lines[-1] if lines else f"exit {code}")
    return code == 0, summary


def check_tools_json() -> tuple[bool, str]:
    try:
        data = json.loads(TOOLS_JSON.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return False, f"parse error: {e}"
    tools = data.get("tools")
    if not isinstance(tools, list) or not tools:
        return False, "tools[] empty or missing"
    required = {"name", "primary_category", "github", "scores", "tier"}
    bad = []
    for t in tools:
        missing = required - set(t.keys())
        if missing:
            bad.append(f"{t.get('name', '?')}: missing {sorted(missing)}")
            continue
        sc = t["scores"]
        for k in ("s1", "s2", "s3", "s4", "overall"):
            if k not in sc:
                bad.append(f"{t['name']}: scores.{k}")
    if bad:
        return False, "; ".join(bad[:5])
    return True, f"ok n={len(tools)} version={data.get('version')}"


def check_design_skill_files() -> tuple[bool, str]:
    missing = []
    base = ROOT / "bootstrap/grok-cli/skills"
    for name in DESIGN_CODING_SKILLS:
        if name == "project-process":
            p = ROOT / "bootstrap/project-process/skills/project-process/SKILL.md"
        else:
            p = base / name / "SKILL.md"
        if not p.is_file():
            missing.append(name)
    if missing:
        return False, f"missing SKILL.md: {missing}"
    return True, f"ok {len(DESIGN_CODING_SKILLS)} design/coding skills"


def check_text_scorers() -> tuple[bool, str]:
    """For each tasks/*/score.py, run fixtures/pass* (expect 0) and fixtures/fail* (expect 1)."""
    reports: list[str] = []
    any_scorer = False
    for task_dir in sorted(TASKS.iterdir()):
        if not task_dir.is_dir():
            continue
        scorer = task_dir / "score.py"
        if not scorer.is_file():
            continue
        any_scorer = True
        fixtures = task_dir / "fixtures"
        if not fixtures.is_dir():
            reports.append(f"{task_dir.name}: no fixtures/")
            continue
        passes = list(fixtures.glob("pass*"))
        fails = list(fixtures.glob("fail*"))
        if not passes or not fails:
            reports.append(f"{task_dir.name}: need pass* and fail* fixtures")
            continue
        for f in passes:
            code, out = run([sys.executable, str(scorer), str(f)])
            if code != 0:
                reports.append(f"{task_dir.name}/{f.name}: expected PASS got {code} {out.strip()}")
        for f in fails:
            code, out = run([sys.executable, str(scorer), str(f)])
            if code == 0:
                reports.append(f"{task_dir.name}/{f.name}: expected FAIL got 0 {out.strip()}")
    if not any_scorer:
        return False, "no tasks/*/score.py found"
    if reports:
        return False, "; ".join(reports[:8])
    return True, "ok all text scorer fixtures"


def check_voice_operator_surface() -> tuple[bool, str]:
    """Installable voice path files + mode map contract (ADR-0012 / T-0092)."""
    edge = ROOT / "examples" / "voice-stt-edge"
    required = [
        edge / "install-voice-agent.sh",
        edge / "agent_runner.py",
        edge / "voice-repl.sh",
        edge / "e2e-develop-loop.sh",
        edge / "ci-optional-local-long-task.sh",
        edge / "remote_server.py",
        ROOT / "make" / "voice.mk",
        ROOT / "docs" / "ops" / "voice-agent-install.md",
        TASKS / "008-voice-receipt" / "score.py",
        TASKS / "009-voice-last-run" / "score.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.is_file()]
    if missing:
        return False, f"missing: {missing[:5]}"
    # Mode map: VOICE_AUTO_AGENT=1 → opencode (not grok)
    code, out = run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.util; from pathlib import Path; "
                "p=Path('examples/voice-stt-edge/agent_runner.py'); "
                "s=importlib.util.spec_from_file_location('ar', p); "
                "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
                "assert m.normalize_mode('1')=='opencode'; "
                "assert m.normalize_mode('on')=='opencode'; "
                "assert m.normalize_mode('auto')=='opencode'; "
                "assert m.normalize_mode('grok')=='grok'; "
                "assert m.normalize_mode('recipe')=='recipe'; "
                "assert m.normalize_mode('0')=='off'; "
                "print('mode-map-ok')"
            ),
        ]
    )
    if code != 0 or "mode-map-ok" not in out:
        return False, f"mode map failed: {out.strip()[:200]}"
    mk = (ROOT / "Makefile").read_text(encoding="utf-8")
    if "include make/voice.mk" not in mk and "include make/voice.mk".replace(" ", "") not in mk.replace(
        " ", ""
    ):
        # tolerate tab/spacing variants
        if "voice.mk" not in mk:
            return False, "Makefile does not include make/voice.mk"
    return True, "ok install path + mode map + 008/009 scorers"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write-md", type=Path, default=None)
    args = ap.parse_args()

    checks = [
        ("skills_manifest", check_skills),
        ("tools_json_schema", check_tools_json),
        ("design_coding_skills", check_design_skill_files),
        ("text_scorer_fixtures", check_text_scorers),
        ("voice_operator_surface", check_voice_operator_surface),
    ]
    rows: list[tuple[str, bool, str]] = []
    for name, fn in checks:
        ok, detail = fn()
        rows.append((name, ok, detail))
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {detail}", flush=True)

    all_ok = all(ok for _, ok, _ in rows)
    print(f"\nSTRUCTURAL EVAL: {'PASS' if all_ok else 'FAIL'}", flush=True)

    if args.write_md:
        args.write_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# Structural eval (design/coding) — {datetime.now(timezone.utc).isoformat()}",
            "",
            "| Check | Result | Detail |",
            "|-------|--------|--------|",
        ]
        for name, ok, detail in rows:
            lines.append(f"| `{name}` | {'PASS' if ok else 'FAIL'} | {detail.replace('|', '/')} |")
        lines.append("")
        lines.append(f"**Overall:** {'PASS' if all_ok else 'FAIL'} (no LLM required)")
        lines.append("")
        args.write_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {args.write_md}", flush=True)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
