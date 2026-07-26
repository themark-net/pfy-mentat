#!/usr/bin/env python3
"""T-0091 phase 1 — voice STT edge → text prompt for Grok monitor or OpenCode worker.

Architecture (OQ-0010 path A):
  mic|audio|text  →  STT backend  →  transcript + agent-prompt  →  grok|opencode

Does NOT replace Grok/OpenCode. Does NOT require Hermes runtime.

Lab smoke uses --backend mock|text (no mic, no Whisper).
Real mic needs a STT backend: `make voice-stt-install` then `make voice-listen`.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import wave
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path(__file__).resolve().parent / ".generated"
FIXTURE_INTENT = Path(__file__).resolve().parent / "fixtures" / "sample_intent.txt"
EDGE_DIR = Path(__file__).resolve().parent


class SttError(Exception):
    """Recoverable STT/backend failure (no process exit)."""


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
        raise SttError(f"empty text file: {path}")
    return text


def install_hint() -> str:
    return (
        "Real STT is not installed (smoke does not record audio).\n"
        "  1) make voice-stt-install          # creates .venv + faster-whisper (PEP 668 safe)\n"
        "  2) make voice-listen              # mic → transcript → handoff artifacts\n"
        "  or: OPENAI_API_KEY=… examples/voice-stt-edge/python.sh "
        "examples/voice-stt-edge/stt_edge.py --mic --backend openai --target monitor\n"
        "If you already recorded: re-run on the wav (no re-record):\n"
        "  examples/voice-stt-edge/python.sh examples/voice-stt-edge/stt_edge.py "
        "--audio examples/voice-stt-edge/.generated/last-capture.wav "
        "--backend local --target monitor\n"
        "Do not: pip install --user into system Python (PEP 668 / Debian blocks it)."
    )


# --- capture -----------------------------------------------------------------


def wav_stats(path: Path) -> dict:
    """Peak/RMS diagnostics for PCM WAV (silence detection)."""
    stats: dict = {
        "path": str(path),
        "bytes": path.stat().st_size if path.is_file() else 0,
        "ok": False,
        "near_silent": True,
        "peak": 0,
        "rms": 0.0,
        "duration_s": 0.0,
        "rate": 0,
        "channels": 0,
        "sampwidth": 0,
    }
    try:
        with wave.open(str(path), "rb") as w:
            nch, sw, rate, nframes = (
                w.getnchannels(),
                w.getsampwidth(),
                w.getframerate(),
                w.getnframes(),
            )
            raw = w.readframes(nframes)
            stats.update(
                {
                    "rate": rate,
                    "channels": nch,
                    "sampwidth": sw,
                    "duration_s": (nframes / rate) if rate else 0.0,
                    "nframes": nframes,
                }
            )
            if sw == 2 and raw:
                n = len(raw) // 2
                samples = struct.unpack("<" + "h" * n, raw)
                peak = max(abs(s) for s in samples) if samples else 0
                mean_sq = sum(s * s for s in samples) / max(1, len(samples))
                rms = math.sqrt(mean_sq)
                # int16 full scale 32767; speech often peak >> 1000
                stats["peak"] = peak
                stats["rms"] = round(rms, 1)
                stats["near_silent"] = peak < 800 and rms < 200
                stats["ok"] = True
            elif sw == 1 and raw:
                samples = list(raw)
                peak = max(abs(s - 128) for s in samples) if samples else 0
                stats["peak"] = peak
                stats["near_silent"] = peak < 8
                stats["ok"] = True
    except Exception as e:
        stats["error"] = str(e)
    return stats


def print_wav_stats(stats: dict) -> None:
    print(
        f"==> audio: {stats.get('duration_s', 0):.1f}s "
        f"{stats.get('rate')}Hz ch={stats.get('channels')} "
        f"peak={stats.get('peak')} rms={stats.get('rms')} "
        f"{'NEAR-SILENT' if stats.get('near_silent') else 'has-energy'}",
        file=sys.stderr,
    )


def record_mic(seconds: float, out_wav: Path) -> Path:
    """Record mono 16 kHz WAV via arecord or ffmpeg. Fail closed if neither."""
    seconds = max(0.5, float(seconds))
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    device = os.environ.get("VOICE_ARECORD_DEVICE", "").strip()

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
        ]
        if device:
            cmd.extend(["-D", device])
            print(f"==> arecord device={device}", file=sys.stderr)
        cmd.append(str(out_wav))
        print(f"==> recording {seconds:.1f}s via arecord → {out_wav}", file=sys.stderr)
        print("    Speak now (clear, close to mic)…", file=sys.stderr)
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise SttError(f"arecord failed (exit {e.returncode})") from e
        if not out_wav.is_file() or out_wav.stat().st_size < 100:
            raise SttError(f"arecord produced empty/missing wav: {out_wav}")
        print(
            f"==> captured {out_wav.stat().st_size} bytes "
            f"(STT still required — not transcribed yet)",
            file=sys.stderr,
        )
        st = wav_stats(out_wav)
        print_wav_stats(st)
        if st.get("near_silent"):
            print(
                "==> warning: capture looks near-silent. "
                "Try: longer VOICE_LISTEN_SECONDS, closer mic, "
                "or VOICE_ARECORD_DEVICE=… (see arecord -l / pactl list short sources)",
                file=sys.stderr,
            )
        return out_wav

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        print(f"==> recording {seconds:.1f}s via ffmpeg → {out_wav}", file=sys.stderr)
        for audio_fmt, device in (("pulse", "default"), ("alsa", "default")):
            cmd = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                audio_fmt,
                "-i",
                device,
                "-t",
                str(seconds),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(out_wav),
            ]
            try:
                subprocess.run(cmd, check=True)
                if out_wav.is_file() and out_wav.stat().st_size >= 100:
                    print(
                        f"==> captured {out_wav.stat().st_size} bytes via ffmpeg/{audio_fmt}",
                        file=sys.stderr,
                    )
                    return out_wav
            except subprocess.CalledProcessError:
                continue
        raise SttError("ffmpeg could not capture from pulse/alsa default")

    raise SttError(
        "no mic capture tool (install arecord/alsa-utils or ffmpeg). "
        "Or pass --audio FILE.wav / --text '…' / --backend mock"
    )


# --- capability probes -------------------------------------------------------


def has_openai_whisper_pkg() -> bool:
    try:
        import whisper  # noqa: F401

        return True
    except ImportError:
        return False


def has_faster_whisper() -> bool:
    try:
        import faster_whisper  # noqa: F401

        return True
    except ImportError:
        return False


def has_whisper_cli() -> bool:
    return shutil.which("whisper") is not None


def has_local_stt() -> bool:
    return has_openai_whisper_pkg() or has_faster_whisper() or has_whisper_cli()


def has_openai_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def probe_report() -> list[str]:
    lines = [
        f"  local faster-whisper: {'yes' if has_faster_whisper() else 'no'}",
        f"  local openai-whisper: {'yes' if has_openai_whisper_pkg() else 'no'}",
        f"  whisper CLI:          {'yes' if has_whisper_cli() else 'no'}",
        f"  OPENAI_API_KEY:       {'yes' if has_openai_key() else 'no'}",
        f"  arecord:              {'yes' if shutil.which('arecord') else 'no'}",
        f"  ffmpeg:               {'yes' if shutil.which('ffmpeg') else 'no'}",
    ]
    return lines


# --- STT backends ------------------------------------------------------------


def backend_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        raise SttError("--text is empty")
    return t


def backend_mock(fixture: Path | None = None) -> str:
    path = fixture or FIXTURE_INTENT
    if not path.is_file():
        raise SttError(f"mock fixture missing: {path}")
    return read_text_file(path)


def backend_openai_whisper(audio: Path, model: str = "whisper-1") -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise SttError("OPENAI_API_KEY required for --backend openai")
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=key)
        with audio.open("rb") as f:
            tr = client.audio.transcriptions.create(model=model, file=f)
        text = getattr(tr, "text", None) or str(tr)
        if not text.strip():
            raise SttError("OpenAI Whisper returned empty transcript")
        return text.strip()
    except ImportError:
        pass
    except Exception as e:
        raise SttError(f"OpenAI Whisper SDK failed: {e}") from e

    curl = shutil.which("curl")
    if not curl:
        raise SttError("need openai python package or curl for --backend openai")
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
    try:
        raw = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as e:
        raise SttError(f"OpenAI curl transcription failed: {e}") from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise SttError(f"OpenAI non-JSON: {raw[:200]}") from e
    if "error" in data:
        raise SttError(f"OpenAI Whisper error: {data['error']}")
    text = (data.get("text") or "").strip()
    if not text:
        raise SttError("OpenAI Whisper empty text")
    return text


def _empty_transcript_error(audio: Path, detail: str) -> SttError:
    st = wav_stats(audio)
    print_wav_stats(st)
    if st.get("near_silent"):
        return SttError(
            f"{detail}: audio is near-silent (peak={st.get('peak')} rms={st.get('rms')}). "
            "Mic likely wrong device or muted. Try:\n"
            "  arecord -l\n"
            "  pactl list short sources\n"
            "  VOICE_ARECORD_DEVICE=default make voice-listen\n"
            "  VOICE_LISTEN_SECONDS=8 make voice-listen   # speak louder, whole window\n"
            f"  Re-check file: {audio}"
        )
    return SttError(
        f"{detail}: non-silent audio but no text decoded. "
        "Retry with: VOICE_STT_WHISPER_MODEL=small.en make voice-listen\n"
        f"  or: examples/voice-stt-edge/python.sh …/stt_edge.py --audio {audio} "
        "--backend local --target monitor\n"
        "  Speak a full English phrase during the whole recording window."
    )


def _faster_whisper_once(
    audio: Path,
    model: str,
    *,
    language: str,
    vad_filter: bool,
    no_speech_threshold: float,
    compute_type: str,
) -> tuple[str, object]:
    from faster_whisper import WhisperModel  # type: ignore

    print(
        f"==> faster-whisper model={model} compute={compute_type} "
        f"lang={language} vad={vad_filter} no_speech_th={no_speech_threshold}",
        file=sys.stderr,
    )
    wm = WhisperModel(model, device="cpu", compute_type=compute_type)
    segments, info = wm.transcribe(
        str(audio),
        language=language or None,
        task="transcribe",
        beam_size=5,
        best_of=5,
        temperature=0.0,
        vad_filter=vad_filter,
        condition_on_previous_text=False,
        no_speech_threshold=no_speech_threshold,
        log_prob_threshold=-1.0,
        compression_ratio_threshold=2.4,
        word_timestamps=False,
    )
    segs = list(segments)
    text = " ".join(s.text.strip() for s in segs if s.text).strip()
    # helpful diagnostics
    dur = getattr(info, "duration", None)
    lang = getattr(info, "language", None)
    prob = getattr(info, "language_probability", None)
    print(
        f"==> decode: segments={len(segs)} duration={dur} lang={lang} lang_p={prob} "
        f"chars={len(text)}",
        file=sys.stderr,
    )
    return text, info


def backend_local_whisper(audio: Path, model: str = "base.en") -> str:
    """openai-whisper or faster-whisper if installed."""
    lang = os.environ.get("VOICE_STT_LANGUAGE", "en").strip() or "en"
    st = wav_stats(audio)
    if st.get("ok"):
        print_wav_stats(st)

    if has_openai_whisper_pkg():
        import whisper  # type: ignore

        print(f"==> local openai-whisper model={model}", file=sys.stderr)
        w = whisper.load_model(model)
        result = w.transcribe(str(audio), language=lang, fp16=False)
        text = (result.get("text") or "").strip()
        if not text:
            raise _empty_transcript_error(audio, "openai-whisper empty transcript")
        return text

    if has_faster_whisper():
        # Prefer English-tuned small models for short operator commands
        models_to_try = [model]
        for alt in ("base.en", "tiny.en", "base", "tiny"):
            if alt not in models_to_try:
                models_to_try.append(alt)

        attempts: list[tuple[str, bool, float, str]] = []
        # (model, vad_filter, no_speech_threshold, compute_type)
        for m in models_to_try[:3]:
            attempts.append((m, False, 0.6, "int8"))
            attempts.append((m, False, 0.3, "int8"))  # more willing to decode speech
            attempts.append((m, True, 0.5, "int8"))  # VAD can help noisy rooms
            attempts.append((m, False, 0.3, "float32"))  # if int8 misbehaves

        last_err = "faster-whisper empty transcript"
        seen: set[tuple] = set()
        for m, vad, nst, ctype in attempts:
            key = (m, vad, nst, ctype)
            if key in seen:
                continue
            seen.add(key)
            try:
                text, _info = _faster_whisper_once(
                    audio,
                    m,
                    language=lang,
                    vad_filter=vad,
                    no_speech_threshold=nst,
                    compute_type=ctype,
                )
            except Exception as e:
                last_err = f"faster-whisper error ({m}/{ctype}): {e}"
                print(f"==> {last_err}", file=sys.stderr)
                continue
            if text:
                print(f"==> transcript ok via model={m} vad={vad}", file=sys.stderr)
                return text

        raise _empty_transcript_error(audio, last_err)

    whisper_bin = shutil.which("whisper")
    if whisper_bin:
        with tempfile.TemporaryDirectory() as td:
            cmd = [
                whisper_bin,
                str(audio),
                "--model",
                model,
                "--language",
                lang,
                "--output_dir",
                td,
                "--output_format",
                "txt",
                "--fp16",
                "False",
            ]
            print(f"==> whisper CLI model={model}", file=sys.stderr)
            subprocess.run(cmd, check=True)
            txts = list(Path(td).glob("*.txt"))
            if not txts:
                raise SttError("whisper CLI produced no txt")
            text = read_text_file(txts[0])
            if not text:
                raise _empty_transcript_error(audio, "whisper CLI empty transcript")
            return text

    raise SttError(
        "no local Whisper in this Python. Run: make voice-stt-install  "
        "(creates examples/voice-stt-edge/.venv with faster-whisper). "
        "Then use: make voice-listen  or  examples/voice-stt-edge/python.sh …"
    )


def backend_ollama_whisper(audio: Path, model: str | None = None) -> str:
    """Best-effort OpenAI-compat audio on Ollama (often 404 — not a default path)."""
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = model or os.environ.get("VOICE_STT_OLLAMA_MODEL", "whisper")
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
        raise SttError(
            f"Ollama audio API {e.code} for model {model!r}: {err}. "
            "Prefer: make voice-stt-install (faster-whisper)."
        ) from e
    except Exception as e:
        raise SttError(f"Ollama unreachable or no audio API: {e}") from e
    try:
        data_j = json.loads(raw)
        text = (data_j.get("text") or "").strip()
    except json.JSONDecodeError:
        text = raw.strip()
    if not text:
        raise SttError("Ollama returned empty transcript")
    return text


def resolve_backend(name: str, audio: Path | None, text: str | None) -> tuple[str, str]:
    """Return (backend_used, transcript). Raises SttError."""
    name = (name or "auto").lower()
    if name == "text":
        if text is None and not sys.stdin.isatty():
            text = sys.stdin.read()
        return "text", backend_text(text or "")
    if name == "mock":
        return "mock", backend_mock()
    if name == "openai":
        if not audio:
            raise SttError("--audio or --mic required for openai backend")
        return "openai", backend_openai_whisper(audio)
    if name in ("local", "whisper", "local_whisper"):
        if not audio:
            raise SttError("--audio or --mic required for local whisper")
        # base.en is better default for short English operator commands
        model = os.environ.get("VOICE_STT_WHISPER_MODEL", "base.en")
        return "local", backend_local_whisper(audio, model=model)
    if name == "ollama":
        if not audio:
            raise SttError("--audio or --mic required for ollama backend")
        return "ollama", backend_ollama_whisper(audio)
    if name == "auto":
        if text is not None:
            return "text", backend_text(text)
        if not audio:
            raise SttError("auto backend needs --text, --audio, or --mic")
        # Probe first — avoid error spam. Ollama only if explicitly opted in
        # (default Ollama installs have no whisper model → noisy 404s).
        attempts: list[tuple[str, str]] = []
        if has_local_stt():
            attempts.append(("local", "local Whisper (faster-whisper / openai-whisper)"))
        if has_openai_key():
            attempts.append(("openai", "OpenAI Whisper API"))
        if os.environ.get("VOICE_STT_TRY_OLLAMA", "").strip() in ("1", "true", "yes"):
            attempts.append(("ollama", "Ollama audio API"))

        errors: list[str] = []
        for bname, label in attempts:
            try:
                used, tr = resolve_backend(bname, audio, None)
                print(f"==> STT backend: {used} ({label})", file=sys.stderr)
                return used, tr
            except SttError as e:
                errors.append(f"{bname}: {e}")
                continue

        if not attempts:
            raise SttError(
                "no STT backend available.\n"
                + "\n".join(probe_report())
                + "\n"
                + install_hint()
            )

        # Prefer the local empty-transcript diagnosis over generic install hint
        detail = "\n".join(f"  - {e}" for e in errors)
        primary = errors[0] if errors else "unknown"
        # If local already explained silence / decode, surface that first
        if "near-silent" in primary or "non-silent" in primary or "empty" in primary:
            raise SttError(primary)
        raise SttError(
            "no working STT backend for this audio.\n"
            f"Probes:\n" + "\n".join(probe_report()) + "\n"
            f"Attempts:\n{detail}\n"
            f"{install_hint()}"
        )
    raise SttError(f"unknown backend: {name}")


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


def write_blocked_handoff(out_dir: Path, reason: str, audio: Path | None) -> Path:
    """Replace handoff.sh so a failed STT cannot re-launch stale 'ping' sessions."""
    path = out_dir / "handoff.sh"
    audio_s = str(audio) if audio else "(none)"
    body = f"""#!/usr/bin/env bash
