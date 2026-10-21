# Autonomous decisions: harness2-local (2026-10-19 log, run 2026-10-20)

Format: choice | alternatives | why

## D1: HOME fingerprint does not content-hash the big caches

Choice: import `home_sig` and mix its digest in for watched trees of at most 32 MiB. Larger trees use a structural digest (path, type, mode, mtime_ns, size, inode, symlink target; nested symlinks are not followed). | Alternative: call `home_sig` on every watched tree, including `~/.cache/uv` (21 GiB, 404k files) and `~/.npm` (3.6 GiB), before and after every stage step. | A full content hash reads tens of gigabytes per snapshot. Six steps would blow the 7h30m cap. Create, delete, resize, retouch, and replace still change the structural digest. Measured metadata walk of `~/.cache/uv`: 0.75 s.

## D2: OpenCode config port until the relay binds

Choice: `stage.sh` writes `$W/tmp/state/opencode.json` with `baseURL http://127.0.0.1:8766/v1`, provider `llamacpp`, npm `@ai-sdk/openai-compatible`, apiKey `local`, temperature 0, seed 230. The sandbox does not rewrite this port (corrected 2026-10-20, Reviewer N3). `common.py write_opencode_config` takes the port from `HARNESS2_RELAY_PORT` and falls back to 8766, and `drive.py bind_relay_port` sets that variable from the llama-server endpoint. The port in `opencode.json` must match the llama-server port. | Alternative: leave the file unwritten until item 2. | Upstream `config.py` and OpenCode need the file present, and item 1's stage is the place that generates it from `examples/opencode-ollama/opencode.json.template`.

## D3: One worktree, lead implements in order

Choice: implement items on `bot/h1-harness2` in this worktree, serially. `project-map` is the only parallel agent (it writes `.project-map/` only). | Alternative: one `build/<phase>` worktree per item, as the orchestrator skill suggests. | The launch override forbids a second worktree and sends every result to this branch. The items share `examples/harness2-local/`.

## D4: Clock is the launch override

Choice: start no new item after 6h from 2026-10-20T03:31:50-07:00 (09:31 local). Stop by 11:01 (7h30m). Live item 6 starts only if 3h15m remain (by about 07:46). | Alternative: the drop-in file's 5h / 6h cap. | The launch block says it wins where the two differ.

## D5: Git config for the clone is empty and local

Choice: stage exports `GIT_TERMINAL_PROMPT=0`, `GIT_CONFIG_NOSYSTEM=1`, and `GIT_CONFIG_GLOBAL=$W/tmp/state/empty-gitconfig`. | Alternative: inherit `~/.gitconfig`. | A prompt would hang the unattended run. An `insteadOf` rewrite could send the clone to a host that is not on the allow-list.

## D6: Stub tests use a private HARNESS2_W

Choice: stage behavior tests set `HARNESS2_W` to a temp directory. | Alternative: run stubs against `$W/tmp/harness2`. | The real stage directory must stay free for the pinned checkout. The temp tree still proves cache variables land under `$HARNESS2_W/tmp/state`.

## D7: Read-only socket find also prunes not-owned unreadable dirs

Choice: on a read-only mount the socket scan is `find "$m" -xdev \( -path /proc -o -path /sys \) -prune -o -type d ! -user "$(id -u)" \( ! -executable -o ! -readable \) -prune -o -type s -print`. | Alternative: the drop-in's literal `! -executable ! -user` prune only. | On nimo (2026-10-20) the literal command exits 1: `/etc/sssd` is mode 751 root (other can search, nobody else can read), so `find` prints `Permission denied`. `/etc/ssl/private` is mode 710 root, which the literal `! -executable` prune already skips, so it is not the blocker. The adjusted command exits 0 on `/etc` (0.02 s) and lists no socket. An owned mode-0100 directory is still an error, because `! -user` is false for the sandbox user, so the fail-closed case in the spec stays. The 120 s cap is not raised. The drop-in text is updated in the sandbox commit that lands this find.

## D8: The sweep proof that follows a symlink is find -L

