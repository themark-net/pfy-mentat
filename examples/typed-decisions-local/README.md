# typed-decisions-local (X intake Entries 086-088)

One stdlib smoke for three I0 catalog entries from the 2026-10-05 daily X intake:

| Entry | Tool | Command | Expected on nimo today |
|------|------|---------|------------------------|
| 086 | Laya | `python3 examples/typed-decisions-local/smoke.py --entry laya` | exit 2 until a venv exists at `~/DEVELOP/pfy-mentat/tmp/laya-venv` |
| 087 | Bespoke Nimble | `python3 examples/typed-decisions-local/smoke.py --entry nimble` | exit 2 (no NVIDIA GPU, not Apple Silicon) |
| 088 | Beacon | `python3 examples/typed-decisions-local/smoke.py --entry beacon` | exit 2 until a user-mode install exists |

Exit 0 = PASS, 1 = ran but the check failed, 2 = can't run here. Each run writes `pipelines/smoke/<entry>/latest.json`.
The script never installs packages or downloads weights itself. Installs go under `~/DEVELOP/pfy-mentat/tmp/` only.
