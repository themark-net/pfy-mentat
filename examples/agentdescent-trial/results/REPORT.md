# AgentDescent vs DSPy vs baseline: X intake triage (held-out results)

Run on nimo, 2026-10-15 20:32-21:08 PT, Ollama `qwen3.6:35b` (Q4_K_M) at `http://localhost:11434/v1`, no paid keys.
Task: one word, CATALOG or SKIP, for one X intake candidate. Gold labels are real past decisions (cataloged
Entries 086-121 vs the SKIPPED lists in `docs/automation/x-intake-2026-10-*-handoff.md`). 61 cases, stratified split
seed 230: train 41 (19 CATALOG / 22 SKIP), held-out 20 (9 CATALOG / 11 SKIP). Classifier calls use
`reasoning_effort: none`, temperature 0, for all three variants.

| Variant | Held-out accuracy | Errors | Tuning wall time | Tuning model calls | Tuning tokens | Held-out eval |
|---|---|---|---|---|---|---|
| Baseline (repo text today) | **0.70** (14/20) | 6 CATALOG→SKIP (097, 103, 107, 111, 115, 116) | – | – | – | 13 s, 5.9k prompt tok |
| AgentDescent 0.5.1 (`kind: text`, 6 rounds × 4 workers max) | **0.95** (19/20) | 097 Foremerge → SKIP | 201 s (stopped after round 1: internal held-out reward 1.0 ≥ target 0.98) | 36 | not reported (0; see notes) | 16 s, 7.3k prompt tok |
| DSPy 3.4.1 MIPROv2 `auto="light"` | **1.00** (20/20) | none | 686 s | 388 (incl. 20 eval) | 332k prompt + 6.2k completion | 34 s |

The AgentDescent/DSPy gap is one case of 20; it is not significant. Both beat the baseline by 5-6 cases, all of which
were the baseline's bias to SKIP tools whose description does not state a license or install path.

## Qualitative diff

**AgentDescent** kept the file and added four lines (`agentdescent_vs_baseline.diff`):
- the "runnable" bullet now accepts "text-based artifacts with a clear installation one-liner";
- the license bullet accepts "standard attribution or usage riders ... unless explicit restrictions" (cass-memory style);
- a new bullet: infer open-source/reproducibility from stack indicators instead of requiring explicit confirmation;
- Phase 0: "Default to CATALOG when descriptions align ..., SKIP only for explicitly stated disqualifiers."
Small, readable and reviewable as a normal PR diff. Risk: the "default to CATALOG" line moves the bias toward accept;
it held on this held-out set (11/11 SKIPs still correct) but should be watched on borderline posts.

**DSPy** replaced the instructions with a full rewrite ("Role: AI Infrastructure Triage Engineer ... AI Tool Registry",
four numbered criteria, explicit CATALOG/SKIP decision logic) and attached 4 few-shot demos, all CATALOG
(098 Sponsio, 106 Rulora, 108 cass-memory, 088 Beacon). It reads as a generic prompt, not as our repo's rules; it
invents names ("AI Tool Registry") and the program lives as DSPy JSON (`dspy_program.json`) rather than a SKILL.md.

## Notes and caveats

- 20 held-out cases is small. The descriptions were written by the trial from the handoff rows (verdict words removed),
  not the raw posts, so they are cleaner than live intake.
- DSPy scores through its own adapter (signature + demos), AgentDescent and baseline through `"{skill}\n\n{prompt}"`.
- AgentDescent `tokens=0`: `openai_compatible` only counts usage when given a `Usage` object in Python; a JSON spec can't.
- The reflector was the same local model with thinking on (max 12k tokens, streamed).
- Real `~/.agentdescent` did not exist before and does not exist after (checked in every harness invocation).
  Every child's temp HOME was empty afterwards. `apply` was never run; AgentDescent's target was a copy in `tmp/`.
- Peak whole-host memory 79 GiB (includes Mark's other processes), under the 85 GiB cap. No lock-up.
