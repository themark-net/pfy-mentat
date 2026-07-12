#!/usr/bin/env python3
"""Validate env for DEPLOY_PROFILE. Loads .env if present (no external deps)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        # expand ${HOME}
        if "${HOME}" in val:
            val = val.replace("${HOME}", os.path.expanduser("~"))
        if "$HOME" in val:
            val = val.replace("$HOME", os.path.expanduser("~"))
        os.environ.setdefault(key, val)


def main() -> int:
    load_dotenv(ROOT / ".env")
    # merge non-secret profile file if present
    profile = os.environ.get("DEPLOY_PROFILE", "balanced").strip() or "balanced"
    prof_path = ROOT / "config" / "profiles" / f"{profile}.env"
    if prof_path.is_file():
        load_dotenv(prof_path)
        # profile file should not override secrets already set; setdefault used

    os.environ["DEPLOY_PROFILE"] = profile
    print(f"DEPLOY_PROFILE={profile}")

    required: list[str] = []
    recommended: list[str] = []

    if profile == "local-only":
        recommended += ["OLLAMA_HOST", "OPENAI_BASE_URL"]
    elif profile == "balanced":
        recommended += ["OLLAMA_HOST", "XAI_API_KEY"]
        # balanced wants at least one cloud key for full stack, but allow missing with warn
    elif profile == "max-performance":
        required += ["XAI_API_KEY"]  # or allow OPENAI as alt — check either below
    else:
        print(f"warn: unknown profile {profile!r} — treating as balanced checks")
        recommended += ["OLLAMA_HOST", "XAI_API_KEY"]

    missing_req = [k for k in required if not os.environ.get(k)]
    # max-performance: accept OPENAI_API_KEY as alternative to XAI
    if profile == "max-performance" and missing_req:
        if os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"):
            missing_req = []
            print("note: using non-XAI cloud key for max-performance")

    missing_rec = [k for k in recommended if not os.environ.get(k)]

    for k in sorted(set(required + recommended + ["DEPLOY_PROFILE", "AGENTCAGE_DIR", "WRITE_GUARD_MODE"])):
        present = "set" if os.environ.get(k) else "MISSING"
        secret = k.endswith("_KEY") or k.endswith("_TOKEN") or "SECRET" in k or "PASSWORD" in k
        shown = "(secret)" if secret and os.environ.get(k) else (os.environ.get(k, "")[:60] or present)
        if secret and os.environ.get(k):
            shown = "set (secret hidden)"
        print(f"  {k}: {shown}")

    if missing_req:
        print("FAIL: required for profile:", ", ".join(missing_req))
        print("Edit .env (make env-init) — see bootstrap/env/REGISTRY.md")
        return 1
    if missing_rec:
        print("warn: recommended missing:", ", ".join(missing_rec))
    print("env-check: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
