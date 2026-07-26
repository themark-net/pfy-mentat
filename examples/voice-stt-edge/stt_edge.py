#!/usr/bin/env python3
"""T-0091 phase 1 — voice STT edge → text prompt for Grok monitor or OpenCode worker.

Architecture (OQ-0010 path A):
  mic|audio|text  →  STT backend  →  transcript + agent-prompt  →  grok|opencode

Does NOT replace Grok/OpenCode. Does NOT require Hermes runtime.
Real Whisper is optional; smoke uses --backend mock|text without mic.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path(__file__).resolve().parent / ".generated"
FIXTURE_INTENT = Path(__file__).resolve().parent / "fixtures" / "sample_intent.txt"


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_out(out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def read_text_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        die(f"empty text file: {path}")
    return text


# --- capture -----------------------------------------------------------------


def record_mic(seconds: float, out_wav: Path) -> Path:
    """Record mono 16 kHz WAV via arecord or ffmpeg. Fail closed if neither."""
    seconds = max(0.5, float(seconds))
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    arecord = shutil.which("arecord")
    if arecord:
        cmd = [
            arecord,
            "-q",
            "-f",
            "S16_LE",
            "-r",
            "16000",
            "-c",
            "1",
            "-d",
            str(int(round(seconds))),
            str(out_wav),
        ]
        print(f"==> recording {seconds:.1f}s via arecord → {out_wav}", file=sys.stderr)
        subprocess.run(cmd, check=True)
        return out_wav

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        # pulse/default may fail in headless; still the standard host path
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "pulse",
            "-i",
            "default",
            "-t",
            str(seconds),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(out_wav),
        ]
        print(f"==> recording {seconds:.1f}s via ffmpeg/pulse → {out_wav}", file=sys.stderr)
        try:
            subprocess.run(cmd, check=True)
            return out_wav
        except subprocess.CalledProcessError:
            # try ALSA default
            cmd[cmd.index("pulse")] = "alsa"
            cmd[cmd.index("default")] = "default"
            subprocess.run(cmd, check=True)
            return out_wav

    die(
        "no mic capture tool (install arecord/alsa-utils or ffmpeg). "
        "Or pass --audio FILE.wav / --text '…' / --backend mock"
    )
    return out_wav  # unreachable


# --- STT backends ------------------------------------------------------------


def backend_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        die("--text is empty")
    return t


def backend_mock(fixture: Path | None = None) -> str:
    path = fixture or FIXTURE_INTENT
    if not path.is_file():
        die(f"mock fixture missing: {path}")
    return read_text_file(path)


def backend_openai_whisper(audio: Path, model: str = "whisper-1") -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        die("OPENAI_API_KEY required for --backend openai")
    # Prefer official SDK if present; else multipart via curl (widely available).
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=key)
        with audio.open("rb") as f:
            tr = client.audio.transcriptions.create(model=model, file=f)
        text = getattr(tr, "text", None) or str(tr)
        if not text.strip():
            die("OpenAI Whisper returned empty transcript")
        return text.strip()
    except ImportError:
        pass

    curl = shutil.which("curl")
    if not curl:
        die("need openai python package or curl for --backend openai")
    # multipart form
    cmd = [
        curl,
        "-sS",
        "https://api.openai.com/v1/audio/transcriptions",
        "-H",
        f"Authorization: Bearer {key}",
        "-F",
        f"file=@{audio}",
        "-F",
        f"model={model}",
    ]
    raw = subprocess.check_output(cmd, text=True)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die(f"OpenAI non-JSON: {raw[:200]}")
    if "error" in data:
        die(f"OpenAI Whisper error: {data['error']}")
    text = (data.get("text") or "").strip()
    if not text:
        die("OpenAI Whisper empty text")
    return text


def backend_local_whisper(audio: Path, model: str = "base") -> str:
    """openai-whisper or faster-whisper if installed."""
    # openai-whisper
    try:
        import whisper  # type: ignore

        print(f"==> local openai-whisper model={model}", file=sys.stderr)
        w = whisper.load_model(model)
        result = w.transcribe(str(audio))
        text = (result.get("text") or "").strip()
        if not text:
            die("local whisper empty transcript")
        return text
    except ImportError:
        pass

    try:
        from faster_whisper import WhisperModel  # type: ignore

        print(f"==> faster-whisper model={model}", file=sys.stderr)
        wm = WhisperModel(model, device="cpu", compute_type="int8")
        segments, _info = wm.transcribe(str(audio))
        text = " ".join(s.text.strip() for s in segments).strip()
        if not text:
            die("faster-whisper empty transcript")
        return text
    except ImportError:
        pass

    # CLI binary
    whisper_bin = shutil.which("whisper")
    if whisper_bin:
        with tempfile.TemporaryDirectory() as td:
            cmd = [
                whisper_bin,
                str(audio),
                "--model",
                model,
                "--output_dir",
                td,
                "--output_format",
                "txt",
                "--fp16",
                "False",
            ]
            print(f"==> whisper CLI model={model}", file=sys.stderr)
            subprocess.run(cmd, check=True)
            # whisper writes <stem>.txt
            txts = list(Path(td).glob("*.txt"))
            if not txts:
                die("whisper CLI produced no txt")
            return read_text_file(txts[0])

    die(
        "no local Whisper: pip install openai-whisper OR faster-whisper, "
        "or install whisper CLI, or use --backend openai|mock|text"
    )
    return ""


def backend_ollama_whisper(audio: Path, model: str | None = None) -> str:
    """Best-effort: some Ollama builds expose whisper-like models; not universal."""
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = model or os.environ.get("VOICE_STT_OLLAMA_MODEL", "whisper")
    # Ollama native audio API is evolving; try /api/generate with images-style
    # is wrong. Prefer OpenAI-compat audio if present, else fail with hint.
    url = f"{host}/v1/audio/transcriptions"
    boundary = "----pfyvoiceboundary"
    data = audio.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{audio.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + data + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"{model}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', 'ollama')}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:300]
        die(
            f"Ollama audio transcription failed ({e.code}): {err}. "
            "Install a local Whisper (openai-whisper) or use --backend openai|mock."
        )
    except Exception as e:
        die(f"Ollama unreachable or no audio API: {e}")
    try:
        data_j = json.loads(raw)
        text = (data_j.get("text") or "").strip()
    except json.JSONDecodeError:
        text = raw.strip()
    if not text:
        die("Ollama returned empty transcript")
    return text


def resolve_backend(name: str, audio: Path | None, text: str | None) -> str:
    name = (name or "auto").lower()
    if name == "text":
        if text is None and not sys.stdin.isatty():
            text = sys.stdin.read()
        return backend_text(text or "")
    if name == "mock":
        return backend_mock()
    if name == "openai":
        if not audio:
            die("--audio or --mic required for openai backend")
        return backend_openai_whisper(audio)
    if name in ("local", "whisper", "local_whisper"):
        if not audio:
            die("--audio or --mic required for local whisper")
        model = os.environ.get("VOICE_STT_WHISPER_MODEL", "base")
        return backend_local_whisper(audio, model=model)
    if name == "ollama":
        if not audio:
            die("--audio or --mic required for ollama backend")
        return backend_ollama_whisper(audio)
    if name == "auto":
        if text is not None:
            return backend_text(text)
        if not audio:
            die("auto backend needs --text, --audio, or --mic")
        # Prefer local whisper, then openai, then ollama
        for attempt in ("local", "openai", "ollama"):
            try:
                return resolve_backend(attempt, audio, None)
            except SystemExit:
                continue
            except Exception:
                continue
        die(
            "auto: no STT backend available. Install openai-whisper, set OPENAI_API_KEY, "
            "or use --backend mock|text for lab/smoke."
        )
    die(f"unknown backend: {name}")
    return ""


# --- handoff artifacts -------------------------------------------------------


def wrap_prompt(transcript: str, target: str, repo: Path) -> str:
    target = target.lower()
    role = {
        "monitor": "Grok **monitor** (subscription) — tools, GitHub, review, escalate",
        "worker": "OpenCode **worker** (local Ollama) — implement against DoD; tools may be limited",
        "raw": "raw transcript only (no role wrapper)",
    }.get(target, "agent")

    if target == "raw":
        return transcript.strip() + "\n"

    return f"""# Voice → agent prompt (T-0091 phase 1)

