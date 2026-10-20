#!/usr/bin/env python3
"""Choice-set adapter. Same seam as upstream DemoAdapter, OpenCode workspace_config.

The adapter never sees gold labels. ``drive.py`` strips cases on the host and
hands this module only opaque batches. Executors and editors both go through
``sbun`` (``config.BUN``), which is the item 2 sandbox.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_H2_ENV = os.environ.get("HARNESS2_W")
_H2_ROOT = (
    Path(_H2_ENV) / "tmp" / "harness2"
    if _H2_ENV
    else Path(__file__).resolve().parents[2] / "tmp" / "harness2"
)
if str(_H2_ROOT) not in sys.path:
    sys.path.insert(0, str(_H2_ROOT))

from harness2.core.spec import BenchPrompts, BenchSpec, ChannelSpec
from harness2.substrate.opencode import OpencodeSubstrate

INSTALL_MODE = "workspace_config"
# Parallel recursion labels finals agg1..aggk. c1..ck belong to sequential mode.
EXEC_TIMEOUT = "900"

_BASE = {
    "systemprompt.md": (
        "Read cases.json in this workspace.\n"
        "Each case has an id, instructions, a state, and criteria.\n"
        "Pick exactly one criteria key for each case.\n"
        "Write output/answer.json and nothing else, in this shape:\n"
        '{"answers":[{"case":"<id>","choice":"<criteria key>","confidence":0.0,"why":"one short reason"}]}\n'
        "Use a confidence below 0.85 when the state does not settle the choice.\n"
    ),
    "guardrails.md": (
        "Do not invent a criteria key.\n"
        "Do not place a case id next to the chosen key in the why field.\n"
    ),
    "LongTermMEMORY.md": (
        "The confidence gate used by the operator is 0.85.\n"
        "Below that gate, the why should say the state is unsettled.\n"
    ),
    "tool_descriptions/tool_guidance.md": (
        "Read cases.json. Write only output/answer.json.\n"
        "A helper script is optional. The answer file is required.\n"
    ),
}

_TOOL_GATE = {
    "agent": {"build": {"steps": 40}},
    "tools": {"read": True, "bash": True, "edit": True, "write": True},
    "permission": {
        "read": "allow",
        "bash": "allow",
        "edit": "allow",
        "write": "allow",
    },
}


def _surface_base(dest: Path) -> bool:
    """Item 4 owns the mapped tree. Until ``surface.write_base`` exists, use _BASE."""
    path = Path(__file__).with_name("surface.py")
    if not path.is_file():
        return False
    import importlib.util

    spec = importlib.util.spec_from_file_location("h2surface", path)
    if spec is None or spec.loader is None:
        return False
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    writer = getattr(mod, "write_base", None)
    if not callable(writer):
        return False
    writer(dest)
    return True


class PfyAdapter:
    def __init__(
        self,
        *,
        batches: dict[str, list[dict]],
        train_ids: list[str],
        runs: Path,
        model: str,
        editor_timeout: int = 900,
    ):
        self.batches = batches
        self.train_ids = list(train_ids)
        self.runs = Path(runs)
        self.model = model
        self.editor_timeout = int(editor_timeout)
        self.substrate = OpencodeSubstrate(self._launch)
        self.spec = BenchSpec(
            name="pfy-decisions",
            runs_root=self.runs,
            install_mode=INSTALL_MODE,
            prompts=BenchPrompts(
                work="Choose one allowed action for each case and write the answers as JSON.",
                domain_word="decision",
                deliverable_word="answer file",
            ),
            channels={
                "proposer": ChannelSpec(
                    "opencode", model, effort="high", steps=40, timeout=self.editor_timeout
                ),
                "selector": ChannelSpec(
                    "opencode", model, effort="high", steps=40, timeout=self.editor_timeout
                ),
            },
            leak_globs=(
                "laya-trial.cases.v0.json",
                "id-map.json",
                "gold-labels.json",
            ),
        )
        self._exec_root = self.runs / "executions"
        self._src_root = self.runs / "sources"
        self.base_dir = self.runs / "base-harness"
        self._write_base()

    def _write_base(self) -> None:
        dest = self.base_dir
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        if _surface_base(dest):
            return
        for rel, body in _BASE.items():
            path = dest / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

    def tasks(self, split: str = "all") -> list[str]:
        return list(self.train_ids)

    def domain_of(self, task_id: str) -> str:
        return "pfy-decisions"

    def task_prompt(self, task_id: str) -> str:
        rows = self.batches.get(task_id) or []
        ids = ", ".join(str(row["id"]) for row in rows)
        return (
            "Choose one criteria key for each case in the source file.\n"
            f"Cases: {ids}\n"
            "Write the answers as JSON in the workspace output.\n"
        )

    def task_files(self, task_id: str) -> Path | None:
        """Train source only. Held-out batches are not written under the training runs dir."""
        if task_id not in self.train_ids:
            return None
        dest = self._src_root / task_id
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "cases.json").write_text(
            json.dumps(self.batches[task_id], ensure_ascii=False),
            encoding="utf-8",
        )
        return dest

    def base_harness(self) -> Path:
        return self.base_dir

    def validate_tree(self, tree: dict) -> None:
        if "systemprompt.md" not in tree:
            raise ValueError("systemprompt.md is required")

    def execute(
        self, task_id: str, harness_dir: Path | None, run_id: str, *, timeout: int | None = None
    ) -> Path:
        run_dir = self._run_dir(run_id)
        if (run_dir / "output" / "answer.json").is_file():
            return run_dir
        held = os.environ.get("HARNESS2_EXEC_HELDOUT")
        previous = tempfile.tempdir
        if held:
            tmp = Path(os.environ.get("HARNESS2_W", Path(__file__).resolve().parents[2])) / "tmp" / "heldout-runs" / held / "tmp"
            # worktree() is not imported here; HARNESS2_W is exported by env.sh and by drive.
            if "HARNESS2_HELDOUT_ROOT" in os.environ:
                tmp = Path(os.environ["HARNESS2_HELDOUT_ROOT"]) / held / "tmp"
            tmp.mkdir(parents=True, exist_ok=True)
            tempfile.tempdir = str(tmp)
        try:
            source = harness_dir or self.base_harness()
            install = self.substrate.materialise(Path(source), self.spec, {})
            try:
                self._stage_workspace(install.staging_dir, task_id)
                self.substrate.execute(task_id, install, [run_id], int(timeout or int(EXEC_TIMEOUT)))
            finally:
                shutil.rmtree(install.staging_dir, ignore_errors=True)
        finally:
            tempfile.tempdir = previous
        return run_dir

    def _stage_workspace(self, workspace: Path, task_id: str) -> None:
        rows = self.batches.get(task_id) or []
        (workspace / "cases.json").write_text(
            json.dumps(rows, ensure_ascii=False), encoding="utf-8"
        )
        parts = []
        for rel in ("systemprompt.md", "guardrails.md", "LongTermMEMORY.md", "tool_descriptions/tool_guidance.md"):
            path = workspace / rel
            if path.is_file():
                parts.append(path.read_text(encoding="utf-8"))
        (workspace / "composition.md").write_text("\n\n".join(parts), encoding="utf-8")
        (workspace / "ENV_DELTA").write_text("temperature=0\nseed=230\n", encoding="utf-8")
        (workspace / "opencode.json").write_text(
            json.dumps(_TOOL_GATE, indent=2) + "\n", encoding="utf-8"
        )

    def _launch(self, req, install) -> list[Path]:
        workspace = Path(install.staging_dir)
        run_id = req.run_ids[0]
        label = run_id.split("__")[-1]
        prompt = (
            "Read systemprompt.md first and follow it exactly, including the answer file shape. "
            "Then read cases.json and write the answer file it names."
        )
        argv = self.substrate.run_argv(
            prompt, workspace, self.model, title=label or "adapt"
        )
        env = self.substrate.run_env(os.environ.copy(), workspace)
        # Upstream Proposer sets these inside the writable workspace
        # (proposer.py). The state dir is read-only inside the sandbox.
        env["XDG_DATA_HOME"] = str(workspace / ".ocdata")
        env["XDG_STATE_HOME"] = str(workspace / ".ocstate")
        held = os.environ.get("HARNESS2_EXEC_HELDOUT")
        if held:
            env["HARNESS2_HELDOUT"] = held
            env.pop("HARNESS2_RUNS_DIR", None)
        timeout_s = os.environ.get("HARNESS2_EXEC_TIMEOUT", EXEC_TIMEOUT)
        cmd = ["timeout", str(timeout_s), *argv]
        proc = subprocess.run(
            cmd,
            cwd=str(workspace),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=int(timeout_s) + 60,
            check=False,
        )
        run_dir = self._run_dir(run_id)
        out = run_dir / "output"
        out.mkdir(parents=True, exist_ok=True)
        (run_dir / "session.jsonl").write_text(proc.stdout or "", encoding="utf-8")
        (run_dir / "executor.stderr").write_text(proc.stderr or "", encoding="utf-8")
        staged_cases = workspace / "cases.json"
        if staged_cases.is_file():
            shutil.copy2(staged_cases, run_dir / "cases.json")
        answer = workspace / "output" / "answer.json"
        if answer.is_file():
            shutil.copy2(answer, out / "answer.json")
        else:
            # A models.dev failure exits 0 with no POST and no answer. That is
            # not a scored run.
            raise RuntimeError(
                f"executor rc={proc.returncode} produced no answer.json: "
                f"{(proc.stderr or '')[-300:]}"
            )
        return [run_dir]

    def _run_dir(self, run_id: str) -> Path:
        held = os.environ.get("HARNESS2_EXEC_HELDOUT")
        if held and "HARNESS2_HELDOUT_ROOT" in os.environ:
            root = Path(os.environ["HARNESS2_HELDOUT_ROOT"]) / held / "executions"
        else:
            root = self._exec_root
        path = root / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def delivered(self, run_dir: Path) -> bool:
        return (Path(run_dir) / "output" / "answer.json").is_file()

    def trajectory(self, run_dir: Path, *, obs_trunc: int) -> str:
        stream = Path(run_dir) / "session.jsonl"
        if stream.is_file() and stream.stat().st_size:
            return self.substrate.read_trajectory(
                stream, obs_trunc=obs_trunc, max_chars=obs_trunc
            )
        if self.delivered(run_dir):
            return "[ACTION] Write output/answer.json\n[OBSERVATION]\nanswer file present\n"
        return "[ERROR] no answer file\n"

    def deliverable_text(self, run_dir: Path) -> str:
        path = Path(run_dir) / "output" / "answer.json"
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def deliverable_files(self, run_dir: Path) -> dict[str, str]:
        text = self.deliverable_text(run_dir)
        return {"answer.json": text} if text else {}

    def tree_sha(self, tree: dict) -> str:
        import hashlib

        blob = json.dumps(tree, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()


def read_answers(run_dir: Path) -> list[dict]:
    path = Path(run_dir) / "output" / "answer.json"
    if not path.is_file():
        return []
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    rows = obj.get("answers") if isinstance(obj, dict) else None
    return rows if isinstance(rows, list) else []
