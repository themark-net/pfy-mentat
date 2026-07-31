# 008-voice-receipt

Structural text scorer for the voice long-task receipt block.

Required lines (case-insensitive labels):

```
STATUS: pass|fail|blocked|done|ok|error
DOD: <one line>
EXIT: <exit-card family>
NEXT: <one concrete next step or done>
```

EXIT families: goal, turn, budget, wall-clock, no-progress, human, error, external (plus done/none).

Also rejects empty/thin DOD·NEXT and unrecognized STATUS. Preamble before the receipt is OK.

Related: VOICE_LONG_TASK, agent_runner mock/long path, 009-voice-last-run, T-0075, T-0092.
