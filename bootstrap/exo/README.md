# Exo optional lab

Optional lab path for [exoharness/exo](https://github.com/exoharness/exo). Not the default harness (grok stays default). Do **not** vendor Exo into this repo.

## Docker / `setup.sh`

Requires **git** and **Docker** (`setup.sh` may offer to install). Official one-liner (no extra flags):

```bash
curl -fsSL https://raw.githubusercontent.com/exoharness/exo/main/setup.sh -o setup.sh
bash setup.sh
```

Day-to-day: `./exo.sh` in the checkout (typically `~/exo/`).

Pin / catalog: https://github.com/exoharness/exo

Pattern extract (already on main): [docs/ops/exo-self-mod-patterns.md](../../docs/ops/exo-self-mod-patterns.md)

## `./pfy`

Detects `$ROOT/exo.sh`, `$HOME/exo/exo.sh`, or `command -v exo.sh`.

```bash
./pfy harness use exo   # sets active file only; default_harness stays grok
./pfy start exo
```

When present, start **execs** that script. Exports `LOCAL_OPENAI_BASE_URL` / `OPENAI_BASE_URL` when the ADR-0014 runtime is ready (no invented Exo flags).

Missing: `STUB harness: exo`, [issue #60](https://github.com/themark-net/pfy-mentat/issues/60), the two-line `setup.sh` one-liner above, exit 2. Docker on PATH is **not** ready by itself.
