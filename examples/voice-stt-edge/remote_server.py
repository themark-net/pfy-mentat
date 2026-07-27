#!/usr/bin/env python3
"""T-0091 phase 4a/4b — remote voice edge for Android / Tailscale.

Listens on HTTP (default 127.0.0.1:8787). Phone browser records audio → STT
on this host → agent-prompt artifacts; optional auto agent (4b).

VOICE_AUTO_AGENT=1|opencode|mock|grok → after STT, run agent (1/opencode=local; grok=escalate).
Default off so remote open does not auto-spend cloud.

Security:
  - Requires VOICE_REMOTE_TOKEN (or --token) on every mutating request
  - Default bind 127.0.0.1 (not public internet)
  - For remote Android: Tailscale (recommended) then bind 0.0.0.0 or 100.x
  - Does NOT auto-open the public internet; does NOT disable cage policy

Not: Grok mobile voice (no tools). Not: Hermes primary runtime.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import secrets
import socket
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Allow `python remote_server.py` from any cwd
EDGE = Path(__file__).resolve().parent
sys.path.insert(0, str(EDGE))

import agent_runner as ar  # noqa: E402
import stt_edge as se  # noqa: E402

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_OUT = EDGE / ".generated"


MOBILE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
  <title>pfy voice → agent</title>
  <style>
    :root { color-scheme: dark light; font-family: system-ui, sans-serif; }
    body { margin: 0; padding: 1rem; max-width: 40rem; margin-inline: auto; }
    h1 { font-size: 1.25rem; margin: 0 0 .5rem; }
    .sub { opacity: .75; font-size: .9rem; margin-bottom: 1rem; }
    label { display: block; font-size: .85rem; margin: .75rem 0 .25rem; }
    input, select, button, textarea {
      width: 100%; box-sizing: border-box; font: inherit; padding: .65rem .75rem;
      border-radius: .5rem; border: 1px solid #6664;
    }
    button { cursor: pointer; font-weight: 600; margin-top: .5rem; }
    button.rec { background: #c62828; color: #fff; border: none; }
    button.rec.on { animation: pulse 1s infinite; }
    button.rec:disabled { opacity: .45; }
    button.go { background: #1565c0; color: #fff; border: none; }
    button.secondary { background: transparent; }
    #banner {
      display: none; font-size: .85rem; margin: 0 0 1rem; padding: .75rem;
      border-radius: .5rem; background: #b71c1c22; border: 1px solid #c62828aa;
    }
    #banner.show { display: block; }
    #status { white-space: pre-wrap; font-size: .85rem; margin-top: 1rem;
      padding: .75rem; border-radius: .5rem; background: #8881; min-height: 3rem; }
    #result {
      display: none; margin-top: 1rem; padding: 1rem; border-radius: .5rem;
      background: #1b5e2033; border: 2px solid #2e7d32; white-space: pre-wrap;
      font-size: 1.05rem; font-weight: 600;
    }
    #result.show { display: block; }
    #result .meta { font-weight: 400; font-size: .8rem; opacity: .8; margin-top: .75rem; }
    @keyframes pulse { 50% { opacity: .7; } }
    .row { display: flex; gap: .5rem; }
    .row > * { flex: 1; }
    code { font-size: .8rem; word-break: break-all; }
  </style>
</head>
<body>
  <h1>Voice → tool-capable agent</h1>
  <p class="sub">Phone → host STT → Grok/OpenCode tools (not Grok mobile voice).</p>

  <div id="banner"></div>

  <label>Token (VOICE_REMOTE_TOKEN)</label>
  <input id="token" type="password" autocomplete="off" placeholder="required"/>

  <label>Target</label>
  <select id="target">
    <option value="worker" selected>worker (OpenCode/Ollama — local default)</option>
    <option value="monitor">monitor (Grok escalate)</option>
    <option value="raw">raw transcript</option>
  </select>

  <label>In-page mic (needs HTTPS or localhost)</label>
  <div class="row">
    <button class="rec" id="recBtn" type="button">Start record</button>
  </div>
  <div class="row">
    <button class="secondary" id="stopBtn" type="button" disabled>Stop</button>
    <button class="go" id="sendAudio" type="button" disabled>Send audio → STT</button>
  </div>

  <label>Works on plain HTTP: pick / capture audio file</label>
  <input id="file" type="file" accept="audio/*,video/*" capture="user"/>
  <button class="go" id="sendFile" type="button">Upload file → STT</button>

  <label>Or type text (always works)</label>
  <textarea id="text" rows="3" placeholder="Run make smoke-opencode-ollama and report"></textarea>
  <button class="go" id="sendText" type="button">Send text</button>
  <button class="secondary" id="fetchLast" type="button">Refresh last transcript from host</button>

  <div id="result" aria-live="polite"></div>
  <div id="status">Ready. Set token first.</div>

  <script>
    const $ = (id) => document.getElementById(id);
    const status = (m) => { $('status').textContent = m; };
    let mediaRecorder = null;
    let chunks = [];
    let lastBlob = null;
    let lastName = 'phone-capture.webm';

    let pollTimer = null;

    function showResult(data) {
      const tr = (data && (data.transcript || data.text)) || '';
      const box = $('result');
      if (!tr) {
        box.classList.add('show');
        box.textContent = 'Server returned OK but transcript was empty. On host: cat examples/voice-stt-edge/.generated/last-transcript.txt';
        status('Empty transcript in response: ' + JSON.stringify(data).slice(0, 300));
        return;
      }
      box.innerHTML = '';
      const title = document.createElement('div');
      title.textContent = 'Transcript';
      title.style.fontSize = '.75rem';
      title.style.fontWeight = '400';
      title.style.opacity = '.75';
      const body = document.createElement('div');
      body.textContent = tr;
      const meta = document.createElement('div');
      meta.className = 'meta';
      let extra = 'backend=' + (data.backend || '?') + '  target=' + (data.target || '?');
      if (data.agent_queued) {
        extra += '\\nAuto-agent queued (' + (data.agent_mode || '?') + ') — waiting for tools…';
      } else if (data.agent_message) {
        extra += '\\n' + data.agent_message;
      } else {
        extra += '\\nOn host: handoff.sh  OR  VOICE_AUTO_AGENT=1';
      }
      meta.textContent = extra;
      box.appendChild(title);
      box.appendChild(body);
      box.appendChild(meta);
      box.classList.add('show');
      try { $('text').value = tr; } catch (_) {}
      if (data.agent_queued) {
        status('Transcript OK — agent running on host. Polling /api/last-run…');
        startAgentPoll();
      } else {
        status('OK — transcript shown (' + tr.length + ' chars). Tools: handoff.sh or enable VOICE_AUTO_AGENT=1');
      }
      try { console.log('voice-remote result', data); } catch (_) {}
    }

    function showAgentRun(run) {
      if (!run || run.status === 'none') return;
      const box = $('result');
      let agentEl = document.getElementById('agentRun');
      if (!agentEl) {
        agentEl = document.createElement('div');
        agentEl.id = 'agentRun';
        agentEl.className = 'meta';
        agentEl.style.marginTop = '1rem';
        agentEl.style.paddingTop = '0.75rem';
        agentEl.style.borderTop = '1px solid #6664';
        box.appendChild(agentEl);
        box.classList.add('show');
      }
      const reply = run.reply_preview || run.reply || run.message || run.error || '';
      agentEl.textContent =
        'Agent: ' + (run.status || '?') +
        (run.mode ? (' (' + run.mode + ')') : '') +
        (run.exit_code != null ? (' exit=' + run.exit_code) : '') +
        (run.duration_s != null ? (' ' + run.duration_s + 's') : '') +
        (reply ? ('\\n\\n' + reply) : '');
      status('Agent status: ' + (run.status || '?'));
    }

    function startAgentPoll() {
      if (pollTimer) clearInterval(pollTimer);
      let n = 0;
      pollTimer = setInterval(async () => {
        n += 1;
        try {
          const run = await getJson('/api/last-run');
          showAgentRun(run);
          if (run.status === 'done' || run.status === 'error' || run.status === 'skipped') {
            clearInterval(pollTimer);
            pollTimer = null;
            status('Agent finished: ' + run.status + (run.ok ? ' OK' : ' (see reply)'));
          }
        } catch (e) {
          if (n > 3) status('Poll error: ' + e.message);
        }
        if (n > 180) { // ~6 min at 2s
          clearInterval(pollTimer);
          pollTimer = null;
        }
      }, 2000);
    }

    const secure = window.isSecureContext === true;
    const hasMD = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    const origin = location.origin;
    const port = location.port || (location.protocol === 'https:' ? '443' : '80');
    const isHttpTailnet = location.protocol === 'http:' && !/^localhost$|^127\\.0\\.0\\.1$/.test(location.hostname);
    const httpsOnAppPort = location.protocol === 'https:' && port === '8787';

    function showBanner(html) {
      const b = $('banner');
      b.innerHTML = html;
      b.classList.add('show');
    }

    // If this script runs, you already got HTTP 200 — SSL errors are usually a
    // *second* navigation where Brave upgraded to https://…:8787
    if (httpsOnAppPort) {
      showBanner(
        '<strong>Wrong URL</strong>: HTTPS on port 8787. Python is HTTP-only.<br>' +
        'On host: <code>make voice-remote-serve</code> then open <code>https://MagicDNS/</code> (port 443, no :8787).'
      );
    }

    // Brave/Chrome: mediaDevices is undefined on non-secure contexts (http://100.x)
    if (!hasMD) {
      $('recBtn').disabled = true;
      $('stopBtn').disabled = true;
      showBanner(
        (document.getElementById('banner').innerHTML ? document.getElementById('banner').innerHTML + '<br><br>' : '') +
        '<strong>In-page mic unavailable</strong> on <code>' + origin + '</code> ' +
        '(secureContext=' + secure + ').<br><br>' +
        '<strong>If Brave shows ERR_SSL_PROTOCOL_ERROR:</strong> it upgraded ' +
        '<code>http://100.x:8787</code> → <code>https://100.x:8787</code>. That cannot work.<br>' +
        'Fix: host <code>make voice-remote-serve</code>, open <code>https://&lt;MagicDNS&gt;/</code> only, ' +
        'or disable Brave “Always use secure connections”, or use file/text/Termux below.<br><br>' +
        '<strong>Works now without HTTPS:</strong> file capture · Send text · Termux'
      );
      status('Mic API missing on plain HTTP. Use file/text, or HTTPS via make voice-remote-serve (port 443).');
    } else if (isHttpTailnet) {
      showBanner(
        'HTTP on tailnet IP — Brave may later force HTTPS and show SSL errors. ' +
        'Prefer <code>make voice-remote-serve</code> + https://MagicDNS/ (no :8787).'
      );
    }

    function authHeaders(json) {
      const t = $('token').value.trim();
      if (!t) throw new Error('token required');
      const h = {
        'Authorization': 'Bearer ' + t,
        'X-Voice-Token': t,
      };
      if (json) h['Content-Type'] = 'application/json';
      return h;
    }

    async function postJson(path, body) {
      status('Request ' + path + ' …');
      const r = await fetch(path, {
        method: 'POST',
        headers: authHeaders(true),
        body: JSON.stringify(body),
      });
      const text = await r.text();
      let data;
      try { data = JSON.parse(text); } catch (e) {
        throw new Error('non-JSON response HTTP ' + r.status + ': ' + text.slice(0, 200));
      }
      if (!r.ok) throw new Error((data && data.error) || text || ('HTTP ' + r.status));
      return data;
    }

    async function getJson(path) {
      const r = await fetch(path, { headers: authHeaders(false) });
      const text = await r.text();
      let data;
      try { data = JSON.parse(text); } catch (e) {
        throw new Error('non-JSON GET ' + r.status + ': ' + text.slice(0, 200));
      }
      if (!r.ok) throw new Error((data && data.error) || text || ('HTTP ' + r.status));
      return data;
    }

    async function blobToB64(blob) {
      // FileReader is more reliable than chunked btoa on mobile
      return await new Promise((resolve, reject) => {
        const fr = new FileReader();
        fr.onload = () => {
          const s = String(fr.result || '');
          const i = s.indexOf(',');
          resolve(i >= 0 ? s.slice(i + 1) : s);
        };
        fr.onerror = () => reject(fr.error || new Error('FileReader failed'));
        fr.readAsDataURL(blob);
      });
    }

    async function sendBlob(blob, filename) {
      $('result').classList.remove('show');
      status('Encoding audio (' + blob.size + ' bytes)…');
      const b64 = await blobToB64(blob);
      status('Uploading + STT on host (' + b64.length + ' b64 chars)…');
      const data = await postJson('/api/audio', {
        audio_b64: b64,
        mime: blob.type || 'audio/webm',
        filename: filename || 'phone-capture.webm',
        target: $('target').value,
      });
      showResult(data);
    }

    $('recBtn').onclick = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error(
            'getUserMedia missing. Use file capture / text, or open via HTTPS ' +
            '(tailscale serve). Plain http://100.x blocks mic in Brave/Chrome.'
          );
        }
        chunks = [];
        lastBlob = null;
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mime = (window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm;codecs=opus'))
          ? 'audio/webm;codecs=opus'
          : ((window.MediaRecorder && MediaRecorder.isTypeSupported('audio/webm')) ? 'audio/webm' : '');
        if (!window.MediaRecorder) throw new Error('MediaRecorder not supported in this browser');
        mediaRecorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
        mediaRecorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
        mediaRecorder.onstop = () => {
          lastBlob = new Blob(chunks, { type: mediaRecorder.mimeType || 'audio/webm' });
          lastName = 'phone-capture.webm';
          stream.getTracks().forEach(t => t.stop());
          $('sendAudio').disabled = false;
          status('Recorded ' + lastBlob.size + ' bytes. Tap Send audio.');
          $('recBtn').classList.remove('on');
        };
        mediaRecorder.start();
        $('recBtn').classList.add('on');
        $('stopBtn').disabled = false;
        $('sendAudio').disabled = true;
        status('Recording… speak a full English phrase, then Stop.');
      } catch (e) {
        status('Mic error: ' + (e && e.message ? e.message : e));
      }
    };

    $('stopBtn').onclick = () => {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
      $('stopBtn').disabled = true;
    };

    $('sendAudio').onclick = async () => {
      try {
        if (!lastBlob) throw new Error('no recording');
        await sendBlob(lastBlob, lastName);
      } catch (e) {
        status('Error: ' + e.message);
      }
    };

    $('file').onchange = () => {
      const f = $('file').files && $('file').files[0];
      if (!f) return;
      lastBlob = f;
      lastName = f.name || 'phone-file';
      $('sendAudio').disabled = false;
      status('Selected file: ' + lastName + ' (' + f.size + ' bytes, ' + (f.type || 'unknown') + '). Tap Send audio or Upload file.');
    };

    $('sendFile').onclick = async () => {
      try {
        const f = $('file').files && $('file').files[0];
        if (!f && !lastBlob) throw new Error('choose a file or record first');
        await sendBlob(f || lastBlob, (f && f.name) || lastName);
      } catch (e) {
        status('Error: ' + e.message);
      }
    };

    $('sendText').onclick = async () => {
      try {
        const text = $('text').value.trim();
        if (!text) throw new Error('text empty');
        $('result').classList.remove('show');
        const data = await postJson('/api/text', {
          text,
          target: $('target').value,
        });
        showResult(data);
      } catch (e) {
        status('Error: ' + e.message);
      }
    };

    $('fetchLast').onclick = async () => {
      try {
        const data = await getJson('/api/last');
        showResult({
          transcript: data.transcript,
          backend: (data.meta && data.meta.backend) || '?',
          target: (data.meta && data.meta.target) || '?',
          handoff_path: data.handoff_path,
          agent_queued: false,
        });
        if (data.last_run) showAgentRun(data.last_run);
      } catch (e) {
        status('Error: ' + e.message);
      }
    };

    try {
      const t = sessionStorage.getItem('voice_token');
      if (t) $('token').value = t;
      $('token').addEventListener('change', () => sessionStorage.setItem('voice_token', $('token').value));
    } catch (_) {}
  </script>
</body>
</html>
"""


