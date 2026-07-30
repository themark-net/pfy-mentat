# Auth file-mount EBUSY (T-0064)

**Symptom:** Docker/podman bind-mount of Grok home/auth hits `EBUSY` when the path is busy (open handles, nested mounts).

## Mitigations (operator)

1. Prefer **copy-import** over live bind for auth secrets: `cage-grok-sessions-import-host` pattern.  
2. Mount a **dedicated** `grok-state/` dir, not `~/.grok` while a host Grok process is running.  
3. Stop host Grok / close sessions before remount.  
4. Avoid mounting the same directory twice (workspace + home overlap).  
5. On Linux: `fuser -vm <path>` to find holders; unmount stale binds.

## Status

Parked env polish — documented. No code change required when copy-import path is used.
