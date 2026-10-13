"""Phase 1 behavior for issue #290 (docs/design/pfy-launcher.md §13).

Temp HOME, fake harness dirs, fake npx. No network. These fail while the
install script, catalog v2 rows, or setup engine are absent.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "pfy"
INSTALL = ROOT / "install.sh"
SOT = ROOT / "bootstrap" / "grok-cli" / "skills"
TAG = "v0.4.17"
ONE_LINER = "https://raw.githubusercontent.com/themark-net/pfy-mentat/v0.4.17/install.sh"
SETUP_ARGV = [
    "-y",
    "rea-agents@6.4.0",
    "setup",
    "--client",
    "grok_build",
    "--client",
    "claude_code",
    "--client",
    "codex",
    "--client",
    "opencode",
    "--yes",
    "--json",
]
HARNESSES = ("grok", "claude-code", "codex", "opencode")
ITEMS = ("core-skills", "code-graph", "rea")

GROK_TOML = (
    "# user comment stays\n"
    "[mcp_servers.other]\n"
    'command = "keep-me"\n'
)
CODEX_TOML = (
    "# codex comment stays\n"
    "[mcp_servers.other]\n"
    'command = "keep-me"\n'
)
CLAUDE_JSON = (
    "{\n"
    '  "mcpServers": {\n'
    '    "other": {\n'
    '      "command": "keep-me"\n'
    "    }\n"
    "  }\n"
    "}\n"
)
OPENCODE_JSON = (
    "{\n"
    '  "mcp": {\n'
    '    "other": {\n'
    '      "command": "keep-me"\n'
    "    }\n"
    "  }\n"
    "}\n"
)


def _sha(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_exe(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class _Home(unittest.TestCase):
    def setUp(self):
        self.home = Path(self._mkdtemp())
        self.addCleanup(shutil.rmtree, self.home, ignore_errors=True)
        self.npx_log = self.home / "npx.log"
        bindir = self.home / "bin"
        _write_exe(
            bindir / "npx",
            "#!/usr/bin/env python3\n"
            "import json, os, sys\n"
            "p = os.environ['NPX_LOG']\n"
            "with open(p, 'a', encoding='utf-8') as f:\n"
            "    f.write(json.dumps(sys.argv[1:]) + '\\n')\n",
        )

    def _mkdtemp(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="pfy-launcher-p1-")

    def env(self, **extra: str) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["NPX_LOG"] = str(self.npx_log)
        env["PATH"] = str(self.home / "bin") + os.pathsep + env.get("PATH", "")
        env["XDG_CONFIG_HOME"] = str(self.home / ".config")
        env["XDG_STATE_HOME"] = str(self.home / ".local" / "state")
        env["PFY_ROOT"] = str(ROOT)
        for key in (
            "PFY_ALLOW_ROOT",
            "PFY_INSTALL_SOURCE",
            "GROK_HOME",
            "CLAUDE_CONFIG_DIR",
            "CODEX_HOME",
            "OPENCODE_CONFIG",
            "OPENCODE_CONFIG_DIR",
            "PFY_STATE_DIR",
        ):
            env.pop(key, None)
        env.update(extra)
        return env

    def seed_harnesses(self) -> dict[Path, bytes]:
        grok = self.home / ".grok" / "config.toml"
        claude = self.home / ".claude.json"
        codex = self.home / ".codex" / "config.toml"
        opencode = self.home / ".config" / "opencode" / "opencode.json"
        (self.home / ".claude").mkdir()
        grok.parent.mkdir(parents=True)
        codex.parent.mkdir(parents=True)
        opencode.parent.mkdir(parents=True)
        grok.write_text(GROK_TOML)
        claude.write_text(CLAUDE_JSON)
        codex.write_text(CODEX_TOML)
        opencode.write_text(OPENCODE_JSON)
        return {grok: GROK_TOML.encode(), claude: CLAUDE_JSON.encode(), codex: CODEX_TOML.encode(), opencode: OPENCODE_JSON.encode()}

    def tracked(self) -> list[Path]:
        home = self.home
        return [
            home / ".grok" / "config.toml",
            home / ".grok" / "config.toml.pfy.backup",
            home / ".claude.json",
            home / ".claude.json.pfy.backup",
            home / ".codex" / "config.toml",
            home / ".codex" / "config.toml.pfy.backup",
            home / ".config" / "opencode" / "opencode.json",
            home / ".config" / "opencode" / "opencode.json.pfy.backup",
            home / ".local" / "state" / "pfy" / "installed.json",
        ]

    def snap(self) -> dict[str, str | None]:
        return {str(p): _sha(p) for p in self.tracked()}

    def run_pfy(self, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(PFY), *args],
            cwd=str(ROOT),
            env=self.env(**extra),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def npx_calls(self) -> list[list[str]]:
        if not self.npx_log.is_file():
            return []
        return [json.loads(line) for line in self.npx_log.read_text().splitlines() if line.strip()]


def _toolsets() -> dict:
    return json.loads((ROOT / "data" / "toolsets.json").read_text())


def _by_id() -> dict[str, dict]:
    return {t["id"]: t for t in _toolsets()["toolsets"]}


class InstallTests(_Home):
    def test_dry_run_leaves_home_empty_and_pins_tag(self):
        text = INSTALL.read_text()
        self.assertIn(ONE_LINER, text)
        self.assertNotIn("pfy-mentat/main/", text)
        self.assertIn("\n{", text)
        self.assertTrue(text.rstrip().endswith("}"))
        proc = subprocess.run(
            ["bash", str(INSTALL), "--dry-run"],
            cwd=str(self.home),
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=15,
        )
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertIn(TAG, blob)
        self.assertIn("dry_run: true", blob)
        self.assertIn("git clone", blob)
        self.assertIn("--branch " + TAG, blob)
        self.assertIn(".local/bin/pfy", blob)
        self.assertNotIn("pfy-mentat/main/", blob)
        self.assertEqual(list(self.home.iterdir()), [self.home / "bin"])

    def test_version_prints_tag(self):
        proc = subprocess.run(
            ["bash", str(INSTALL), "--version"],
            cwd=str(self.home),
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(TAG, proc.stdout)
        self.assertNotIn("main", proc.stdout)

    def test_root_dry_run_exits_1(self):
        _write_exe(self.home / "bin" / "id", "#!/bin/sh\necho 0\n")
        proc = subprocess.run(
            ["bash", str(INSTALL), "--dry-run"],
            cwd=str(self.home),
            env=self.env(),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertFalse((self.home / ".local").exists())

    def test_root_allowed_with_flag(self):
        _write_exe(self.home / "bin" / "id", "#!/bin/sh\necho 0\n")
        proc = subprocess.run(
            ["bash", str(INSTALL), "--dry-run"],
            cwd=str(self.home),
            env=self.env(PFY_ALLOW_ROOT="1"),
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("dry_run: true", proc.stdout + proc.stderr)
        self.assertFalse((self.home / ".local").exists())


class CatalogTests(unittest.TestCase):
    def test_v2_items_schema_and_preset(self):
        schema = json.loads((ROOT / "data" / "schema" / "catalog-item.v2.json").read_text())
        self.assertIn("kind", json.dumps(schema))
        rows = _by_id()
        for iid in ITEMS:
            self.assertIn(iid, rows)
            item = rows[iid]
            self.assertIn(item["kind"], ("skill", "mcp", "external", "env", "bundle"))
            self.assertEqual(item["install"]["strategy"] in ("native", "delegate"), True)
            self.assertEqual(item["secrets"], [])
            self.assertIn("core", item["presets"])
        self.assertEqual(rows["core-skills"]["kind"], "bundle")
        self.assertEqual(rows["core-skills"]["install"]["strategy"], "native")
        self.assertEqual(rows["code-graph"]["kind"], "mcp")
        self.assertEqual(rows["code-graph"]["install"]["strategy"], "native")
        mcp = rows["code-graph"]["provides"]["mcp"]
        self.assertEqual(mcp[0]["name"], "code-graph")
        self.assertEqual(mcp[0]["command"], "codebase-memory-mcp")
        names = [s["name"] for s in rows["core-skills"]["provides"]["skills"]]
        expected = sorted(p.name for p in SOT.iterdir() if (p / "SKILL.md").is_file())
        self.assertEqual(sorted(names), expected)
        self.assertIn("adr", names)
        self.assertIn("investigate", names)
        rea = rows["rea"]
        self.assertEqual(rea["kind"], "external")
        self.assertEqual(rea["install"]["strategy"], "delegate")
        cmd = rea["install"]["delegate"]["cmd"]
        self.assertIn("rea-agents@6.4.0", cmd)
        self.assertIn("setup", cmd)
        cmap = rea["install"]["delegate"]["client_map"]
        self.assertEqual(cmap["grok"], "grok_build")
        self.assertEqual(cmap["claude-code"], "claude_code")
        self.assertEqual(cmap["codex"], "codex")
        self.assertEqual(cmap["opencode"], "opencode")
        self.assertIn("uninstall", rea["install"]["uninstall"]["cmd"])
        self.assertTrue(any("rea-agents@6.4.0" in str(x) for x in rea["install"]["uninstall"]["cmd"]))
        core_ids = sorted(i for i, t in rows.items() if "core" in (t.get("presets") or []))
        self.assertEqual(core_ids, ["code-graph", "core-skills", "rea"])
        self.assertIsNone(rows["core-skills"]["catalog_tool"])
        self.assertIsNone(rows["rea"]["catalog_tool"])
        self.assertEqual(rows["code-graph"]["catalog_tool"], "codebase-memory-mcp")

    def test_validate_script(self):
        proc = subprocess.run(
            ["python3", str(ROOT / "scripts" / "catalog_item_validate.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class SetupTests(_Home):
    def test_needs_confirmation_writes_nothing(self):
        originals = self.seed_harnesses()
        proc = self.run_pfy("setup", "--preset", "core", "--harness", "grok", "--harness", "claude-code", "--harness", "codex", "--harness", "opencode")
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, blob)
        self.assertIn("needs_confirmation", blob)
        self.assertNotIn("profile=", blob)
        for path, raw in originals.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(self.npx_calls(), [])
        self.assertFalse((self.home / ".grok" / "config.toml.pfy.backup").exists())

    def test_bare_yes_does_not_select_new_harnesses(self):
        originals = self.seed_harnesses()
        proc = self.run_pfy("setup", "--yes")
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertNotIn("profile=", blob)
        for path, raw in originals.items():
            self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(self.npx_calls(), [])

    def _apply(self) -> subprocess.CompletedProcess[str]:
        return self.run_pfy(
            "setup",
            "--preset",
            "core",
            "--yes",
            "--harness",
            "grok",
            "--harness",
            "claude-code",
            "--harness",
            "codex",
            "--harness",
            "opencode",
        )

    def test_setup_writes_four_harnesses_and_npx_once(self):
        originals = self.seed_harnesses()
        proc = self._apply()
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertNotIn("profile=", blob)
        grok = (self.home / ".grok" / "config.toml").read_text()
        codex = (self.home / ".codex" / "config.toml").read_text()
        self.assertIn(GROK_TOML, grok)
        self.assertIn("# user comment stays", grok)
        self.assertIn("managed-by: pfy item=code-graph", grok)
        self.assertIn("codebase-memory-mcp", grok)
        self.assertIn(CODEX_TOML, codex)
        self.assertIn("# codex comment stays", codex)
        claude = json.loads((self.home / ".claude.json").read_text())
        self.assertEqual(claude["mcpServers"]["other"]["command"], "keep-me")
        entry = claude["mcpServers"]["code-graph"]
        self.assertEqual(entry["command"], "codebase-memory-mcp")
        self.assertEqual(entry["_pfy"]["owner"], "pfy")
        self.assertEqual(entry["_pfy"]["item"], "code-graph")
        opened = json.loads((self.home / ".config" / "opencode" / "opencode.json").read_text())
        self.assertEqual(opened["mcp"]["other"]["command"], "keep-me")
        self.assertEqual(opened["mcp"]["code-graph"]["command"], "codebase-memory-mcp")
        names = [s["name"] for s in _by_id()["core-skills"]["provides"]["skills"]]
        for name in names:
            src = SOT / name / "SKILL.md"
            for dest_root in (
                self.home / ".grok" / "skills",
                self.home / ".claude" / "skills",
                self.home / ".agents" / "skills",
            ):
                dest = dest_root / name
                self.assertTrue((dest / ".pfy-owned").is_file(), dest)
                self.assertEqual((dest / "SKILL.md").read_bytes(), src.read_bytes())
        nested = SOT / "marketing-council" / "references" / "advisors" / "seth-godin.md"
        copied = self.home / ".grok" / "skills" / "marketing-council" / "references" / "advisors" / "seth-godin.md"
        self.assertEqual(copied.read_bytes(), nested.read_bytes())
        for path in originals:
            backup = Path(str(path) + ".pfy.backup")
            self.assertTrue(backup.is_file(), backup)
            self.assertEqual(backup.read_bytes(), originals[path])
        setups = [c for c in self.npx_calls() if "setup" in c]
        self.assertEqual(setups, [SETUP_ARGV])

    def test_second_run_zero_writes(self):
        originals = self.seed_harnesses()
        first = self._apply()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        before = {str(p): p.read_bytes() for p in self.tracked() if p.exists()}
        second = self._apply()
        blob = second.stdout + second.stderr
        self.assertEqual(second.returncode, 0, blob)
        self.assertIn("0 writes", blob)
        after = {str(p): p.read_bytes() for p in self.tracked() if p.exists()}
        self.assertEqual(before, after)
        for path, raw in originals.items():
            self.assertEqual(Path(str(path) + ".pfy.backup").read_bytes(), raw)
        setups = [c for c in self.npx_calls() if "setup" in c]
        self.assertEqual(setups, [SETUP_ARGV])

    def test_malformed_claude_json_aborts_before_any_write(self):
        originals = self.seed_harnesses()
        claude = self.home / ".claude.json"
        claude.write_text("{")
        before = {p: p.read_bytes() for p in originals}
        before[claude] = b"{"
        proc = self._apply()
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, blob)
        self.assertIn(str(claude), blob)
        self.assertIn("next", blob.lower())
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw, path)
        self.assertFalse((self.home / ".grok" / "config.toml.pfy.backup").exists())
        self.assertFalse((self.home / ".grok" / "skills").exists())
        self.assertEqual(self.npx_calls(), [])

    def test_uninstall_restores_originals_and_calls_rea(self):
        originals = self.seed_harnesses()
        applied = self._apply()
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        held = self.run_pfy("uninstall")
        held_blob = held.stdout + held.stderr
        self.assertEqual(held.returncode, 1, held_blob)
        self.assertIn("needs_confirmation", held_blob)
        self.assertIn("code-graph", (self.home / ".grok" / "config.toml").read_text())
        proc = self.run_pfy("uninstall", "--yes")
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        for path, raw in originals.items():
            self.assertEqual(path.read_bytes(), raw, path)
            self.assertEqual(Path(str(path) + ".pfy.backup").read_bytes(), raw)
        self.assertFalse((self.home / ".grok" / "skills" / "adr").exists())
        self.assertFalse((self.home / ".claude" / "skills" / "adr").exists())
        self.assertFalse((self.home / ".agents" / "skills" / "adr").exists())
        uninstalls = [c for c in self.npx_calls() if "uninstall" in c]
        self.assertEqual(len(uninstalls), 1)
        self.assertIn("rea-agents@6.4.0", uninstalls[0])
        self.assertIn("uninstall", uninstalls[0])

    def test_uninstall_leaves_edited_entry(self):
        originals = self.seed_harnesses()
        applied = self._apply()
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        grok = self.home / ".grok" / "config.toml"
        grok.write_text(grok.read_text().replace("codebase-memory-mcp", "user-edited-cmd"))
        proc = self.run_pfy("uninstall", "--yes")
        blob = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, blob)
        self.assertIn("warn", blob.lower())
        self.assertIn("user-edited-cmd", grok.read_text())
        self.assertEqual((self.home / ".claude.json").read_bytes(), originals[self.home / ".claude.json"])
        self.assertEqual((self.home / ".codex" / "config.toml").read_bytes(), originals[self.home / ".codex" / "config.toml"])
        self.assertEqual(
            (self.home / ".config" / "opencode" / "opencode.json").read_bytes(),
            originals[self.home / ".config" / "opencode" / "opencode.json"],
        )
        uninstalls = [c for c in self.npx_calls() if "uninstall" in c]
        self.assertEqual(len(uninstalls), 1)

    def test_doctor_json_readonly_aligned_missing_drifted(self):
        self.seed_harnesses()
        applied = self._apply()
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)

        def states(proc: subprocess.CompletedProcess[str]) -> dict[tuple[str, str], str]:
            blob = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 0, blob)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertIsInstance(payload["plan"], list)
            rows = payload["doctor"]
            self.assertIsInstance(rows, list)
            return {(r["harness"], r["item"]): r["state"] for r in rows}

        before = self.snap()
        got = states(self.run_pfy("doctor", "--json"))
        for harness in HARNESSES:
            for item in ITEMS:
                self.assertEqual(got[(harness, item)], "aligned", (harness, item, got))
        self.assertEqual(self.snap(), before)

        shutil.rmtree(self.home / ".grok" / "skills" / "adr")
        after_delete = self.snap()
        got = states(self.run_pfy("doctor", "--json"))
        self.assertEqual(got[("grok", "core-skills")], "missing")
        self.assertEqual(got[("claude-code", "core-skills")], "aligned")
        self.assertEqual(got[("grok", "code-graph")], "aligned")
        self.assertEqual(got[("grok", "rea")], "aligned")
        self.assertEqual(self.snap(), after_delete)

        grok = self.home / ".grok" / "config.toml"
        grok.write_text(grok.read_text().replace("codebase-memory-mcp", "user-edited-cmd"))
        after_edit = self.snap()
        got = states(self.run_pfy("doctor", "--json"))
        self.assertEqual(got[("grok", "code-graph")], "drifted")
        self.assertEqual(got[("claude-code", "code-graph")], "aligned")
        self.assertEqual(self.snap(), after_edit)


class SecretTests(unittest.TestCase):
    def test_new_code_has_no_secret_reads(self):
        paths = [ROOT / "install.sh", ROOT / "pfylib" / "setup.py", ROOT / "pfylib" / "adapters"]
        for path in paths:
            self.assertTrue(path.exists(), path)
        proc = subprocess.run(
            ["grep", "-R", "-n", "-E", r"auth\.json|api_key|API_KEY|Authorization|access_token", *map(str, paths)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 1, proc.stdout)


if __name__ == "__main__":
    unittest.main()
