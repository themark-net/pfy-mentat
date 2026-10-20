# Autonomous decisions — harness2-local (2026-10-19 log, run 2026-10-20)

Format: choice | alternatives | why

## D1 — HOME fingerprint does not content-hash the big caches

Choice: import `home_sig` and mix its digest in for watched trees of at most 32 MiB. Larger trees use a structural digest (path, type, mode, mtime_ns, size, inode, symlink target; nested symlinks are not followed). | Alternative: call `home_sig` on every watched tree, including `~/.cache/uv` (21 GiB, 404k files) and `~/.npm` (3.6 GiB), before and after every stage step. | A full content hash reads tens of gigabytes per snapshot. Six steps would blow the 7h30m cap. Create, delete, resize, retouch, and replace still change the structural digest. Measured metadata walk of `~/.cache/uv`: 0.75 s.

## D2 — OpenCode config port until the relay binds

Choice: `stage.sh` writes `$W/tmp/state/opencode.json` with `baseURL http://127.0.0.1:8766/v1`, provider `llamacpp`, npm `@ai-sdk/openai-compatible`, apiKey `local`, temperature 0, seed 230. The sandbox rewrites the port when the relay binds. | Alternative: leave the file unwritten until item 2. | Upstream `config.py` and OpenCode need the file present, and item 1's stage is the place that generates it from `examples/opencode-ollama/opencode.json.template`.

## D3 — One worktree, lead implements in order

Choice: implement items on `bot/h1-harness2` in this worktree, serially. `project-map` is the only parallel agent (it writes `.project-map/` only). | Alternative: one `build/<phase>` worktree per item, as the orchestrator skill suggests. | The launch override forbids a second worktree and sends every result to this branch. The items share `examples/harness2-local/`.

## D4 — Clock is the launch override

Choice: start no new item after 6h from 2026-10-20T03:31:50-07:00 (09:31 local). Stop by 11:01 (7h30m). Live item 6 starts only if 3h15m remain (by about 07:46). | Alternative: the drop-in file's 5h / 6h cap. | The launch block says it wins where the two differ.

## D5 — Git config for the clone is empty and local

Choice: stage exports `GIT_TERMINAL_PROMPT=0`, `GIT_CONFIG_NOSYSTEM=1`, and `GIT_CONFIG_GLOBAL=$W/tmp/state/empty-gitconfig`. | Alternative: inherit `~/.gitconfig`. | A prompt would hang the unattended run. An `insteadOf` rewrite could send the clone to a host that is not on the allow-list.

## D6 — Stub tests use a private HARNESS2_W

Choice: stage behavior tests set `HARNESS2_W` to a temp directory. | Alternative: run stubs against `$W/tmp/harness2`. | The real stage directory must stay free for the pinned checkout. The temp tree still proves cache variables land under `$HARNESS2_W/tmp/state`.

## D7 — Read-only socket find also prunes not-owned unreadable dirs

Choice: on a read-only mount the socket scan is `find "$m" -xdev \( -path /proc -o -path /sys \) -prune -o -type d ! -user "$(id -u)" \( ! -executable -o ! -readable \) -prune -o -type s -print`. | Alternative: the drop-in's literal `! -executable ! -user` prune only. | On nimo (2026-10-20) the literal command exits 1: `/etc/sssd` is mode 751 root (other can search, nobody else can read), so `find` prints `Permission denied`. `/etc/ssl/private` is mode 710 root, which the literal `! -executable` prune already skips, so it is not the blocker. The adjusted command exits 0 on `/etc` (0.02 s) and lists no socket. An owned mode-0100 directory is still an error, because `! -user` is false for the sandbox user, so the fail-closed case in the spec stays. The 120 s cap is not raised. The drop-in text is updated in the sandbox commit that lands this find.

## D8 — The sweep proof that follows a symlink is find -L

Choice: keep `chmod -R -P` and `find -P`, and skip every `$RUNS/tmp` entry that is not a real directory (`os.lstat`, then `S_ISDIR`). The RED that shows a followed symlink is `find -P` changed to `find -L`. | Alternatives: drop `-P` because uutils calls it the default; use the spec's `chmod -R -L` as the only RED. | On nimo, `chmod (uutils coreutils) 0.10.0` does not change modes through a directory symlink for `-L`, `-H`, or the default, so `chmod -R -L` left the sweep test green. `find -L <ws> -xdev -type s -delete` deletes the socket in the target. Dropping the lstat skip handed the symlink and a regular file to both tools; the test went red because those paths were arguments, while `-P` still left the target modes alone. `-P` stays. If `-P` is rejected, the sweep exits 2. There is no fallback.

## D9 — This session's clock replaces the first session's

Choice: START is 2026-10-20T11:21:42-07:00. Start no new item after 2026-10-20T17:21:42-07:00. Stop by 2026-10-20T18:51:42-07:00. Live item 6 starts only if begun by 2026-10-20T15:36:42-07:00. | Alternative: keep D4's 09:31 / 11:01 / 07:46 limits from the first session. | The H1b block says this session's clock replaces those limits. D4 stays as the record of the first session.

## D10 — Stub driver shape

Choice: `sbun` waits on the sandbox instead of `exec` so an opt-in trace can write a start line and an end line, and it passes `--heldout` or `--runs` from the environment. Score tests use a synthetic bank (every label `push`) because the sandbox cannot see gold. The leak walk uses one real-bank task. `LocalProposer` forces `max_attempts=1` only when `HARNESS2_STUB_MODE` is set. The held-out path logs one line so `drive.log` exists. The `c1` scan matches rollout labels only (`__c1`, receipt `final_label`, `base_labels`) because upstream surface markdown contains the prose `c1 persona`. An audit `*.meta.json` `label` that matches a session label (`base`/`inv`/`dom`/`agg` plus an optional attempt) is not a gold label. | Alternatives: `exec` the sandbox; scan every `c1` boundary in the run dir; ban every `label` key in meta files; score the real bank from inside the sandbox. | `exec` drops the end line. A whole-tree `c1` scan false-positives on the component table. Upstream meta uses `label` for the session name. Live runs do not set `HARNESS2_STUB_MODE`, so they keep two transport attempts.

## D11 — Order-preserving stripped pin

Choice: pin the stripped file with `canonical_order` (`sort_keys=False`) at `ab0ee29bbe75b46d33248729f9c4dd61376ec357275c8debf6efdb4d296e1b7e`. The id map still uses sorted-key `canonical`. | Alternative: pin the sort_keys digest `6d6c09cf6467a7fbd72c5d7800be86794867e483c5aa2e26c7c35a38658b57bb` from the spec text. | `sort_keys` erases criteria order. A sorted-only strip stays inside the key-order band (first 20, last 12) and has that same `6d6c09cf` digest, so the test would stay green. The order-preserving pin goes red (`eb00a397` != `ab0ee29b`).
