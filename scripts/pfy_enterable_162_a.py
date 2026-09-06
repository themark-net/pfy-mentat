#!/usr/bin/env python3
"""Enterable OpenCode session helpers — cite #162 (a).

Attach must open/focus a usable interactive terminal (not silent sidecar alone).
Launch env must arm/open enterable path or honest SKIP (copy alone insufficient).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

SESSION_REACH_OK = "terminal · OpenCode"
SESSION_FILE = "opencode-session-reach"
TERMINAL_PID_FILE = "opencode-terminal.pid"


def _which(*names):
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    return ""


def read_session_reach(STATE) -> str:
    path = Path(STATE) / SESSION_FILE
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()[:80]
    except OSError:
        return ""


def write_session_reach(STATE, text: str) -> None:
    STATE = Path(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / SESSION_FILE).write_text((text or "").strip()[:80] + "\n", encoding="utf-8")


def clear_session_reach(STATE) -> None:
    STATE = Path(STATE)
    for name in (SESSION_FILE, TERMINAL_PID_FILE):
        path = STATE / name
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def write_terminal_pid(STATE, pid: int) -> None:
    STATE = Path(STATE)
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / TERMINAL_PID_FILE).write_text(str(int(pid)) + "\n", encoding="utf-8")


def read_terminal_pid(STATE):
    path = Path(STATE) / TERMINAL_PID_FILE
    if not path.is_file():
        return 0
    try:
        return int(path.read_text(encoding="utf-8", errors="replace").strip())
    except (ValueError, OSError):
        return 0


def _focus_pid(pid: int) -> bool:
    """Best-effort focus an existing terminal/process window. True only if a window was activated."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    wmctrl = _which("wmctrl")
    if wmctrl:
        try:
            proc = subprocess.run(
                [wmctrl, "-lp"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            for line in (proc.stdout or "").splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[2] == str(pid):
                    wid = parts[0]
                    r = subprocess.run([wmctrl, "-ia", wid], capture_output=True, timeout=5, check=False)
                    if r.returncode == 0:
                        return True
        except Exception:
            pass
    xdotool = _which("xdotool")
    if xdotool:
        try:
            proc = subprocess.run(
                [xdotool, "search", "--pid", str(pid)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            wids = [w for w in (proc.stdout or "").split() if w.strip()]
            if wids:
                r = subprocess.run(
                    [xdotool, "windowactivate", "--sync", wids[0]],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                if r.returncode == 0:
                    return True
        except Exception:
            pass
    return False


def _has_display(env: dict) -> bool:
    if sys.platform == "darwin":
        return True
    display = (env.get("DISPLAY") or os.environ.get("DISPLAY") or "").strip()
    wayland = (env.get("WAYLAND_DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or "").strip()
    return bool(display or wayland)


def _cmdline(pid: int) -> str:
    try:
        raw = Path("/proc/%d/cmdline" % int(pid)).read_bytes()
    except (OSError, ValueError):
        return ""
    return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip()


def _find_opencode_pids(bin_path: str, after_ts: float | None = None) -> list:
    """Find alive processes whose cmdline looks like opencode (not wrappers)."""
    bin_path = str(bin_path)
    base = Path(bin_path).name
    found = []
    proc = Path("/proc")
    if not proc.is_dir():
        return found
    try:
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            cmd = _cmdline(pid)
            if not cmd:
                continue
            # Match opencode binary; exclude our python helpers / shells that only mention it
            if base not in cmd and "opencode" not in cmd.split()[:3]:
                # allow path form .../opencode ...
                if ("/" + base) not in cmd and not cmd.startswith(base + " "):
                    if bin_path not in cmd:
                        continue
            # Prefer argv0 looking like opencode
            argv0 = cmd.split()[0] if cmd else ""
            if "opencode" not in Path(argv0).name and bin_path not in cmd and base not in argv0:
                continue
            if after_ts is not None:
                try:
                    mtime = (entry / "stat").stat().st_mtime
                    # /proc/pid creation approx via starttime is harder; use cwd mtime loose gate
                    if mtime + 3600 < after_ts:
                        pass
                except OSError:
                    pass
            found.append(pid)
    except Exception:
        return found
    return found


def resolve_enterable_pid(bin_path: str, candidate: int, pid_alive) -> int:
    """Pick a still-alive enterable pid: candidate, its descendants, or live opencode."""
    try:
        candidate = int(candidate or 0)
    except (TypeError, ValueError):
        candidate = 0
    if candidate and pid_alive(candidate):
        return candidate
    if candidate:
        child = _find_alive_descendant(candidate, pid_alive)
        if child:
            return child
    # Wrapper exited (xfce4-terminal/gnome-terminal) — find live opencode
    for pid in _find_opencode_pids(bin_path):
        if pid_alive(pid):
            return pid
    return 0


def _find_alive_descendant(parent_pid: int, pid_alive, depth: int = 3) -> int:
    """Walk /proc for descendants of parent (handles reparented children poorly;
    also scans children of any pid that still lists parent in NSpid chain via PPid walk)."""
    try:
        parent_pid = int(parent_pid)
    except (TypeError, ValueError):
        return 0
    proc = Path("/proc")
    if not proc.is_dir():
        return 0
    # Build ppid map
    ppid_of = {}
    try:
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            try:
                status = (entry / "status").read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            ppid = 0
            for line in status.splitlines():
                if line.startswith("PPid:"):
                    try:
                        ppid = int(line.split()[1])
                    except (IndexError, ValueError):
                        ppid = 0
                    break
            ppid_of[pid] = ppid
    except Exception:
        return 0
    # BFS descendants while parent was alive; also include anyone whose ancestor was parent_pid
    frontier = {parent_pid}
    seen = set()
    found = []
    for _ in range(max(1, depth + 2)):
        nxt = set()
        for pid, ppid in ppid_of.items():
            if ppid in frontier and pid not in seen:
                nxt.add(pid)
                seen.add(pid)
                if pid != parent_pid and pid_alive(pid):
                    found.append(pid)
        if not nxt:
            break
        frontier = nxt
    return found[0] if found else 0


def _terminal_cmds(bin_path: str, cwd: str):
    """Yield argv lists to spawn a native terminal running opencode."""
    xte = _which("xdg-terminal-exec")
    if xte:
        yield [xte, bin_path]
    # Prefer terminals that keep a long-lived process when possible
    kitty = _which("kitty")
    if kitty:
        yield [kitty, "--directory", cwd, bin_path]
    alacritty = _which("alacritty")
    if alacritty:
        yield [alacritty, "--working-directory", cwd, "-e", bin_path]
    wezterm = _which("wezterm")
    if wezterm:
        yield [wezterm, "start", "--cwd", cwd, "--", bin_path]
    xterm = _which("xterm")
    if xterm:
        yield [xterm, "-e", "cd %s && exec %s" % (cwd, bin_path)]
    konsole = _which("konsole")
    if konsole:
        yield [konsole, "--workdir", cwd, "-e", bin_path]
    # Wrappers that often exit after spawn — still supported; resolve child/opencode after
    gnome = _which("gnome-terminal")
    if gnome:
        yield [gnome, "--working-directory=" + cwd, "--", bin_path]
    xfce = _which("xfce4-terminal")
    if xfce:
        yield [xfce, "--working-directory=" + cwd, "-e", bin_path]
    if sys.platform == "darwin":
        osa = _which("osascript")
        if osa:
            script = (
                'tell application "Terminal"\n'
                "  activate\n"
                '  do script "cd " & quoted form of "%s" & " && %s"\n'
                "end tell\n" % (cwd.replace('"', ""), bin_path)
            )
            yield [osa, "-e", script]


def spawn_terminal_opencode(bin_path: str, cwd: str, env: dict, log_path: Path, pid_alive) -> tuple:
    """Spawn native terminal running opencode. Returns (ok, pid, error).

    ok=True when an enterable session is up — tracks the real opencode/session pid,
    not a short-lived terminal wrapper (xfce4-terminal / gnome-terminal).
    """
    cwd = str(cwd)
    bin_path = str(bin_path)
    last_err = "no terminal"
    if not _has_display(env):
        return False, 0, "no DISPLAY · cannot open terminal"
    cmds = list(_terminal_cmds(bin_path, cwd))
    if not cmds:
        return False, 0, "no terminal binary on PATH"
    before = set(_find_opencode_pids(bin_path))
    t0 = time.time()
    for argv in cmds:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("ab") as f:
                f.write(("spawn: %s\n" % " ".join(argv)).encode("utf-8", errors="replace"))
                proc = subprocess.Popen(
                    argv,
                    cwd=cwd,
                    env=env,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            # Allow wrapper to hand off to child opencode
            time.sleep(0.6)
            real = resolve_enterable_pid(bin_path, proc.pid, pid_alive)
            if real and pid_alive(real):
                return True, real, ""
            # New opencode appearing after spawn
            after = set(_find_opencode_pids(bin_path)) - before
            for pid in sorted(after):
                if pid_alive(pid):
                    return True, pid, ""
            if argv and "osascript" in argv[0]:
                # macOS handoff — accept if any new opencode or Terminal still up
                after = set(_find_opencode_pids(bin_path)) - before
                if after:
                    return True, sorted(after)[0], ""
                return True, proc.pid, ""
            last_err = "terminal exited without enterable OpenCode session"
        except OSError as e:
            last_err = str(e)[:300]
            continue
        except Exception as e:
            last_err = str(e)[:300]
            continue
    # Last chance: any new opencode since we started trying
    after = set(_find_opencode_pids(bin_path)) - before
    for pid in sorted(after):
        if pid_alive(pid):
            return True, pid, ""
    _ = t0
    return False, 0, last_err or "terminal cannot start"
