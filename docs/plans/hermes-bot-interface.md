# Hermes bot interface

One-shot local bot turn behind a flag. Default stays the current opencode path. This is not a Feature GO and it does not rescore the catalog.

`./pfy attach hermes` is unchanged. That path still execs a `hermes` binary on `PATH` or prints the registry installer line. This command does not exec `~/.local/bin/hermes`, does not read `~/.hermes`, and does not run the installer.

## Surface

```bash
./pfy bot "prompt"
```

Prints the interface name, the reasoning setting, and the local endpoint, then runs one turn.

## Flag

`PFY_BOT_INTERFACE`

| Value | Behavior |
|---|---|
| unset, empty, `opencode`, `off` | opencode path (default, flag off) |
| `hermes` | isolated Hermes library driver |
| anything else | exit 2. Next: set the flag to `opencode` or `hermes` |

Turn it off: `unset PFY_BOT_INTERFACE` or `PFY_BOT_INTERFACE=opencode`.

## Config

| Env | Default | Role |
|---|---|---|
| `LOCAL_OPENAI_BASE_URL` | `http://127.0.0.1:11434/v1` | Ollama or llama-server. No hosted API and no key |
| `PFY_BOT_MODEL` | `qwen3.6:35b` | local tag |
| `PFY_BOT_REASONING` | `off` | `off` or `on` only. Printed before the call |
| `PFY_BOT_TIMEOUT` | `180` | seconds, then the child is killed |
| `PFY_HERMES_HOME` | `<repo>/tmp/hermes-bot-home` | refused if it resolves to `~/.hermes` |
| `PFY_HERMES_CHECKOUT` | `<repo>/tmp/hermes-agent` | pinned library tree |
| `PFY_HERMES_PYTHON` | `<repo>/tmp/.venv-hermes/bin/python` | interpreter for the driver |
| `PFY_BOT_OPENCODE` | `opencode` on `PATH` | fallback binary |

Hermes reasoning `off` writes `reasoning_effort: none` and `tools.tool_search.enabled: off` into the isolated home. Opencode is started as `opencode run --model ollama/<tag> --variant none` (or `--variant high` when reasoning is `on`). The opencode CLI has no temperature or seed switch. The variant flag is the explicit request. The bake-off proxy, not this command, is what forces the eval arms to the same body.

State dirs for the opencode path are `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, and `XDG_CACHE_HOME` under `<repo>/tmp/bot-interface/`. The command does not write `~/.config/opencode`.

## Fallback and recovery

| Failure | What happens |
|---|---|
| Flag is `hermes` and the checkout or python is missing | Print `FAIL`, do not run the installer, run the opencode path if that binary exists. If it does not, exit 2 and print `next: ./pfy attach opencode` |
| Model server down | Probe `/api/tags` and `/v1/models` for a few seconds. Do not start either agent. Exit 2. `next: ./pfy up` |
| Malformed tool call | A tool call whose arguments are not an object. Exit 1. Print `malformed tool call`. No second agent |
| Timeout | Kill the child process group this command started. Exit 2. `next: retry or raise PFY_BOT_TIMEOUT` |
| `PFY_HERMES_HOME` is `~/.hermes` | Exit 2 before any write. `next: unset PFY_HERMES_HOME` |

## Out of scope

- No product UI. CLI only.
- Catalog HOLD 70-75 stays. No `data/tools.json` rescore unless a later run changes the scores.
- No Feature GO.