Choice: keep `chmod -R -P` and `find -P`, and skip every `$RUNS/tmp` entry that is not a real directory (`os.lstat`, then `S_ISDIR`). The RED that shows a followed symlink is `find -P` changed to `find -L`. | Alternatives: drop `-P` because uutils calls it the default; use the spec's `chmod -R -L` as the only RED. | On nimo, `chmod (uutils coreutils) 0.10.0` does not change modes through a directory symlink for `-L`, `-H`, or the default, so `chmod -R -L` left the sweep test green. `find -L <ws> -xdev -type s -delete` deletes the socket in the target. Dropping the lstat skip handed the symlink and a regular file to both tools; the test went red because those paths were arguments, while `-P` still left the target modes alone. `-P` stays. If `-P` is rejected, the sweep exits 2. There is no fallback.

## D9: This session's clock replaces the first session's

Choice: START is 2026-10-20T11:21:42-07:00. Start no new item after 2026-10-20T17:21:42-07:00. Stop by 2026-10-20T18:51:42-07:00. Live item 6 starts only if begun by 2026-10-20T15:36:42-07:00. | Alternative: keep D4's 09:31 / 11:01 / 07:46 limits from the first session. | The H1b block says this session's clock replaces those limits. D4 stays as the record of the first session.

## D10: Stub driver shape

Choice: `sbun` waits on the sandbox instead of `exec` so an opt-in trace can write a start line and an end line, and it passes `--heldout` or `--runs` from the environment. Score tests use a synthetic bank (every label `push`) because the sandbox cannot see gold. The leak walk uses one real-bank task. `LocalProposer` forces `max_attempts=1` only when `HARNESS2_STUB_MODE` is set. The held-out path logs one line so `drive.log` exists. The `c1` scan matches rollout labels only (`__c1`, receipt `final_label`, `base_labels`) because upstream surface markdown contains the prose `c1 persona`. An audit `*.meta.json` `label` that matches a session label (`base`/`inv`/`dom`/`agg` plus an optional attempt) is not a gold label. | Alternatives: `exec` the sandbox; scan every `c1` boundary in the run dir; ban every `label` key in meta files; score the real bank from inside the sandbox. | `exec` drops the end line. A whole-tree `c1` scan false-positives on the component table. Upstream meta uses `label` for the session name. Live runs do not set `HARNESS2_STUB_MODE`, so they keep two transport attempts.

## D11: Order-preserving stripped pin

Choice: pin the stripped file with `canonical_order` (`sort_keys=False`) at `ab0ee29bbe75b46d33248729f9c4dd61376ec357275c8debf6efdb4d296e1b7e`. The id map still uses sorted-key `canonical`. | Alternative: pin the sort_keys digest `6d6c09cf6467a7fbd72c5d7800be86794867e483c5aa2e26c7c35a38658b57bb` from the spec text. | `sort_keys` erases criteria order. A sorted-only strip stays inside the key-order band (first 20, last 12) and has that same `6d6c09cf` digest, so the test would stay green. The order-preserving pin goes red (`eb00a397` != `ab0ee29b`).

## D12: What the decision harness maps

Choice: one skill, `jev-decision`. The prompt is `decision_prompt()` in `examples/typed-decisions-local/trial.py`, between the `HARNESS2_PROMPT_*` markers, and it names the 0.85 gate. Guardrails are the `## Do not` block of `AGENTS.md` plus the Feature-GO gate line. Tool guidance is the `### Custom Scripts, Tools & Automation` section. `write_base` also ships `scripts/pfy_jev_230.py` because the skill line `python3 scripts/pfy_jev_230.py` fails upstream's "invokes a script it does not ship" check. Adopt ignores that stub when the bytes match and rejects an edit to it. | Alternatives: map every `.grok/skills` entry; edit the skill so it no longer mentions `python3 scripts/...`; leave skills empty. | The decision task is the #230 Choice set, and `jev-decision` is the skill that defines it. Editing the skill would change the operator surface. An empty skills directory is not the map the spec asks for. The stub is harness-only and is not an allowed repo write.