def _ext_for_mime(mime: str, filename: str) -> str:
    name = (filename or "").lower()
    if "." in name:
        return Path(name).suffix
    mime = (mime or "").lower()
    if "webm" in mime:
        return ".webm"
    if "ogg" in mime or "opus" in mime:
        return ".ogg"
    if "mpeg" in mime or "mp3" in mime:
        return ".mp3"
    if "mp4" in mime or "m4a" in mime:
        return ".m4a"
    if "wav" in mime:
        return ".wav"
    return ".bin"


def maybe_to_wav(src: Path) -> Path:
    """Convert non-wav to 16k mono PCM wav via ffmpeg (phone webm/opus)."""
    if src.suffix.lower() == ".wav":
        return src
    import shutil
    import subprocess

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return src  # hope faster-whisper/av can decode
    dst = src.with_suffix(".wav")
    # Explicit PCM; ignore opus header warnings when possible
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-i",
        str(src),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(dst),
    ]
    subprocess.run(cmd, check=True)
    if dst.is_file() and dst.stat().st_size > 100:
        return dst
    return src


class VoiceRemoteState:
    def __init__(
        self,
        token: str,
        out_dir: Path,
        backend: str,
        host: str,
        port: int,
        repo: Path,
    ):
        self.token = token
        self.out_dir = out_dir
        self.backend = backend
        self.host = host
        self.port = port
        self.repo = repo
        self.lock = threading.Lock()

    def maybe_queue_agent(self, target: str, transcript: str) -> dict:
        """Opt-in 4b: queue tool-capable agent after STT."""
        mode = ar.auto_mode()
        if mode == "off":
            return {
                "agent_queued": False,
                "agent_mode": "off",
                "agent_message": (
                    "VOICE_AUTO_AGENT off — set VOICE_AUTO_AGENT=opencode "
                    "(local default) or =grok (cloud escalate)"
                ),
            }
        # T-0092: default target worker for opencode, monitor for grok
        if target == "raw":
            target = "worker" if mode == "opencode" else "monitor"
        elif mode == "opencode" and target == "monitor":
            # keep monitor if user asked; still run opencode stack
            pass
        max_turns = int(os.environ.get("VOICE_AGENT_MAX_TURNS", "8"))
        timeout_s = int(os.environ.get("VOICE_AGENT_TIMEOUT", "600"))
        # Align remote auto-agent with installable long-task path (VOICE_LONG_TASK=0 to disable).
        lt = os.environ.get("VOICE_LONG_TASK", "").strip().lower()
        if lt in ("",):
            os.environ["VOICE_LONG_TASK"] = "1"
        long_task = ar.long_task_enabled()
        prompt_path = self.out_dir / "agent-prompt.md"
        run_id = ar.spawn_background(
            repo=self.repo,
            out=self.out_dir,
            mode=mode,
            target=target,
            prompt_path=prompt_path if prompt_path.is_file() else None,
            transcript=transcript,
            max_turns=max_turns,
            timeout_s=timeout_s,
        )
        sys.stderr.write(
            f"==> auto-agent queued mode={mode} run_id={run_id} long_task={long_task}\n"
        )
        return {
            "agent_queued": True,
            "agent_mode": mode,
            "agent_run_id": run_id,
            "agent_long_task": long_task,
            "agent_message": (
                f"agent {mode} queued"
                + (" (VOICE_LONG_TASK)" if long_task else "")
                + " — poll GET /api/last-run"
            ),
        }