**Generated:** {utc_now()}  
**Target:** {role}  
**Repo:** `{repo}`  
**Source:** STT edge (`examples/voice-stt-edge`) — not Grok mobile voice (no tools there)

## Spoken intent (transcript)

{transcript.strip()}

## Operator instructions for the agent

1. Treat the transcript as the **operator's current request**.
2. You have **tools** (edit, shell, git, smokes, GitHub MCP as configured) — use them.
3. If this is a dual-session lab: honor `examples/opencode-ollama/.generated/monitor-brief.md` when present.
4. Prefer cheap local checks before cloud; stop after 3 identical failures.
5. Do **not** leave code only in chat — land changes in the repo when asked to implement.

## Suggested first moves

- Restate goal + DoD (pass/fail commands)
- If monitor: `/agent-loops plan` then let worker implement, or implement if tools-only steps
- If worker: implement against DoD; escalate tool-heavy steps to monitor when model lacks tools
"""


def write_handoff_script(
    out_dir: Path,
    repo: Path,
    target: str,
    transcript_path: Path,
    prompt_path: Path,
) -> Path:
    path = out_dir / "handoff.sh"
    mon_brief = repo / "examples/opencode-ollama/.generated/monitor-brief.md"
    worker_env = repo / "examples/opencode-ollama/.generated/worker.env"
    worker_cfg = repo / "examples/opencode-ollama/.generated/opencode.json"

    body = f"""#!/usr/bin/env bash
# Generated by voice-stt-edge — launch tool-capable agent with STT transcript
set -euo pipefail
ROOT={repo!s}
cd "$ROOT"
TRANSCRIPT={transcript_path!s}
PROMPT={prompt_path!s}
TARGET={target}

