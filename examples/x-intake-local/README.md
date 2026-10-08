# X intake local smokes (Entries 095-100)

Stdlib-only operate-or-FAIL checks for the X intake entries. Exit 0 PASS, 1 FAIL, 2 can't run here.
Each run writes `pipelines/smoke/<entry>/latest.json`. Nothing is installed or downloaded; scratch files go to a
tempfile dir that is removed.

```sh
QWEN38_URL=http://127.0.0.1:8080/v1 python3 examples/x-intake-local/smoke.py --entry qwen38flash
python3 examples/x-intake-local/smoke.py --entry sandlock     # needs Linux 6.12+ and the release binary
python3 examples/x-intake-local/smoke.py --entry foremerge    # needs the release binary and git
python3 examples/x-intake-local/smoke_098_100.py --entry sponsio      # needs a venv with `pip install --pre sponsio`
python3 examples/x-intake-local/smoke_098_100.py --entry opensteps    # needs a clone of kharmanskyi/open-steps, bash, git
python3 examples/x-intake-local/smoke_098_100.py --entry repoharness  # needs the harness-linux-x64 release binary and git
```

Prereqs are looked up via `$SANDLOCK_BIN` / `$FOREMERGE_BIN` / `$SPONSIO_PY` / `$OPEN_STEPS_DIR` / `$HARNESS_BIN`,
then `~/DEVELOP/pfy-mentat/tmp/{sandlock,foremerge,sponsio/.venv,open-steps,repository-harness}/`, then PATH where
it applies. The opensteps smoke points HOME at a temp dir so the hooks never touch real harness state.
Not wired into CI or Make.
