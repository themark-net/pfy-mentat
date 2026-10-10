# X intake local smokes (Entries 095-100, 103-105)

Stdlib-only operate-or-FAIL checks for the X intake entries. Exit 0 PASS, 1 FAIL, 2 can't run here.
Each run writes `pipelines/smoke/<entry>/latest.json`. Nothing is installed or downloaded; scratch files go to a
tempfile dir that is removed.

```sh
QWEN38_URL=http://127.0.0.1:8080/v1 python3 examples/x-intake-local/smoke.py --entry qwen38flash
python3 examples/x-intake-local/smoke.py --entry sandlock     # needs Linux 6.12+ and the release binary
python3 examples/x-intake-local/smoke.py --entry foremerge    # needs the release binary and git
python3 examples/x-intake-local/smoke_098_100.py --entry sponsio      # needs a venv with `pip install --pre sponsio`
python3 examples/x-intake-local/smoke_098_100.py --entry opensteps    # needs a clone of kharmanskyi/open-steps, bash, git
python3 examples/x-intake-local/smoke_098_100.py --entry repoharness  # repository-harness harness-v0.1.10 harness-linux-x64 sha256 68b6a51e40cd8e229f1f056c2aa5ea93de7934f746dcf8dd38e3b7d9dd4ee397, plus git
python3 examples/x-intake-local/smoke_103_105.py --entry bugpatrol    # npm --prefix bugpatrol@0.3.0, Node 22+, git; fake local OpenAI-compatible endpoint, no model or key
python3 examples/x-intake-local/smoke_103_105.py --entry graphjin     # graphjin v3.21.6 linux_amd64 binary sha256 e6f0fd88f99b07e8036ba7db76f24f0fceab697935559d154e823b5951f46805; throwaway SQLite
python3 examples/x-intake-local/smoke_103_105.py --entry antislop     # a clone of miqdadbadjuber/anti-slop; SKILL.md frontmatter check
```

Prereqs are looked up via `$SANDLOCK_BIN` / `$FOREMERGE_BIN` / `$SPONSIO_PY` / `$OPEN_STEPS_DIR` / `$HARNESS_BIN`,
then `~/DEVELOP/pfy-mentat/tmp/{sandlock,foremerge,sponsio/.venv,open-steps,repository-harness}/`, then PATH where
it applies. Sponsio, opensteps, and repoharness tool subprocesses point HOME at a fresh temp dir (git keeps the
parent env) so they never touch real harness state. `PFY_XINTAKE_TIMEOUT` (float seconds, > 0) overrides those
timeouts; empty or invalid keeps 60s for opensteps hooks and 120s for sponsio and repoharness.

Entries 103-105 (`smoke_103_105.py`) look up `$BUGPATROL_BIN` + `$BUGPATROL_NODE` / `$GRAPHJIN_BIN` (pin override
`$GRAPHJIN_SHA256`) / `$ANTISLOP_DIR`, then `~/DEVELOP/pfy-mentat/tmp/{bugpatrol/node_modules/.bin/bugpatrol,
bugpatrol/node/bin/node,graphjin/graphjin,anti-slop}`, then PATH where it applies. Tool subprocesses get a fresh temp
HOME. The bugpatrol smoke strips paid provider keys from the env and serves its own stdlib fake model on 127.0.0.1,
so it never calls a real model; the graphjin smoke only binds 127.0.0.1 on a free port. `PFY_XINTAKE_TIMEOUT`
overrides 120s for bugpatrol explore and 60s for graphjin startup.
Not wired into CI or Make.
