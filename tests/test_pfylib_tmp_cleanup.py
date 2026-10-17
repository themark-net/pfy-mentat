"""A run of the mkdtemp modules leaves no new temp dirs under the prefixes they use.

Covers pfylib-* plus the launcher prefix and the x-intake smoke prefixes, including
the dirs the smoke scripts themselves create while those tests run.
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULES = (
    "tests.test_cli",
    "tests.test_toolsets",
    "tests.test_hedge",
    "tests.test_loop_paint",
    "tests.test_attach",
    "tests.test_pfy_launcher_p1",
    "tests.test_x_intake_smoke_098_100",
    "tests.test_x_intake_smoke_103_105",
    "tests.test_x_intake_smoke_103_111_receipts",
    "tests.test_x_intake_smoke_106_108",
    "tests.test_x_intake_smoke_109_111",
    "tests.test_x_intake_smoke_112_114",
    "tests.test_x_intake_smoke_115_116",
    "tests.test_x_intake_smoke_117_118",
    "tests.test_x_intake_smoke_119_121",
    "tests.test_x_intake_smoke_122_124",
)

# Prefixes these modules and the smokes they drive create under /tmp.
PREFIXES = (
    "pfylib-",
    "pfy-launcher-p1-",
    "pfy-xintake-",
    "pfy-bugpatrol-",
    "pfy-graphjin-",
    "pfy-rulora-",
    "pfy-har-",
    "pfy-cm-",
    "pfy-smolvm-",
    "pfy-brigade-",
    "pfy-runx-",
    "pfy-bwrap-probe-",
    "pfy-node-",
    "pfy-overtime-",
    "pfy-festival-",
    "pfy-sloptrim-",
    "pfy-sponsio-",
    "pfy-opensteps-",
    "pfy-os-home-",
    "pfy-harness-",
    "pfy-sandlock-",
    "pfy-foremerge-",
    "pfy-kander-",
    "pfy-moira-",
    "pfy-agentdescent-",
    "pfy-kenfold-",
    "pfy-tsa-",
    "pfy-llmrouter-",
    "pfy-hr-",
    "pfy-squadra-",
    "pfy-assay-",
    "pfy-openqodex-",
)


def _tracked_tmp_paths() -> set[str]:
    tmp = Path("/tmp")
    found: set[str] = set()
    for prefix in PREFIXES:
        found.update(str(path) for path in tmp.glob(prefix + "*"))
    return found


class PfylibTmpCleanupTests(unittest.TestCase):
    def test_module_run_leaves_no_new_tmp_dirs(self):
        before = _tracked_tmp_paths()
        subprocess.run(
            ["python3", "-m", "unittest", *MODULES],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        after = _tracked_tmp_paths()
        self.assertEqual(after - before, set())
