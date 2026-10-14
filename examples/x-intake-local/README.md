# X intake local smokes (Entries 095-100, 103-111)

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
python3 examples/x-intake-local/smoke_106_108.py --entry rulora       # npm --prefix @rulora/core@0.1.0-alpha.4, Node 20+; Core controls offline, no model
python3 examples/x-intake-local/smoke_106_108.py --entry har          # npm --prefix @osfactory/har@1.16.0, Node 20+, git; telemetry off, temp HOME, throwaway repo
python3 examples/x-intake-local/smoke_106_108.py --entry cassmemory   # cass-memory v0.5.0 linux-x64 binary sha256 06e1563881f8bb1225cf7036068252ef210f242704a27f8ce32518b822181bd7; no keys
python3 examples/x-intake-local/smoke_109_111.py --entry smolvm       # smolvm v1.26.1 linux-x86_64 tarball (smolvm-bin sha256 62ed0353d664c2d6d78bd87ecf3213c64464003f51cb58506b87b187b1a6494a), /dev/kvm read/write
python3 examples/x-intake-local/smoke_109_111.py --entry brigade      # venv with brigade-cli==0.27.0, git; BRIGADE_NO_UPDATE_CHECK=1, throwaway repo
python3 examples/x-intake-local/smoke_109_111.py --entry runx         # runx 0.9.1 musl binary sha256 e0c0627882c2ce7a4e8cfb20cf4896a4aa371db0e13c95c8b86fa31276388b60, clone at cli-v0.9.1, node
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

Entries 106-108 (`smoke_106_108.py`) look up `$RULORA_DIR` + `$RULORA_NODE` / `$HAR_BIN` + `$HAR_NODE` / `$CM_BIN`
(pin override `$CM_SHA256`), then `~/DEVELOP/pfy-mentat/tmp/{rulora,rulora/node/bin/node,har/node_modules/.bin/har,
har/node/bin/node,cass-memory/cm}`, then PATH where it applies. Tool subprocesses get a fresh temp HOME and an env
with paid provider keys (plus AWS credentials, `OLLAMA_BASE_URL`, `HAR_PORTAL_TOKEN`, `CASS_PATH`) stripped; none of
the three calls a model. The har smoke runs `har telemetry off` before anything else and FAILs if agent hook files
(`~/.cursor/hooks.json`, `~/.claude/settings.json`, `~/.codex/hooks.json`) appear in its temp HOME; its session
worktree lives under that temp HOME too. `PFY_XINTAKE_TIMEOUT` overrides the 120s per-command timeout.

Entries 109-111 (`smoke_109_111.py`) look up `$SMOLVM_BIN` (pin override `$SMOLVM_SHA256`) / `$BRIGADE_BIN`
(version override `$BRIGADE_VERSION`) / `$RUNX_BIN` (pin override `$RUNX_SHA256`) + `$RUNX_SRC` + `$RUNX_NODE`, then
`~/DEVELOP/pfy-mentat/tmp/{smolvm/smolvm,brigade/.venv/bin/brigade,runx/runx,runx/src,runx/node/bin/node}`, then PATH
where it applies. Tool subprocesses get a fresh temp HOME and an env with paid provider keys, `XDG_*` and inherited
`SMOLVM_*`/`BRIGADE_*`/`RUNX_*` stripped; none of the three calls a model. When `bwrap` works, the brigade and runx
commands run with a read-only root, only the temp HOME and scratch dir writable, and no network; otherwise the smoke
checks the tools' real-HOME state dirs did not change (receipt field `containment`). The smolvm smoke exits 2 without
read/write `/dev/kvm`, pulls `alpine` from Docker Hub on the host (`$SMOLVM_IMAGE` overrides), and adds
checkpoint/rewind only with `SMOLVM_CHECKPOINT=1`. `PFY_XINTAKE_TIMEOUT` overrides the 120s per-command timeout (300s
for smolvm machine commands).

New smokes must start every subprocess with `run_isolated` in `smoke.py` and with nothing else. Not `subprocess`,
not `os.system`, and not the older `run` helper (that one stays for Entries 095-097). `run_isolated` builds a clean
environment and does not copy the parent process's variables. It sets `HOME` to the temp directory the caller
passes. It starts the child in a new session and SIGKILLs the process group on timeout, so a grandchild the child
forked dies too. Pass `bwrap_writable` (a list of directories to bind writable) to add a bubblewrap prefix when
`bwrap` works; the prefix includes `--unshare-pid` when that flag works. Pass `None` to skip bubblewrap. `extra`
is only for variables the smoke itself names. Do not pass the parent environment as `extra`.

Entries 115-116 (`smoke_115_116.py`):

```sh
python3 examples/x-intake-local/smoke_115_116.py --entry openqodex   # Node >= 22, package pinned 0.12.0
python3 examples/x-intake-local/smoke_115_116.py --entry assay       # assay-ui pinned 0.3.0, local Chromium
```

OpenQodex looks up `$OPENQODEX_DIR` and `$OPENQODEX_NODE`, then `~/DEVELOP/pfy-mentat/tmp/openqodex`. Its HOME is
`$OPENQODEX_HOME` or `tmp/openqodex/home`, and that path must resolve under `~/DEVELOP/pfy-mentat/tmp` or the
system temp directory. Assay looks up `$ASSAY_BIN`, then `tmp/assay/venv/bin/assay`, and Chromium from
`$PLAYWRIGHT_BROWSERS_PATH` or `tmp/assay/ms-playwright`. Version probes use the same helper as the tool commands.
`PFY_XINTAKE_TIMEOUT` overrides the 600s per-command timeout.

Not wired into CI or Make.