echo "== voice handoff (T-0091 p1) =="
echo "  target=$TARGET"
echo "  transcript=$TRANSCRIPT"
echo ""
echo "--- transcript ---"
cat "$TRANSCRIPT"
echo "------------------"
echo ""

case "$TARGET" in
  monitor|raw)
    if command -v grok >/dev/null 2>&1; then
      echo "Launching: grok \\"$(head -c 80 "$TRANSCRIPT")…\\""
      # Full wrapped prompt as initial message (tools available in Grok CLI)
      exec grok "$(cat "$PROMPT")"
    else
      echo "grok not on PATH. Paste this into Grok Build / Grok CLI:"
      echo "  $PROMPT"
      exit 0
    fi
    ;;
  worker)
    if [[ -f {worker_env!s} ]]; then
      set -a; # shellcheck disable=SC1091
      . {worker_env!s}
      set +a
    fi
    export OPENCODE_CONFIG="${{OPENCODE_CONFIG:-{worker_cfg!s}}}"
    if command -v opencode >/dev/null 2>&1; then
      echo "OpenCode worker: paste or pass prompt from:"
      echo "  $PROMPT"
      echo "Starting opencode (interactive)…"
      exec opencode
    else
      echo "opencode not on PATH. Install OpenCode, then:"
      echo "  set -a; . {worker_env!s}; set +a"
      echo "  opencode"
      echo "Paste: $PROMPT"
      exit 0
    fi
    ;;
  *)
    echo "unknown TARGET=$TARGET" >&2
    exit 1
    ;;
esac
"""
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    # note mon_brief for operators in meta only
    _ = mon_brief
    return path


def write_meta(
    out_dir: Path,
    *,
    backend: str,
    target: str,
    transcript: str,
    audio: str | None,
) -> Path:
    meta = {
        "generated": utc_now(),
        "backend": backend,
        "target": target,
        "audio": audio,
        "transcript_chars": len(transcript),
        "transcript_preview": transcript[:200],
        "phase": "T-0091-p1",
    }
    path = out_dir / "last-meta.json"
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Voice STT edge → text prompt for Grok monitor / OpenCode worker (T-0091 p1)"
    )
    p.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "mock", "text", "openai", "local", "whisper", "local_whisper", "ollama"],
        help="STT backend (default auto). mock/text need no Whisper install.",
    )
    p.add_argument("--audio", type=Path, help="Audio file (wav/mp3/m4a/…)")
    p.add_argument("--mic", action="store_true", help="Record from default mic")
    p.add_argument("--seconds", type=float, default=5.0, help="Mic record length (default 5)")
    p.add_argument("--text", help="Skip STT; use this text as transcript")
    p.add_argument(
        "--target",
        default="monitor",
        choices=["monitor", "worker", "raw"],
        help="Wrap prompt for monitor (Grok) or worker (OpenCode)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT,
        help="Output directory for transcript/prompt/handoff",
    )
    p.add_argument(
        "--print-only",
        action="store_true",
        help="Print transcript to stdout only (still writes files unless --no-write)",
    )
    p.add_argument("--no-write", action="store_true", help="Do not write .generated artifacts")
    p.add_argument(
        "--handoff",
        action="store_true",
        help="Exec handoff.sh after write (launch grok/opencode)",
    )
    args = p.parse_args(argv)

    audio_path: Path | None = args.audio
    backend = args.backend
    if args.mic:
        out_dir = ensure_out(args.out_dir)
        audio_path = out_dir / "last-capture.wav"
        record_mic(args.seconds, audio_path)
        if backend == "auto":
            backend = "auto"  # will pick STT for audio

    if args.text is not None and backend == "auto":
        backend = "text"
    if backend == "mock" and args.text is None and audio_path is None:
        pass  # fixture only
    if backend not in ("mock", "text") and audio_path is None and args.text is None:
        die("provide --audio, --mic, --text, or --backend mock")

    if audio_path is not None and not audio_path.is_file():
        die(f"audio not found: {audio_path}")

    transcript = resolve_backend(backend, audio_path, args.text)

    if not args.no_write:
        out_dir = ensure_out(args.out_dir)
        t_path = out_dir / "last-transcript.txt"
        p_path = out_dir / "agent-prompt.md"
        t_path.write_text(transcript.strip() + "\n", encoding="utf-8")
        p_path.write_text(wrap_prompt(transcript, args.target, ROOT), encoding="utf-8")
        h_path = write_handoff_script(out_dir, ROOT, args.target, t_path, p_path)
        write_meta(
            out_dir,
            backend=backend,
            target=args.target,
            transcript=transcript,
            audio=str(audio_path) if audio_path else None,
        )
        print(f"==> wrote {t_path}", file=sys.stderr)
        print(f"==> wrote {p_path}", file=sys.stderr)
        print(f"==> wrote {h_path}", file=sys.stderr)
        print(
            f"Handoff:  {h_path}\n"
            f"  or:     grok \"$(cat {t_path})\"\n"
            f"  or:     paste {p_path} into Grok / OpenCode",
            file=sys.stderr,
        )
        if args.handoff:
            os.execv(str(h_path), [str(h_path)])

    # stdout = clean transcript for piping
    sys.stdout.write(transcript.strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