TLS_HELP = (
    "ERROR: TLS/HTTPS was sent to the plain HTTP voice-remote port.\n"
    "\n"
    "This Python process only speaks HTTP (default :8787).\n"
    "Tailscale Serve terminates HTTPS on :443 and proxies HTTP here.\n"
    "\n"
    "Do NOT open:  https://<host>:8787/   ← causes HTTP 400 + binary garbage\n"
    "Do NOT open:  https://100.x.y.z:8787/\n"
    "\n"
    "Correct setup:\n"
    "  1) make voice-remote   # or VOICE_REMOTE_HOST=127.0.0.1 make voice-remote\n"
    "  2) tailscale serve --bg --https=443 http://127.0.0.1:8787\n"
    "  3) tailscale serve status   # copy the https://… URL (no :8787)\n"
    "  4) Phone: open that https://MagicDNS/ URL (port 443)\n"
    "\n"
    "Quick checks:\n"
    "  curl -sS http://127.0.0.1:8787/ping          # → pong\n"
    "  curl -sS https://<magicdns>/ping              # → pong via Serve\n"
)


def make_handler(state: VoiceRemoteState):
    class Handler(BaseHTTPRequestHandler):
        server_version = "pfy-voice-remote/0.1"
        # Allow long headers from reverse proxies
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def handle(self) -> None:
            """Reject TLS ClientHello with a clear text error (not binary 400)."""
            try:
                self.connection.settimeout(30)
                peek = self.connection.recv(5, socket.MSG_PEEK)
            except Exception:
                peek = b""
            # TLS record: ContentType 0x16 (Handshake), version 0x03 0x01/02/03/04
            if peek and peek[0:1] == b"\x16":
                sys.stderr.write(
                    f"{self.address_string()} - TLS handshake on plain HTTP port "
                    f"(client opened https://…:{state.port}? use tailscale serve URL)\n"
                )
                try:
                    body = TLS_HELP.encode("utf-8")
                    msg = (
                        b"HTTP/1.0 400 Bad Request\r\n"
                        b"Content-Type: text/plain; charset=utf-8\r\n"
                        b"Connection: close\r\n"
                        b"Content-Length: "
                        + str(len(body)).encode()
                        + b"\r\n\r\n"
                        + body
                    )
                    self.connection.sendall(msg)
                except Exception:
                    pass
                return
            # HTTP/2 connection preface
            if peek.startswith(b"PRI ") or peek.startswith(b"PRI\r"):
                try:
                    body = (
                        b"ERROR: HTTP/2 prior knowledge sent to HTTP/1 voice-remote.\n"
                        b"Use HTTP/1.1 or access via tailscale serve https://.../\n"
                    )
                    self.connection.sendall(
                        b"HTTP/1.0 400 Bad Request\r\n"
                        b"Content-Type: text/plain\r\n"
                        b"Connection: close\r\n"
                        b"Content-Length: "
                        + str(len(body)).encode()
                        + b"\r\n\r\n"
                        + body
                    )
                except Exception:
                    pass
                return
            return super().handle()

        def _read_body(self) -> bytes:
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0:
                return b""
            if n > 25 * 1024 * 1024:
                raise ValueError("body too large (max 25MB)")
            return self.rfile.read(n)

        def _check_token(self) -> bool:
            auth = self.headers.get("Authorization") or ""
            x = self.headers.get("X-Voice-Token") or ""
            token = ""
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()
            elif x:
                token = x.strip()
            else:
                # query ?token= for simple mobile bookmarks (less ideal)
                q = parse_qs(urlparse(self.path).query)
                token = (q.get("token") or [""])[0]
            return secrets.compare_digest(token, state.token) if token else False

        def _json(self, code: int, obj: dict) -> None:
            raw = json.dumps(obj, indent=2).encode("utf-8") + b"\n"
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _html(self, code: int, html: str) -> None:
            raw = html.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(raw)

        def _text(self, code: int, text: str, content_type: str = "text/plain; charset=utf-8") -> None:
            raw = text.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _process_audio_bytes(
            self, raw: bytes, mime: str, fname: str, target: str
        ) -> dict:
            se.ensure_out(state.out_dir)
            audio_path = state.out_dir / f"remote-capture{_ext_for_mime(mime, fname)}"
            audio_path.write_bytes(raw)
            try:
                audio_path = maybe_to_wav(audio_path)
            except Exception as e:
                sys.stderr.write(f"ffmpeg convert skipped/failed: {e}\n")
            used, transcript = se.resolve_backend(state.backend, audio_path, None)
            return se.persist_success(
                state.out_dir,
                transcript=transcript,
                target=target,
                backend=used,
                audio=audio_path,
                source="remote",
            )

        def _ok_result(self, result: dict, target: str) -> None:
            tr = result.get("transcript") or ""
            sys.stderr.write(f"==> TRANSCRIPT: {tr!r}\n")
            sys.stderr.write(
                f"==> wrote {result.get('transcript_path')} · handoff {result.get('handoff_path')}\n"
            )
            agent_info = state.maybe_queue_agent(target, tr)
            hint = (
                "Agent auto-running — poll /api/last-run"
                if agent_info.get("agent_queued")
                else "On host: handoff.sh  OR  VOICE_AUTO_AGENT=1 make voice-remote"
            )
            return self._json(
                200,
                {
                    "ok": True,
                    "transcript": tr,
                    "text": tr,  # alias for picky clients
                    "target": target,
                    "backend": result["backend"],
                    "handoff_path": result["handoff_path"],
                    "prompt_path": result["prompt_path"],
                    "inbox_path": result["inbox_path"],
                    "transcript_path": result.get("transcript_path"),
                    "hint": hint,
                    **agent_info,
                },
            )

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            # Fast path for connectivity — no JSON, no auth (Termux/browser diagnose)
            if path in ("/ping", "/ping/"):
                return self._text(200, "pong\n")
            if path in ("/", "/index.html", "/m", "/mobile"):
                return self._html(200, MOBILE_HTML)
            if path == "/favicon.ico":
                # Avoid noisy 404s; empty icon
                self.send_response(204)
                self.send_header("Connection", "close")
                self.end_headers()
                return
            if path == "/health":
                return self._json(
                    200,
                    {
                        "ok": True,
                        "service": "pfy-voice-remote",
                        "phase": "T-0091-p4a",
                        "backend": state.backend,
                        "bind": f"{state.host}:{state.port}",
                        "clients": "prefer Termux termux-voice-send.sh if browser hangs",
                    },
                )
            if path == "/api/last":
                if not self._check_token():
                    return self._json(401, {"error": "unauthorized"})
                t = state.out_dir / "last-transcript.txt"
                meta = state.out_dir / "last-meta.json"
                return self._json(
                    200,
                    {
                        "transcript": t.read_text(encoding="utf-8") if t.is_file() else "",
                        "meta": json.loads(meta.read_text(encoding="utf-8"))
                        if meta.is_file()
                        else {},
                        "handoff_path": str(state.out_dir / "handoff.sh"),
                        "prompt_path": str(state.out_dir / "agent-prompt.md"),
                        "last_run": ar.read_run(state.out_dir),
                    },
                )
            if path in ("/api/last-run", "/api/agent-status"):
                if not self._check_token():
                    return self._json(401, {"error": "unauthorized"})
                return self._json(200, ar.read_run(state.out_dir))
            return self._json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path not in (
                "/api/text",
                "/api/audio",
                "/api/transcribe",
                "/api/audio-raw",
            ):
                return self._json(404, {"error": "not found"})
            if not self._check_token():
                return self._json(401, {"error": "unauthorized — set Bearer token"})

            try:
                body = self._read_body()
            except Exception as e:
                return self._json(400, {"error": f"bad body: {e}"})

            # Termux/curl: raw audio bytes (no JSON base64)
            if path == "/api/audio-raw":
                target = (self.headers.get("X-Voice-Target") or "worker").strip().lower()
                if target not in ("monitor", "worker", "raw"):
                    return self._json(400, {"error": "X-Voice-Target must be monitor|worker|raw"})
                if not body:
                    return self._json(400, {"error": "empty audio body"})
                mime = self.headers.get("Content-Type") or "audio/wav"
                # strip "; charset=..." if any
                mime = mime.split(";")[0].strip()
                fname = self.headers.get("X-Voice-Filename") or "phone.wav"
                try:
                    with state.lock:
                        result = self._process_audio_bytes(body, mime, fname, target)
                except se.SttError as e:
                    return self._json(422, {"error": str(e)})
                except Exception as e:
                    traceback.print_exc()
                    return self._json(500, {"error": str(e)})
                return self._ok_result(result, target)

            try:
                data = json.loads(body.decode("utf-8") or "{}")
            except Exception as e:
                return self._json(400, {"error": f"bad json body: {e}"})

            target = (data.get("target") or "worker").strip().lower()
            if target not in ("monitor", "worker", "raw"):
                return self._json(400, {"error": "target must be monitor|worker|raw"})

            try:
                with state.lock:
                    if path == "/api/text":
                        text = (data.get("text") or "").strip()
                        if not text:
                            return self._json(400, {"error": "text required"})
                        used, transcript = se.resolve_backend("text", None, text)
                        result = se.persist_success(
                            state.out_dir,
                            transcript=transcript,
                            target=target,
                            backend=used,
                            audio=None,
                            source="remote",
                        )
                    else:
                        b64 = data.get("audio_b64") or data.get("audio") or ""
                        if not b64:
                            return self._json(400, {"error": "audio_b64 required"})
                        if "," in b64 and b64.strip().startswith("data:"):
                            b64 = b64.split(",", 1)[1]
                        raw = base64.b64decode(b64)
                        mime = data.get("mime") or "audio/webm"
                        fname = data.get("filename") or "phone-capture.webm"
                        result = self._process_audio_bytes(raw, mime, fname, target)
            except se.SttError as e:
                return self._json(422, {"error": str(e)})
            except Exception as e:
                traceback.print_exc()
                return self._json(500, {"error": str(e)})

            return self._ok_result(result, target)

    return Handler


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Remote Android/Tailscale voice edge (T-0091 p4a)")
    p.add_argument("--host", default=os.environ.get("VOICE_REMOTE_HOST", DEFAULT_HOST))
    p.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("VOICE_REMOTE_PORT", str(DEFAULT_PORT))),
    )
    p.add_argument(
        "--token",
        default=os.environ.get("VOICE_REMOTE_TOKEN", ""),
        help="Shared secret (required). Env VOICE_REMOTE_TOKEN.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path(os.environ.get("VOICE_STT_OUT", str(DEFAULT_OUT))),
    )
    p.add_argument(
        "--backend",
        default=os.environ.get("VOICE_STT_BACKEND", "auto"),
        help="STT backend for /api/audio (default auto)",
    )
    p.add_argument(
        "--generate-token",
        action="store_true",
        help="Print a random token and exit",
    )
    args = p.parse_args(argv)

    if args.generate_token:
        print(secrets.token_urlsafe(24))
        return 0

    token = (args.token or "").strip()
    if not token:
        print(
            "error: VOICE_REMOTE_TOKEN / --token required\n"
            "  export VOICE_REMOTE_TOKEN=$(examples/voice-stt-edge/python.sh "
            "examples/voice-stt-edge/remote_server.py --generate-token)",
            file=sys.stderr,
        )
        return 2

    if args.host in ("0.0.0.0", "::", "[::]"):
        print(
            "warning: binding all interfaces — only safe on Tailscale/private net, "
            "never raw public internet without extra controls",
            file=sys.stderr,
        )

    repo = Path(os.environ.get("VOICE_AGENT_REPO", str(se.ROOT))).resolve()
    state = VoiceRemoteState(
        token=token,
        out_dir=se.ensure_out(args.out_dir),
        backend=args.backend,
        host=args.host,
        port=args.port,
        repo=repo,
    )
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    amode = ar.auto_mode()
    print(f"== voice-remote (T-0091 p4a/4b) ==")
    print(f"  bind: plain HTTP only  http://{args.host}:{args.port}/")
    print(f"  out  {state.out_dir}")
    print(f"  backend={args.backend}")
    print(f"  auto-agent={amode}  (ADR-0012: 1/opencode=local · grok=cloud escalate)")
    print(f"  repo={repo}")
    print("")
    print("  HTTPS for phone mic:")
    print(f"    make voice-remote-serve   # tailscale serve :443 → :{args.port}")
    print("")
    print(f"  NEVER open https://…:{args.port}  (TLS on this port → SSL error)")
    print(f"  Desk check: curl -sS http://127.0.0.1:{args.port}/ping")
    if amode == "off":
        print("  After STT:  VOICE_AUTO_AGENT=opencode  (local) or =grok (paid)")
    else:
        print("  After STT:  auto agent runs; poll GET /api/last-run")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n==> stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
