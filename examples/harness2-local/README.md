# harness2-local

Pinned local Harness² stage and the one-port sandbox around every OpenCode process. Setup is `stage.sh` only. It does not call `harness2-setup`, `harness2-check`, `harness2`, or `harness2-judge`. `env.sh` points caches and XDG dirs at `$W/tmp/state`.

OpenCode at pin `23fb5e0516c99ac04a1aa46c193efda2e1b9bb24` reads its managed config directory from `/etc/opencode` on Linux (`packages/opencode/src/config/managed.ts:30`). `managedConfigDir()` at line 35 of that file uses `OPENCODE_TEST_MANAGED_CONFIG_DIR` when it is set. `packages/opencode/src/config/config.ts:619-623` merges `opencode.json` and `opencode.jsonc` from that directory when the directory exists. The sandbox always drops `OPENCODE_TEST_MANAGED_CONFIG_DIR`.

The build spec is [docs/build-dropins/harness2-local.md](../../docs/build-dropins/harness2-local.md). The run log is [docs/ops/RUN-LOG-harness2-local.md](../../docs/ops/RUN-LOG-harness2-local.md).
