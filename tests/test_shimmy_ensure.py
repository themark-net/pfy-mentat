"""Shimmy is the last engine ./pfy up will start (ADR-0014)."""
from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PFY = ROOT / "scripts" / "pfy"


def _chunk(state: str) -> str:
    text = PFY.read_text(encoding="utf-8")
    start = text.index("shimmy_health()")
    end = text.index("\nprint_live_models(")
    head = (
        'have() { command -v "$1" >/dev/null 2>&1; }\n'
        f'STATE_DIR="{state}"\n'
        'mkdir -p "$STATE_DIR"\n'
    )
    return head + text[start:end]


def _cold_start_order(ollama_rc: int) -> subprocess.CompletedProcess[str]:
    """Run the cold-start chain with stub ensures. No engine binary is started."""
    text = PFY.read_text(encoding="utf-8")
    cold = text.split("# Cold start", 1)[1].split("rt=$(local_runtime)", 1)[0]
    inner = "started=0" + cold.split("started=0", 1)[1]
    lines = inner.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()
    # The slice includes the else-closer. The chain's own fi lines are indented further.
    if lines and lines[-1].strip() == "fi" and (len(lines[-1]) - len(lines[-1].lstrip(" "))) < 4:
        lines.pop()
    header = """set -euo pipefail
order=""
have() {
  case "$1" in
    ollama|shimmy) return 0 ;;
    *) return 1 ;;
  esac
}
ensure_freetoken() { order="$order ft"; return 0; }
ensure_llama_swap() { order="$order swap"; return 0; }
ensure_llama_server() { order="$order llama"; return 0; }
ensure_ollama_adapter() { order="$order ollama"; return %d; }
ensure_shimmy() { order="$order shimmy"; return 0; }
""" % ollama_rc
    script = header + "\n".join(lines) + '\nprintf "%s\\n" "$order"\n'
    return subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
        timeout=15,
    )


class ShimmyEnsureTests(unittest.TestCase):
    def test_cold_start_tries_shimmy_after_ollama(self):
        """Fail: shimmy runs before ollama, or ollama success still starts shimmy.
        Recover: ollama success records only ollama. Ollama failure then records shimmy.
        """
        ok = _cold_start_order(0)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertEqual(ok.stdout.strip(), "ollama")
        failed = _cold_start_order(1)
        self.assertEqual(failed.returncode, 0, failed.stdout + failed.stderr)
        self.assertEqual(failed.stdout.strip(), "ollama shimmy")

    def test_missing_binary_is_stub(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["PATH"] = "/usr/bin:/bin"
            env["PFY_STATE_DIR"] = tmp
            env.pop("LOCAL_OPENAI_BASE_URL", None)
            proc = subprocess.run(
                ["bash", "-c", _chunk(tmp) + "\nensure_shimmy\n"],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("STUB: shimmy not on PATH", proc.stdout)
        self.assertIn("shimmy serve --bind 127.0.0.1:11435", proc.stdout)

    def test_starts_bound_to_11435_then_healthy(self):
        with tempfile.TemporaryDirectory() as tmp:
            bind = Path(tmp) / "bin"
            bind.mkdir()
            log = Path(tmp) / "shimmy.args"
            (bind / "shimmy").write_text(
                textwrap.dedent(
                    """\
                    #!/bin/bash
                    printf '%s\\n' "$*" >> "$SHIMMY_LOG"
                    exit 0
                    """
                ),
                encoding="utf-8",
            )
            (bind / "curl").write_text(
                textwrap.dedent(
                    """\
                    #!/bin/bash
                    url=""
                    for a in "$@"; do url="$a"; done
                    if [[ "$url" == *11435* ]] && grep -q 'serve --bind 127.0.0.1:11435' "$SHIMMY_LOG" 2>/dev/null; then
                      exit 0
                    fi
                    exit 1
                    """
                ),
                encoding="utf-8",
            )
            os.chmod(bind / "shimmy", 0o755)
            os.chmod(bind / "curl", 0o755)
            env = os.environ.copy()
            env["PATH"] = f"{bind}:/usr/bin:/bin"
            env["PFY_STATE_DIR"] = tmp
            env["SHIMMY_LOG"] = str(log)
            env.pop("LOCAL_OPENAI_BASE_URL", None)
            proc = subprocess.run(
                ["bash", "-c", _chunk(tmp) + "\nensure_shimmy\n"],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("shimmy API healthy", proc.stdout)
            self.assertIn("serve --bind 127.0.0.1:11435", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
