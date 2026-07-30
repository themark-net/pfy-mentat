#!/usr/bin/env python3
"""GAP-19: refresh monitor brief from recent git + smoke receipts."""
from __future__ import annotations
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "opencode-ollama" / ".generated" / "monitor-brief.md"
PIPE = ROOT / "pipelines"


def sh(cmd: list[str]) -> str:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return (p.stdout or "").strip()


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    log = sh(["git", "log", "-8", "--oneline"])
    status = sh(["git", "status", "-sb"])
    receipts = []
    for path in sorted(PIPE.rglob("*.latest.md"))[:12]:
        receipts.append(f"- `{path.relative_to(ROOT)}`")
    body = f"""# Monitor brief (auto)

Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}

## Git

```
{status}
```

### Recent commits

```
{log}
```

## Eval / smoke receipts present

{chr(10).join(receipts) if receipts else "- (none yet)"}

## Operator

- Worker: OpenCode + Ollama when local bulk
- Monitor: Grok for hard review / tools
- Gates: `make eval-structural` (G0), `make eval-deploy-ready` (G1)

"""
    OUT.write_text(body, encoding="utf-8")
    # also copy to pipelines
    alt = ROOT / "pipelines" / "ops" / "monitor-brief.latest.md"
    alt.parent.mkdir(parents=True, exist_ok=True)
    alt.write_text(body, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"wrote {alt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
