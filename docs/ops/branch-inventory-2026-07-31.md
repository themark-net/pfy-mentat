# Branch inventory (2026-07-31)

## Long-lived (policy)

| Branch | Action this session |
|--------|---------------------|
| main | Release tip (unchanged SHA until next promote) |
| dev | Created from main; received selective ports from unmerged voice/CI work |
| stage | Created from main (= production mirror) |

## Fully merged into main (safe to delete later)

feature/agent-cage-*, feature/cage-smokes-*, feature/env-profiles-*, feature/gstack-*, feature/investigate-*, feature/litellm-*, feature/multica-*, feature/one-shot-*, feature/oq-0006-*, feature/readme-*, feature/rebrand-*, feature/skill-ports-*, feature/write-guard-*, grok/cli, heavy-structural-voice-2026-07-26

## Unmerged (behind main ~66 commits) — not force-merged

Conflict-heavy; **selective file ports** onto **dev** instead:

| Branch | Port decision |
|--------|----------------|
| fix-voice-remote-port-20260727 | Primary source for voice install/REPL/008–009 tasks/voice-clean |
| voice-operator-surface / voice-install-path / voice-clean-port-fix | Subset already covered by tip above |
| heavy-worth-300 | install-runner.sh only |
| heavy-structural-voice-lift | mostly superseded by main’s 006/007 tasks |
| ci-self-hosted-runner | docs/workflows partially ported via voice-clean + self-hosted-runner.md |
| adr-0013-optional-tui-preference | main already has ADR-0013 content |

## Cleanup recommendation

Delete fully-merged remote feature branches after operator ACK. Leave unmerged tips for 1–2 weeks or archive as tags `archive/<name>`.
