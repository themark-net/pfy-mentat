"""Toolset x harness matrix, plan and apply (ADR-0017).

A toolset is declared once in ``data/toolsets.json`` and applied to any
harness in ``data/harnesses.json``. ``matrix()`` is the honest status grid;
``plan()`` turns one cell into a concrete apply plan (env dict, files to
write, MCP/config fragments, brief text) or an honest STUB / FAIL with a next
step; ``apply()`` writes a plan only with ``yes=True`` and only under
``$PFY_STATE_DIR`` or the harness's own config dir.

Reference toolset: **jev** (ADR-0016), implemented here by importing
``scripts/pfy_jev_230.py`` -- no decision logic is duplicated. The other
toolsets report the status their existing scripts earn today; porting their
``plan()`` bodies into this module is T-0121.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from . import _legacy, registry

STATUSES = registry.STATUSES
LANES = registry.LANES

MARK_BEGIN = "<!-- pfy-toolset:%s begin -->"
MARK_END = "<!-- pfy-toolset:%s end -->"

def harness_home(hid: str, root_dir: Path | None = None) -> Path | None:
    """Harness-native config dir from ``harnesses.json[].attach.config_dir``.

    Only these dirs, plus ``$PFY_STATE_DIR``, are writable by ``apply()``.
    """
    return registry.harness_home(hid, root_dir)


# ---------------------------------------------------------------- matrix ---

def matrix(root_dir: Path | None = None) -> list[dict]:
    """One row per toolset x harness cell: toolset, harness, status, how, lanes."""
    hids = registry.harness_ids(root_dir)
    rows: list[dict] = []
    for t in registry.toolset_rows(root_dir):
        impl = t.get("implementation") or {}
        for hid in hids:
            cell = impl.get(hid) or {}
            rows.append(
                {
                    "toolset": t.get("id"),
                    "harness": hid,
                    "status": cell.get("status") or "stub",
                    "how": cell.get("how") or "",
                    "lanes": list(t.get("lanes") or []),
                    "catalog_tool": t.get("catalog_tool"),
                }
            )
    return rows


def matrix_grid(root_dir: Path | None = None) -> tuple[list[str], list[list[str]]]:
    """(header, rows) for a compact table: toolset then one column per harness."""
    hids = registry.harness_ids(root_dir)
    header = ["TOOLSET"] + hids
    grid: list[list[str]] = []
    for t in registry.toolset_rows(root_dir):
        impl = t.get("implementation") or {}
        grid.append([str(t.get("id"))] + [str((impl.get(h) or {}).get("status") or "stub") for h in hids])
    return header, grid


def matrix_text(root_dir: Path | None = None) -> str:
    header, grid = matrix_grid(root_dir)
    widths = [max(len(str(r[i])) for r in [header] + grid) for i in range(len(header))]
    lines = ["  ".join(str(c).ljust(widths[i]) for i, c in enumerate(header))]
    lines.append("  ".join("-" * w for w in widths))
    for r in grid:
        lines.append("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))
    counts = {s: 0 for s in STATUSES}
    for row in matrix(root_dir):
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    lines.append("")
    lines.append(
        "cells: %d · implemented %d · partial %d · stub %d   (IMPLEMENTATION column, not live STATUS; ADR-0017)"
        % (sum(counts.values()), counts["implemented"], counts["partial"], counts["stub"])
    )
    return "\n".join(lines)


def cell(tid: str, hid: str, root_dir: Path | None = None) -> dict | None:
    t = registry.toolset(tid, root_dir)
    if t is None:
        return None
    return (t.get("implementation") or {}).get(hid)


# ------------------------------------------------------------------ plan ---

def _result(kind: str, tid: str, hid: str, lane: str | None, **extra) -> dict:
    out = {
        "ok": kind == "READY",
        "live": kind,
        "toolset": tid,
        "harness": hid,
        "lane": lane,
        "status": extra.pop("status", None),
        "env": {},
        "files": [],
        "mcp": [],
        "brief": "",
        "commands": [],
        "next_step": "",
        "copy": "",
    }
    out.update(extra)
    if not out["copy"]:
        tail = (" · " + out["next_step"]) if out["next_step"] else ""
        out["copy"] = "%s toolset %s → %s%s" % (kind, tid, hid, tail)
    return out


def plan(
    tid: str,
    hid: str,
    lane: str | None = None,
    *,
    root_dir: Path | None = None,
    state: Path | None = None,
) -> dict:
    """Concrete apply plan, or honest STUB / FAIL with next step. Never writes."""
    t = registry.toolset(tid, root_dir)
    if t is None:
        return _result(
            "FAIL", tid, hid, lane,
            error="unknown toolset %r" % tid,
            next_step="pick one of: %s" % ", ".join(registry.toolset_ids(root_dir)),
        )
    hids = registry.harness_ids(root_dir)
    if hid not in hids:
        return _result(
            "FAIL", tid, hid, lane,
            error="unknown harness %r" % hid,
            next_step="pick one of: %s" % ", ".join(hids),
        )
    lanes = list(t.get("lanes") or [])
    if lane is None:
        lane = "local" if "local" in lanes else lanes[0]
    if lane not in LANES:
        return _result("FAIL", tid, hid, lane, error="unknown lane %r" % lane, next_step="use --lane local|cloud")
    if lane not in lanes:
        return _result(
            "FAIL", tid, hid, lane,
            error="toolset %s has no %s lane" % (tid, lane),
            next_step="use --lane %s" % "|".join(lanes),
            status=(cell(tid, hid, root_dir) or {}).get("status"),
        )
    c = cell(tid, hid, root_dir) or {"status": "stub", "how": "stub: no cell"}
    status = c.get("status") or "stub"
    if status == "stub":
        return _result(
            "STUB", tid, hid, lane,
            status=status,
            how=c.get("how") or "",
            next_step=_stub_next(t, hid, root_dir),
        )
    if tid == "jev":
        return _plan_jev(t, hid, lane, status, root_dir=root_dir, state=state)
    # Not yet ported: report the status the existing script earns, do not fake a plan.
    prov = t.get("provides") or {}
    return _result(
        "STUB", tid, hid, lane,
        status=status,
        how=c.get("how") or "",
        ported=False,
        commands=list(prov.get("commands") or []),
        next_step="plan not ported to pfylib (T-0121) · today: %s · via %s"
        % (" | ".join(prov.get("commands") or []) or "n/a", t.get("source") or "?"),
        copy="STUB plan -- %s on %s is %s via %s; pfylib plan not ported (T-0121)"
        % (tid, hid, status, t.get("source") or "?"),
    )


def _stub_next(t: dict, hid: str, root_dir: Path | None) -> str:
    h = registry.harness(hid, root_dir) or {}
    issue = h.get("github_issue")
    bits = ["no config surface wired for %s" % hid]
    if issue:
        bits.append("harness adapter issue #%s" % issue)
    impl_h = [x for x in registry.harness_ids(root_dir) if ((t.get("implementation") or {}).get(x) or {}).get("status") == "implemented"]
    if impl_h:
        bits.append("implemented today on: %s" % ", ".join(impl_h))
    return " · ".join(bits)


# --------------------------------------------------------------- jev ref ---

def _jev_brief(jev, hid: str, lane: str, path: str, state: Path, gate: float) -> str:
    invoke = {
        "grok": "Grok: skill `pfy-jev-decision` is in `GROK_HOME/skills`; shell out to `./pfy decision …` for a typed Choice/Score.",
        "opencode": "OpenCode: this brief is listed under `instructions` in `$OPENCODE_CONFIG`; shell out to `./pfy decision …`.",
        "claude-code": "Claude Code: this brief is appended to `$PFY_ATTACH_AGENTS` and to `CLAUDE.md` under `CLAUDE_CONFIG_DIR`; shell out to `./pfy decision …`.",
        "codex": "Codex: this brief is appended to `$PFY_ATTACH_AGENTS` and to `AGENTS.md` under `CODEX_HOME`; shell out to `./pfy decision …`.",
        "hermes": "Hermes: read `$PFY_ATTACH_AGENTS` (env only; no hermes-native surface is written -- partial).",
    }.get(hid, "Read `$PFY_TOOLSET_BRIEF`.")
    lane_line = (
        "Lane **local**: engine `%s` (%s). No cloud call." % (path, jev.path_paint(path))
        if lane == "local"
        else "Lane **cloud**: TypeSafe `%s` at `%s` (key from TYPESAFE_API_KEY). Budgeted by `./pfy hedge`." % (jev.typesafe_model(), jev.TYPESAFE_URL)
    )
    lines = [
        "# Toolset: jev -- decision layer (typed Choice/Score)",
        "",
        "Applied by `./pfy toolset apply jev --harness %s --lane %s` (ADR-0017; decision semantics ADR-0016, #230)." % (hid, lane),
        "",
        "- %s" % jev.CHIP_DECISION,
        "- %s" % jev.CHIP_HONEST,
        "- %s" % jev.CHIP_CORE,
        "- Confidence is a **margin** chip (`%s` / `%s`), never percent-correct. Gate: %.2f -> below gate the layer FAILs and escalates; no silent auto-act." % (jev.CHIP_CONF_OK, jev.CHIP_CONF_LOW, gate),
        "- %s" % lane_line,
        "",
        "## Use in this session",
        "",
        "- `./pfy decision route`   -> Choice over live models/lane/harness/toolset (options rebuilt from live state).",
        "- `./pfy decision compact` -> keep|truncate|drop per stale tool result; user text is kept verbatim.",
        "- `./pfy decision queue put|next` -> local JSONL queue at `%s`." % (state / jev.QUEUE_FILE),
        "- State: `%s`." % (state / jev.STATE_FILE),
        "",
        "## Harness",
        "",
        invoke,
        "",
        "Do not paint Jev as chat. Do not equate decision with Gab `auto` or local recommend order.",
    ]
    return "\n".join(lines) + "\n"


def _jev_skill_md(brief: str) -> str:
    front = (
        "---\n"
        "name: pfy-jev-decision\n"
        "description: Use the pfy-mentat Jev-style decision layer (typed Choice/Score, margin confidence) via ./pfy decision. Applied by ./pfy toolset apply jev --harness grok (ADR-0017).\n"
        "---\n\n"
    )
    return front + brief


def _plan_jev(t: dict, hid: str, lane: str, status: str, *, root_dir: Path | None, state: Path | None) -> dict:
    jev = _legacy.jev(root_dir)
    st = registry.state_dir(state)
    gate = jev.conf_gate()
    if lane == "cloud":
        path = "typesafe"
        if not jev.typesafe_key():
            return _result(
                "FAIL", t["id"], hid, lane,
                status=status,
                error="TypeSafe key missing (cloud lane)",
                next_step=jev.NEXT_KEY + " · or --lane local",
            )
    else:
        path = jev.PRIMARY_LOCAL
    brief_path = st / str((t.get("provides") or {}).get("brief") or "toolset-jev-brief.md")
    brief = _jev_brief(jev, hid, lane, path, st, gate)
    env = {
        "PFY_DECISION_PATH": path,
        "PFY_DECISION_STATE": str(st / jev.STATE_FILE),
        "PFY_DECISION_QUEUE": str(st / jev.QUEUE_FILE),
        "PFY_JEV_CONF_GATE": "%.2f" % gate,
        "PFY_TOOLSET_BRIEF": str(brief_path),
    }
    files: list[dict] = [{"path": str(brief_path), "mode": "write", "content": brief}]
    agents = st / "attach-agents.md"
    if hid == "grok":
        home = harness_home("grok", root_dir)
        files.append({"path": str(home / "skills" / "pfy-jev-decision" / "SKILL.md"), "mode": "write", "content": _jev_skill_md(brief)})
    elif hid == "opencode":
        files.append({"path": str(st / "opencode.json"), "mode": "json-merge", "fragment": {"instructions": [str(brief_path)]}})
    elif hid == "claude-code":
        env["PFY_ATTACH_AGENTS"] = str(agents)
        files.append({"path": str(agents), "mode": "append-marker", "content": brief})
        files.append({"path": str(harness_home("claude-code", root_dir) / "CLAUDE.md"), "mode": "append-marker", "content": brief})
    elif hid == "codex":
        env["PFY_ATTACH_AGENTS"] = str(agents)
        files.append({"path": str(agents), "mode": "append-marker", "content": brief})
        files.append({"path": str(harness_home("codex", root_dir) / "AGENTS.md"), "mode": "append-marker", "content": brief})
    elif hid == "hermes":
        env["PFY_ATTACH_AGENTS"] = str(agents)
        files.append({"path": str(agents), "mode": "append-marker", "content": brief})
    commands = list((t.get("provides") or {}).get("commands") or [])
    note = "" if status == "implemented" else "partial: %s" % ((cell("jev", hid, root_dir) or {}).get("how") or "")
    return _result(
        "READY", t["id"], hid, lane,
        status=status,
        env=env,
        files=files,
        mcp=[],
        brief=brief,
        commands=commands,
        note=note,
        next_step="" if status == "implemented" else "hermes-native config surface unknown (partial)",
        copy="READY plan -- jev → %s (%s, %s) · %d file(s) · %d env" % (hid, lane, status, len(files), len(env)),
    )


# ----------------------------------------------------------------- apply ---

def _allowed_roots(hid: str, state: Path | None) -> list[Path]:
    roots = [registry.state_dir(state).resolve()]
    home = harness_home(hid)
    if home is not None:
        roots.append(home.expanduser().resolve())
    return roots


def _under(path: Path, roots: list[Path]) -> bool:
    p = path.expanduser().resolve()
    return any(p == r or r in p.parents for r in roots)


def _write_marker(path: Path, tid: str, content: str) -> str:
    begin, end = MARK_BEGIN % tid, MARK_END % tid
    block = "%s\n%s\n%s\n" % (begin, content.rstrip("\n"), end)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    if begin in existing and end in existing:
        head = existing.split(begin, 1)[0]
        tail = existing.split(end, 1)[1]
        new = head + block + tail.lstrip("\n")
        action = "replaced"
    else:
        new = (existing.rstrip("\n") + "\n\n" if existing.strip() else "") + block
        action = "appended"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")
    return action


def _merge_json(path: Path, fragment: dict) -> str:
    cfg: dict = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            cfg = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            return "FAIL: existing %s is not valid JSON" % path
    for key, val in fragment.items():
        if isinstance(val, list):
            cur = cfg.get(key) if isinstance(cfg.get(key), list) else []
            for item in val:
                if item not in cur:
                    cur.append(item)
            cfg[key] = cur
        elif isinstance(val, dict):
            cur = cfg.get(key) if isinstance(cfg.get(key), dict) else {}
            cur.update(val)
            cfg[key] = cur
        else:
            cfg[key] = val
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return "merged"


def apply(p: dict, *, yes: bool = False, state: Path | None = None) -> dict:
    """Write a plan's files. Without ``yes`` returns the plan marked dry_run."""
    out = dict(p)
    if not p.get("ok"):
        out["applied"] = []
        out["dry_run"] = not yes
        return out
    if not yes:
        out["dry_run"] = True
        out["applied"] = []
        out["copy"] = "DRY-RUN %s · pass --yes to write %d file(s)" % (p.get("copy", ""), len(p.get("files") or []))
        return out
    tid = str(p.get("toolset"))
    hid = str(p.get("harness"))
    roots = _allowed_roots(hid, state)
    applied: list[dict] = []
    failed: list[dict] = []
    for f in p.get("files") or []:
        path = Path(str(f.get("path")))
        if not _under(path, roots):
            failed.append({"path": str(path), "result": "refused: outside %s" % ", ".join(str(r) for r in roots)})
            continue
        mode = f.get("mode") or "write"
        try:
            if mode == "write":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(str(f.get("content") or ""), encoding="utf-8")
                res = "written"
            elif mode == "append-marker":
                res = _write_marker(path, tid, str(f.get("content") or ""))
            elif mode == "json-merge":
                res = _merge_json(path, dict(f.get("fragment") or {}))
            else:
                res = "FAIL: unknown mode %s" % mode
        except OSError as e:
            res = "FAIL: %s" % str(e)[:160]
        (failed if res.startswith("FAIL") else applied).append({"path": str(path), "result": res})
    out["applied"] = applied
    out["failed"] = failed
    out["dry_run"] = False
    if failed:
        out["ok"] = False
        out["live"] = "FAIL"
        out["copy"] = "FAIL apply -- %d of %d file(s) failed" % (len(failed), len(applied) + len(failed))
        out["next_step"] = failed[0]["result"]
    else:
        out["copy"] = "READY applied %s → %s · %d file(s)" % (tid, hid, len(applied))
    return out


def export_env_lines(p: dict) -> list[str]:
    return ["export %s=%s" % (k, json.dumps(str(v))) for k, v in sorted((p.get("env") or {}).items())]