## D13: The chmod -L proof was the fixture

Choice: keep `chmod -R -P`. The RED is `chmod -R -L` against target modes 400 and 500. | Alternative: keep blaming uutils 0.10.0 for not following a directory symlink (D8). | On nimo, uutils 0.10.0 `chmod -R -L u+rwX` changes 400 to 600 and 500 to 700. `-P` leaves 400 and 500. Modes 600 and 700 already include `u+rwX`, so no chmod can show a follow. D8's green `chmod -R -L` run was that fixture. `-P` stays.

## D14: Relay idle is the 600 s client budget

Choice: `RELAY_IDLE_S = 600` on both splice sides. | Alternative: delete the idle cut and rely only on the `/health` watchdog. | The spec gives each llama-server request a 600 s client timeout. A silent prefill or a request waiting behind `-np 1` must not be cut at 30 s. A finite idle still bounds a splice the watchdog is not watching. The RED sets the constant back to 30.

## D15: Caller XDG data and state win

Choice: `env.sh` sets `XDG_DATA_HOME` and `XDG_STATE_HOME` only when unset (`:=`), then exports them. | Alternative: save and restore the caller values only inside `sbun`. | Upstream Proposer and the executor launcher set those two to the call workspace. The state dir is read-only inside the sandbox, so forcing it makes `mkdir` fail with EROFS. A direct `sandbox.py` after `source env.sh` has the same root cause, so the fix belongs in `env.sh`.

## D16: sbun takes the relay port from one source

Choice: `sbun` runs `common.py relay-port`, which reads only `HARNESS2_RELAY_PORT`, and passes that port as `--expose` and `--allow`. Unknown (unset, or not an integer from 1 to 65535) exits 2 with `BLOCKED: relay port unknown`. `drive.py` sets the variable from the endpoint URL before any call. | Alternative: hardcode 8766 inside `sbun`, or keep launching with no listener. | No listener means 0 POSTs and a hang until the 15 min wall. A silent default would aim the relay at the wrong port. The generated OpenCode config uses the same variable.

## D17: Watchdog gap is 10 s after a miss too

Choice: both probe waits use `WATCHDOG_GAP_S = 10`. The single-stall test is one 12 s `/health` blackout. | Alternative: keep the 0.2 s miss wait, or treat a 6 s stall of one request as the RED. | The spec is a round trip every 10 s and 2 misses in a row. A 6 s stall of one request stays green under the 0.2 s mutant: the first probe's 5 s recv timeout uses the stall, and the retry is a new request (measured rc 0 in 22.8 s). A 12 s blackout covers two 5 s probes when the gap is 0.2 s, and the 10 s gap starts the next probe after it. A dead server still ends the call in about 20 s.

## D18: Stage tests bring their own Python 3.12

Choice: `HARNESS2_PY312` overrides discovery. Otherwise prefer `cpython-3.12.12`, then the first `cpython-3.12.*` under `~/.local/share/uv/python`. After `realpath`, the path must match that directory's `cpython-3.12.*/bin/python3.12`. | Alternative: keep the tests pointed at the host's real 3.12.12 tree. | Tester's box has no that tree, so the stage tests failed or passed without asserting the stage rc. The kept-`.env` test now requires rc 0 and `env: kept existing .env`. Pointing the stand-in away fails with `BLOCKED: no-python312`.

## D19: Refuse a checkout under /tmp or /run

Choice: after resolving the worktree, exit 2 `BLOCKED: checkout under /tmp` (or `/run`) before any mount. | Alternative: let bwrap hide the checkout and fail later. | The sandbox mounts tmpfs on `/tmp` and `/run`, so a checkout there is not the tree the operator thinks is running. The test points `HARNESS2_W` at a symlink under the worktree and does not create a real checkout in `/tmp`.

## D20: H1c clock

