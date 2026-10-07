# X intake local smokes (Entries 095-097)

Stdlib-only operate-or-FAIL checks for the 2026-10-06 X intake entries. Exit 0 PASS, 1 FAIL, 2 can't run here.
Each run writes `pipelines/smoke/<entry>/latest.json`. Nothing is installed or downloaded; scratch files go to a
tempfile dir that is removed.

```sh
QWEN38_URL=http://127.0.0.1:8080/v1 python3 examples/x-intake-local/smoke.py --entry qwen38flash
python3 examples/x-intake-local/smoke.py --entry sandlock     # needs Linux 6.12+ and the release binary
python3 examples/x-intake-local/smoke.py --entry foremerge    # needs the release binary and git
```

Binaries are looked up via `$SANDLOCK_BIN` / `$FOREMERGE_BIN`, then `~/DEVELOP/pfy-mentat/tmp/{sandlock,foremerge}/`,
then PATH. Not wired into CI or Make.
