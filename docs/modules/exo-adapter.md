# Module: Exo optional lab adapter

**Purpose:** Exec `exo.sh` from `./pfy start exo` when the script is present. Inference via `LOCAL_OPENAI_BASE_URL` from the ADR-0014 detector when ready (`OPENAI_BASE_URL` defaults to that). Do not invent Exo-specific flags. Do not vendor Exo. Not the default harness.

## Entry

```bash
./pfy harness use exo
./pfy start exo
```

Detect: `$ROOT/exo.sh`, `$HOME/exo/exo.sh`, or `command -v exo.sh`. Registry json `status` is **partial**; live status is **ready** only if `exo.sh` is found.

Missing binary: `STUB harness: exo`, issue #60, official installer, exit 2. Docker on PATH is **not** ready. No fake ready.

```bash
curl -fsSL https://raw.githubusercontent.com/exoharness/exo/main/setup.sh -o setup.sh
bash setup.sh
```

Requires git + Docker (`setup.sh` may offer to install). Day-to-day: `./exo.sh` in the checkout (typically `~/exo/`). Setup notes: [`bootstrap/exo/README.md`](../../bootstrap/exo/README.md). Patterns: [`docs/ops/exo-self-mod-patterns.md`](../ops/exo-self-mod-patterns.md).

Upstream: [exoharness/exo](https://github.com/exoharness/exo)

## Not yet

- Vendoring Exo into git
- Invented Exo flags
- Making Exo the default harness
- Other harness adapters