Choice: START is 2026-10-20T12:23:06-07:00. Start no new item after 2026-10-20T18:23:06-07:00. Stop by 2026-10-20T19:53:06-07:00. Live item 6 starts only if begun by 2026-10-20T16:38:06-07:00. | Alternative: keep D9's H1b limits. | The H1c block says this session's clock replaces those limits. D4 and D9 stay as the record of the earlier sessions. Item 2c is one sequential workstream: the sub-items share `sandbox.py`.

## D21: Proposal gate is a host-side CLI

Choice: `propose.py` reads a receipt with `install_mode`, `heldout.a1`, `heldout.a2`, `heldout.c` (`correct` or `n_correct`, `n`, `wrong_but_confident`, `parse_ok`), and `relay_log`. `GAIN_MIN = 2`. Paid-key values shorter than 8 characters are ignored. The bare repo for tests is `$W/tmp/propose-tests`, not `/tmp`. `origin/main` moved to Hermes eval commits after `aed526d`; this branch is not merged with that tip. A proposal clones whatever `main` the given remote has. | Alternative: call only upstream's grader-marker check, and rebase onto current `origin/main` before item 5. | Upstream accepted `label: B correct`. Rebase would rewrite pushed commits. The short-value floor keeps a dummy `local` key from matching ordinary prose.

## D22: Blob id counts as the model, and qwen thinking stays off

Choice: `endpoint_up` accepts a 64-character `HARNESS2_GGUF_SHA` in the `/v1/models` body, and strips one trailing `/v1`. The generated model options add `chat_template_kwargs.enable_thinking: false` next to temperature 0 and seed 230. | Alternatives: require the OpenCode name in the body; restart llama-server with a thinking flag the lane script does not pass; rename the model so it does not contain `qwen`. | This server lists the blob digest `d372de8e...` and still accepts `llamacpp/qwen3.6-35b` on chat completions. A direct call with thinking left on returned empty `content` and `finish_reason: length`. The same call with `enable_thinking: false` returned `pong`. OpenCode forwards unknown `@ai-sdk/openai-compatible` provider options into the JSON body, which is how seed 230 already arrives. The lane script is unchanged.

## D23: env.sh turns off the models.dev fetch

Choice: `env.sh` exports `OPENCODE_DISABLE_MODELS_FETCH=1` and the other five `OPENCODE_DISABLE_*` names. An executor that exits without `answer.json` raises, including rc 0. | Alternative: leave the fetch on and allow the 0/16 score. | A live `sbun` call without the flag exits 0, prints `FailedToOpenSocket` for `https://models.dev/api.json`, writes no stdout, and sends no POST. The same call with the flag returns `pong`. The 13:54 a1 score of 0/16 had no POST and is not a base run.

## D24: The executor prompt points at systemprompt.md

Choice: the executor user prompt tells OpenCode to read `systemprompt.md` first and follow its answer shape. | Alternative: keep "Read cases.json" only, or accept `id` / `criteria_key` with no confidence as a parsed answer. | The 13:58 a1 call did reach the server (temperature 0, seed 230) and wrote `answer.json`, but the model ran a script that picked the first criteria key and used `id` and `criteria_key`. It never opened `systemprompt.md`. The scorer requires `case`, `choice`, and `confidence`, so the score was 0/16 with `parse_ok` 0. That run is not the base. A harness edit cannot move the score if the executor never reads the harness.

## D25: Do not raise ctx after the live run

Choice: keep ctx 32768. Do not restart llama-server and do not rerun the chain. | Alternatives: raise ctx to 49152 and rerun; treat the two truncated calls as a failed item. | The spec raises ctx to 49152 only when the first editor or executor prompt exceeds 24k tokens and MemAvailable still has 25 GiB of headroom. Prompt-eval sizes start at 30, 17, 31. The first large one is 10349. The peak is 24231, and two later calls log `truncated = 1` at `n_tokens = 32767`. The first-prompt condition is not met. Scoring-window MemAvailable stayed about 49.8 GiB, so headroom alone would not have blocked a raise. The held-out score is 15/16 against a better base of 15/16. The best possible rerun is 16/16, a gain of 1, and the gate needs 2.
