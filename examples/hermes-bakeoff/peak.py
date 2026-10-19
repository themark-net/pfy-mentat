"""Sample VmHWM / RSS of one process tree every 0.5s.

Ollama processes are reported separately and are not added to the agent peak.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path


def _status(pid: int) -> dict[str, int]:
    text = Path(f"/proc/{pid}/status").read_text(encoding="utf-8", errors="replace")
    out: dict[str, int] = {}
    for key in ("VmRSS", "VmHWM", "PPid"):
        for line in text.splitlines():
            if line.startswith(key + ":"):
                out[key] = int(line.split()[1])
                break
    return out


def _cmdline(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\x00", b" ").decode("utf-8", "replace")


def _is_ollama(pid: int) -> bool:
    cmd = _cmdline(pid)
    return "ollama" in cmd.split(" ")[0] or "/ollama" in cmd or cmd.startswith("ollama")


def _children_map() -> dict[int, list[int]]:
    kids: dict[int, list[int]] = {}
    proc = Path("/proc")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            info = _status(pid)
        except OSError:
            continue
        ppid = info.get("PPid")
        if ppid is None:
            continue
        kids.setdefault(ppid, []).append(pid)
    return kids


def tree_pids(root: int) -> list[int]:
    kids = _children_map()
    seen = []
    stack = [root]
    guard = {root}
    while stack:
        pid = stack.pop()
        seen.append(pid)
        for child in kids.get(pid, []):
            if child not in guard:
                guard.add(child)
                stack.append(child)
    return seen


class PeakSampler:
    def __init__(self, root_pid: int, interval: float = 0.5):
        self.root_pid = root_pid
        self.interval = interval
        self.peak_hwm_kib = 0
        self.peak_tree_rss_kib = 0
        self.ollama_peak_rss_kib = 0
        self.samples = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop.is_set():
            self.samples += 1
            try:
                pids = tree_pids(self.root_pid)
            except OSError:
                pids = []
            tree_rss = 0
            for pid in pids:
                if _is_ollama(pid):
                    continue
                try:
                    info = _status(pid)
                except OSError:
                    continue
                tree_rss += info.get("VmRSS", 0)
                self.peak_hwm_kib = max(self.peak_hwm_kib, info.get("VmHWM", 0))
            self.peak_tree_rss_kib = max(self.peak_tree_rss_kib, tree_rss)
            self._sample_ollama()
            self._stop.wait(self.interval)

    def _sample_ollama(self) -> None:
        proc = Path("/proc")
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            pid = int(entry.name)
            if not _is_ollama(pid):
                continue
            try:
                info = _status(pid)
            except OSError:
                continue
            self.ollama_peak_rss_kib = max(self.ollama_peak_rss_kib, info.get("VmRSS", 0))

    def summary(self) -> dict:
        agent_kib = max(self.peak_hwm_kib, self.peak_tree_rss_kib)
        return {
            "agent_peak_rss_bytes": agent_kib * 1024,
            "agent_peak_hwm_kib": self.peak_hwm_kib,
            "agent_peak_tree_rss_kib": self.peak_tree_rss_kib,
            "ollama_peak_rss_bytes": self.ollama_peak_rss_kib * 1024,
            "samples": self.samples,
        }


def sample_once_for_tests(pid: int) -> dict:
    """One immediate sample. Used by nothing in the live path; kept for the sampler math."""
    sampler = PeakSampler(pid, interval=0.05)
    sampler._run_once = True  # type: ignore[attr-defined]
    # Do a single iteration inline.
    info = _status(pid)
    return {"VmRSS": info.get("VmRSS", 0), "VmHWM": info.get("VmHWM", 0)}


# silence unused in case a linter cares; time is used by the wait
_ = time
