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


def _terminal_cmds(bin_path: str, cwd: str):
    """Yield argv lists to spawn a native terminal running opencode."""
    xte = _which("xdg-terminal-exec")
    if xte:
        yield [xte, bin_path]
    gnome = _which("gnome-terminal")
    if gnome:
        yield [gnome, "--working-directory=" + cwd, "--", bin_path]
    kitty = _which("kitty")
    if kitty:
        yield [kitty, "--directory", cwd, bin_path]
    alacritty = _which("alacritty")
    if alacritty:
        yield [alacritty, "--working-directory", cwd, "-e", bin_path]
    wezterm = _which("wezterm")
    if wezterm:
        yield [wezterm, "start", "--cwd", cwd, "--", bin_path]
    konsole = _which("konsole")
    if konsole:
        yield [konsole, "--workdir", cwd, "-e", bin_path]
    xfce = _which("xfce4-terminal")
    if xfce:
        yield [xfce, "--working-directory=" + cwd, "-e", bin_path]
    xterm = _which("xterm")
    if xterm:
        yield [xterm, "-e", "cd %s && exec %s" % (cwd, bin_path)]
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

    ok=True only when a terminal process is actually running (or verified macOS handoff).
    """
    cwd = str(cwd)
    bin_path = str(bin_path)
    last_err = "no terminal"
    if not _has_display(env):
        return False, 0, "no DISPLAY · cannot open terminal"
    cmds = list(_terminal_cmds(bin_path, cwd))
    if not cmds:
        return False, 0, "no terminal binary on PATH"
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
            time.sleep(0.35)
            # gnome-terminal / xdg-terminal-exec often exit after spawning a child.
            # Prefer a still-alive wrapper; else accept if a window for the pid appears,
            # or if children of the session are alive (best-effort via /proc).
            if pid_alive(proc.pid):
                return True, proc.pid, ""
            # Short-lived launcher: look for child opencode or terminal window
            child = _find_alive_child(proc.pid, pid_alive)
            if child:
                return True, child, ""
            if argv and "osascript" in argv[0]:
                # macOS Terminal handoff — require activate succeeded (returncode 0)
                return True, proc.pid, ""
            # If focus finds a brand-new window for this spawn tree, accept
            if _focus_pid(proc.pid):
                return True, proc.pid, ""
            last_err = "terminal exited without enterable window"
        except OSError as e:
            last_err = str(e)[:300]
            continue
        except Exception as e:
            last_err = str(e)[:300]
            continue
    return False, 0, last_err or "terminal cannot start"


def _find_alive_child(parent_pid: int, pid_alive) -> int:
    """Best-effort: find an alive child of parent on Linux /proc."""
    try:
        parent_pid = int(parent_pid)
    except (TypeError, ValueError):
        return 0
    proc = Path("/proc")
    if not proc.is_dir():
        return 0
    try:
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            if pid == parent_pid:
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
            if ppid == parent_pid and pid_alive(pid):
                return pid
    except Exception:
        return 0
    return 0
