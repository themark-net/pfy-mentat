# AgenC Bootstrap & Launch Wrapper

**AgenC is the primary runtime** for this project (see `AGENTS.md` → Primary Runtime Policy).

## Primary Entry Point

Use `agenc-launch` (recommended) instead of calling `agenc` directly. It adds:

- Non-blocking (configurable) runtime update check on every launch
- Daemon health verification
- Clean hand-off to the real `agenc` binary

```bash
# Make executable
chmod +x bootstrap/agenc/agenc-launch

# Recommended: add to PATH or create alias
# e.g. in ~/.zshrc or ~/.bashrc
alias agenc="$HOME/path/to/local-llm-dev-tools/bootstrap/agenc/agenc-launch"

agenc-launch "your prompt here"
agenc-launch daemon status
agenc-launch --help
```

## Environment Variables

| Variable                    | Default     | Effect                                      |
|-----------------------------|-------------|---------------------------------------------|
| `AGENC_UPDATE_CHECK`        | `1`         | Set to `0` to skip update check             |
| `AGENC_UPDATE_MODE`         | `nonblocking` | `blocking` (wait) or `nonblocking`        |
| `AGENC_DAEMON_AUTOSTART`    | `1`         | Set to `0` to skip daemon health check      |
| `AGENC_NO_UPDATE`           | `0`         | Global kill-switch for all update checks    |

## Scheduling Updates

For periodic deeper updates you can use a simple cron or systemd timer:

```cron
# Daily at 03:00
0 3 * * * /full/path/to/agenc-launch runtime update >/dev/null 2>&1 || true
```

Later we will add a proper scheduled background skill inside AgenC itself.

## Related Files

- `AGENTS.md` — Primary Runtime Policy section
- Future: skills and integration docs under `integration/agenc/`