# BLOCKED — last voice capture did not produce a fresh transcript
set -euo pipefail
echo "error: handoff blocked — no successful STT since last capture" >&2
echo "  reason: {reason[:200]}" >&2
echo "  audio:  {audio_s}" >&2
echo "" >&2
echo "Fix:" >&2
echo "  make voice-stt-install" >&2
echo "  python3 examples/voice-stt-edge/stt_edge.py --audio {audio_s} --backend local --target monitor" >&2
echo "  # then re-run this handoff.sh" >&2
exit 2
"""
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)
    note = out_dir / "STT-NEEDED.txt"
    note.write_text(
        f"Recorded audio but STT failed at {utc_now()}.\n\n{reason}\n\n{install_hint()}\n",
        encoding="utf-8",
    )
    return path


def write_handoff_script(
    out_dir: Path,
    repo: Path,
    target: str,
    transcript_path: Path,
    prompt_path: Path,
) -> Path:
    path = out_dir / "handoff.sh"
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

if [[ ! -s "$TRANSCRIPT" ]]; then
  echo "error: empty transcript at $TRANSCRIPT" >&2
  exit 2
fi

# Refuse smoke leftovers if operator expects voice
if grep -qx 'ping' "$TRANSCRIPT" 2>/dev/null; then
  echo "warning: transcript is exactly 'ping' (often from smoke raw-target leftover)" >&2
  echo "  If you just used --mic, STT probably failed earlier; see STT-NEEDED.txt" >&2
fi

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
      echo "Launching: grok with agent-prompt.md (tools enabled in CLI)"
      exec grok "$(cat "$PROMPT")"
    else
      echo "grok not on PATH. Paste this into Grok Build / Grok CLI:"
      echo "  $PROMPT"
      exit 0
    fi
    ;;
  worker)
    if [[ -f {worker_env!s} ]]; then
      set -a
      # shellcheck disable=SC1091
      . {worker_env!s}
      set +a
    fi
    export OPENCODE_CONFIG="${{OPENCODE_CONFIG:-{worker_cfg!s}}}"
    if command -v opencode >/dev/null 2>&1; then
      echo "OpenCode worker: starting interactive session."
      echo "Paste or attach prompt from: $PROMPT"
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
    return path


def write_meta(
    out_dir: Path,
    *,
    backend: str,
    target: str,
    transcript: str,
    audio: str | None,
    ok: bool = True,
    source: str = "local",
) -> Path:
    meta = {
        "generated": utc_now(),
        "ok": ok,
        "backend": backend,
        "target": target,
        "audio": audio,
        "transcript_chars": len(transcript),
        "transcript_preview": transcript[:200],
        "phase": "T-0091",
        "source": source,
    }
    path = out_dir / "last-meta.json"
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return path


def persist_success(
    out_dir: Path,
    *,
    transcript: str,
    target: str,
    backend: str,
    audio: Path | None = None,
    source: str = "local",
    repo: Path | None = None,
) -> dict:
    """Write transcript + agent-prompt + handoff + meta. Returns paths dict."""
    repo = repo or ROOT
    out_dir = ensure_out(out_dir)
    t_path = out_dir / "last-transcript.txt"
    p_path = out_dir / "agent-prompt.md"
    t_path.write_text(transcript.strip() + "\n", encoding="utf-8")
    p_path.write_text(wrap_prompt(transcript, target, repo), encoding="utf-8")
    h_path = write_handoff_script(out_dir, repo, target, t_path, p_path)
    write_meta(
        out_dir,
        backend=backend,
        target=target,
        transcript=transcript,
        audio=str(audio) if audio else None,
        ok=True,
        source=source,
    )
    needed = out_dir / "STT-NEEDED.txt"
    if needed.is_file():
        needed.unlink()

    # Inbox copy for remote / multi-shot history (gitignored under .generated)
    inbox = out_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in transcript.strip()[:40])
    item = inbox / f"{stamp}_{safe or 'prompt'}.md"
    item.write_text(
        f"# Voice inbox item\n\n"
        f"- **When:** {utc_now()}\n"
        f"- **Source:** {source}\n"
        f"- **Target:** {target}\n"
        f"- **Backend:** {backend}\n\n"
        f"## Transcript\n\n{transcript.strip()}\n\n"
        f"## Agent prompt\n\n"
        f"(see also agent-prompt.md)\n\n"
        f"{wrap_prompt(transcript, target, repo)}\n",
        encoding="utf-8",
    )
    return {
        "transcript_path": str(t_path),
        "prompt_path": str(p_path),
        "handoff_path": str(h_path),
        "inbox_path": str(item),
        "transcript": transcript.strip(),
        "target": target,
        "backend": backend,
        "source": source,
    }


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
    p.add_argument("--no-write", action="store_true", help="Do not write .generated artifacts")
    p.add_argument(
        "--handoff",
        action="store_true",
        help="Exec handoff.sh after write (launch grok/opencode)",
    )
    p.add_argument(
        "--probe",
        action="store_true",
        help="Print STT capability probe and exit 0 if any real STT ready, else 2",
    )
    args = p.parse_args(argv)

    if args.probe:
        print("== voice-stt-edge probe ==")
        for line in probe_report():
            print(line)
        ready = has_local_stt() or has_openai_key()
        if ready:
            print("  ready: yes (local and/or OpenAI)")
            return 0
        print("  ready: no")
        print(install_hint())
        return 2

    audio_path: Path | None = args.audio
    backend = args.backend
    out_dir = ensure_out(args.out_dir)

    try:
        if args.mic:
            audio_path = out_dir / "last-capture.wav"
            record_mic(args.seconds, audio_path)

        if args.text is not None and backend == "auto":
            backend = "text"
        if backend not in ("mock", "text") and audio_path is None and args.text is None:
            raise SttError("provide --audio, --mic, --text, or --backend mock")

        if audio_path is not None and not audio_path.is_file():
            raise SttError(f"audio not found: {audio_path}")

        used, transcript = resolve_backend(backend, audio_path, args.text)
    except SttError as e:
        msg = str(e)
        print(f"error: {msg}", file=sys.stderr)
        if not args.no_write and (args.mic or audio_path):
            write_blocked_handoff(out_dir, msg.split("\n")[0], audio_path)
            write_meta(
                out_dir,
                backend=backend,
                target=args.target,
                transcript="",
                audio=str(audio_path) if audio_path else None,
                ok=False,
            )
            print(f"==> wrote {out_dir / 'STT-NEEDED.txt'}", file=sys.stderr)
            print(
                "==> handoff.sh blocked until STT succeeds "
                "(will not re-launch stale smoke 'ping')",
                file=sys.stderr,
            )
        return 1

    if not args.no_write:
        paths = persist_success(
            out_dir,
            transcript=transcript,
            target=args.target,
            backend=used,
            audio=audio_path,
            source="local",
        )
        print(f"==> wrote {paths['transcript_path']}", file=sys.stderr)
        print(f"==> wrote {paths['prompt_path']}", file=sys.stderr)
        print(f"==> wrote {paths['handoff_path']}", file=sys.stderr)
        print(f"==> inbox {paths['inbox_path']}", file=sys.stderr)
        print(
            f"Handoff:  {paths['handoff_path']}\n"
            f"  or:     grok \"$(cat {paths['prompt_path']})\"\n"
            f"  or:     paste {paths['prompt_path']} into Grok / OpenCode",
            file=sys.stderr,
        )
        if args.handoff:
            os.execv(str(paths["handoff_path"]), [str(paths["handoff_path"])])

    sys.stdout.write(transcript.strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
