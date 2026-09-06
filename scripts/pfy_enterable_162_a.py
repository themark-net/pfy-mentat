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
from pathlib import Path

SESSION_REACH_OK = "terminal · OpenCode"
SESSION_FILE = "opencode-session-reach"


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
    path = Path(STATE) / SESSION_FILE
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass


def _focus_pid(pid: int) -> bool:
    """Best-effort focus an existing terminal/process window."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    # Linux: wmctrl / xdotool by pid
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
                    subprocess.run([wmctrl, "-ia", wid], capture_output=True, timeout=5, check=False)
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
                subprocess.run([xdotool, "windowactivate", wids[0]], capture_output=True, timeout=5, check=False)
                return True
        except Exception:
            pass
    return False


def _terminal_cmds(bin_path: str, cwd: str):
    """Yield argv lists to spawn a native terminal running opencode."""
    # Prefer xdg-terminal-exec when present (freedesktop)
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
        # xterm -e runs a command; use shell to cd then exec
        yield [xterm, "-e", "cd %s && exec %s" % (cwd, bin_path)]
    # macOS Terminal.app
    if sys.platform == "darwin":
        open_bin = _which("open")
        if open_bin:
            # AppleScript via osascript is more reliable for cwd+env; open -a alone lacks cwd.
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
    """Spawn native terminal running opencode. Returns (ok, pid, error)."""
    cwd = str(cwd)
    bin_path = str(bin_path)
    last_err = "no terminal"
    display = (env.get("DISPLAY") or os.environ.get("DISPLAY") or "").strip()
    wayland = (env.get("WAYLAND_DISPLAY") or os.environ.get("WAYLAND_DISPLAY") or "").strip()
    if sys.platform.startswith("linux") and not display and not wayland:
        # Still try — some terminals work headless-ish; but usually FAIL.
        last_err = "no DISPLAY · cannot open terminal"
    for argv in _terminal_cmds(bin_path, cwd):
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
            # Brief settle — terminal wrappers may re-exec
            try:
                import time
                time.sleep(0.15)
            except Exception:
                pass
            if pid_alive(proc.pid):
                return True, proc.pid, ""
            # osascript/open may exit after handing off — treat short-lived success if no crash
            if argv and "osascript" in argv[0]:
                return True, proc.pid, ""
            last_err = "terminal exited"
        except OSError as e:
            last_err = str(e)[:300]
            continue
        except Exception as e:
            last_err = str(e)[:300]
            continue
    return False, 0, last_err or "terminal cannot start"

