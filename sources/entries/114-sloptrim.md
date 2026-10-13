### Entry 114: Sloptrim — local, stdlib-only detector that scores AI-writing patterns in prose files

- **URL**: https://github.com/seyedehsanhadi/sloptrim (Apache-2.0, Python, 307 stars at this read; tag v0.9.4 at `38dbb7cb4e97`)
- **Date**: 2026-10-12 (daily X intake)
- **Source / Poster**: @DanKornas, https://x.com/DanKornas/status/2109452489346924959
- **Summary / Key Claims** (upstream README, `scripts/detect.py --help`): "A local detector for AI-writing patterns ... Python standard library only, no network, no model. Prose only, never code." Scores 0-100 against 71 documented patterns (62 with a detector, 50 of which move the score) into bands from `clean` to heavy tells, reads 20 formats including `.docx`, `.pptx`, `.ipynb` and LaTeX, and reports metrics such as invisible characters and homoglyphs. `python scripts/detect.py FILE` prints JSON; `--clean` prints scrubbed text. Hooks score files on save in Claude Code; `/sloptrim init` writes the contract to `AGENTS.md` and a Cursor rule for other agents. Upstream warns short texts (under 120 words) give low confidence.
- **Why it matters here**: Entry 105 (anti-slop) gives agents instructions; Sloptrim gives a number. A Reviewer or Design check could run `detect.py` on handoff docs, PR bodies and catalog entries the bots write and flag high scores, with no model and no key. Mark's standing preference for plain, specific writing makes this a cheap gate. No eval-auto trial: nothing in pfy-mentat scores prose today, so it would be an addition, not a replacement.
- **Fit on nimo**: Yes. A clone at v0.9.4 under `~/DEVELOP/pfy-mentat/tmp/sloptrim`; system `python3` is enough. Don't install the Claude Code plugin or copy it into `~/.claude/` on nimo, and don't run `/sloptrim init` in pfy-mentat until a trial says the score is useful.
- **Verified on the Grok Bot box** (`/tmp`, bubblewrap read-only root, no network): a deliberately sloppy paragraph scored 66 ("heavy tells", 6 patterns), a plain one scored 0 ("clean"); a zero-width space planted in the plain text was reported (`invisible_chars`) and removed by `--clean`. Not verified: other formats, the hooks, false-positive rates on our own docs.
- **Extracted Repos / Tools**: https://github.com/seyedehsanhadi/sloptrim · https://github.com/seyedehsanhadi/sloptrim/blob/main/references/patterns.md
- **TOOLS.md Link**: None yet. I0 awareness. No TOOLS.md row, no `data/tools.json` row.
- **Smoke**: `python3 examples/x-intake-local/smoke_112_114.py --entry sloptrim`. Uses `$SLOPTRIM_DIR` or `~/DEVELOP/pfy-mentat/tmp/sloptrim`, HEAD pinned to v0.9.4 (`$SLOPTRIM_COMMIT` overrides; a mismatch exits 2). Sloppy must score at least 30 above plain, plain under 40, the planted zero-width char must be reported and scrubbed. Receipt: `pipelines/smoke/sloptrim/latest.json`.
- **Non-goals**: No plugin install, no hooks, no AGENTS.md contract in pfy-mentat in this slice.
- **How this fails / how we recover**:

| Risk | How it fails | Recovery |
|------|----------------|----------|
| Scores flag formal but honest writing | False positives on ADRs or handoffs | Trial on 20 existing docs first; treat score as a hint, not a gate |
| Short texts | Under 120 words confidence is low | Run on whole docs, not single lines |
| Upstream pattern changes | Scores drift between versions | Commit pinned; bump deliberately |
