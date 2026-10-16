#!/usr/bin/env python3
"""Build the labeled X-intake triage case set from real past decisions in this repo.

CATALOG = became a numbered entry (sources/entries/NNN-*.md, intake handoffs 2026-10-05..15).
SKIP    = listed under SKIPPED/Skipped in docs/automation/x-intake-2026-10-*-handoff.md.
LATER items are excluded (deferred, not a decision). Descriptions restate the facts the
operator had (what it is, license, platform, requirements); verdict words are removed.
Split: stratified, seed 230, ~2/3 train, rest held out. Writes cases.jsonl, train.jsonl, heldout.jsonl.
"""
import json, random
from pathlib import Path

C = "CATALOG"; S = "SKIP"
ROWS = [
 # --- cataloged (entry number, handoff date)
 ("086", C, "Laya", "Open-weight 322M-421M param models for typed decisions (choice / score / yes-no) on CPU; laya-serve speaks the same POST /v1/systemone protocol as TypeSafe Jev. Open source on GitHub."),
 ("087", C, "Bespoke Nimble", "Open data + training recipe + 9B model for Jev-style decisions with published evals. Documented path needs NVIDIA BF16 or Apple Silicon."),
 ("088", C, "Beacon (agent-beacon)", "Cross-harness agent session capture (lists Grok Build) that turns user corrections into reusable skills; user-mode install with a local destination."),
 ("095", C, "Qwen3.8-Flash-Next", "180B MoE open-weight model, ~6B active; smallest GGUFs ~66-68 GB, served by llama.cpp/Ollama-style local servers."),
 ("096", C, "Sandlock", "Rootless Landlock + seccomp sandbox for agent commands with copy-on-write dry-run and a host allowlist. Linux, open source."),
 ("097", C, "Foremerge", "Intent-level conflict detection for parallel coding agents in one repo; single binary."),
 ("098", C, "Sponsio", "Deterministic tool-call contracts (LTL monitors) that block/escalate/redirect agent actions, no LLM at runtime; shell, filesystem and destructive-command bundles. Pure Python."),
 ("099", C, "Open Steps", "Done-or-not / check-work agent skills plus a stop hook that refuses to end a session until it writes a report; bash + git."),
 ("100", C, "repository-harness", "AGENTS.md + docs map protocol with a checksum-verified three-way-merge updater; single static binary release."),
 ("103", C, "BugPatrol", "Autonomous QA patrol (explorer, judge, optional fixer, retest in the running app); runs on CLI agents or any custom OpenAI-compatible endpoint. Node 22 CLI."),
 ("104", C, "GraphJin", "Governed GraphQL + MCP server over databases, files and code, with read_only sources and query allow-lists; SQLite supported; single Go binary."),
 ("105", C, "anti-slop", "SKILL.md rule packs that filter generic AI UI, copy and code comments; plain files in a repo."),
 ("106", C, "Rulora", "Small Node library of agent controls: output validation by stage, bounded loops with an explicit human_handoff, frozen candidate selection; no model needed."),
 ("107", C, "HAR", "Agent harness CLI + MCP: a git worktree slot per task, deterministic verify tied to the tree, teardown keeps the branch; npm package, telemetry can be turned off."),
 ("108", C, "cass-memory", "Procedural cross-agent memory: scored rule playbook, harmful marks deprecate rules, context at task start. MIT with an OpenAI/Anthropic rider; release binaries, reflection via local Ollama."),
 ("109", C, "smolvm", "Branchable, checkpointable microVMs (libkrun, KVM on Linux) for any OCI image, no Docker daemon, egress allow lists; release tarball."),
 ("110", C, "Brigade", "Local file-first control plane for agents: work ledger with atomic claims, verification receipts with log digests, memory handoffs; pip package."),
 ("111", C, "runx", "Governed skill runtime that seals a signed, verifiable receipt per run with no account; static binary."),
 ("112", C, "Overtime", "Persistent agents as folders that outlive sessions: daemon wakes, daily budgets, protected paths, drives any ACP agent. MIT, npm."),
 ("113", C, "Festival", "Plans, gates and 'fest next' live in files and git so any agent harness can resume. Apache-2.0, static binaries."),
 ("114", C, "Sloptrim", "Stdlib-only offline 0-100 score for AI-writing patterns in prose files. Apache-2.0."),
 ("115", C, "OpenQodex", "Pre-push code review: scanners on changed lines, then a reviewer agent that must raise or drop each finding, checked by a model-free finalize step; any agent can be the reviewer. Apache-2.0, npm."),
 ("116", C, "assay", "Deterministic, no-LLM web-page QA that opens the page in Chromium and exercises every control. MIT, PyPI."),
 ("117", C, "Kander", "Terminal kanban that runs coding agents (Grok, OpenCode and others) in parallel git worktrees with read-only reviewer agents before a card is done. MIT, Go binary."),
 ("118", C, "MCP Moira", "Self-hosted workflow engine driven over MCP: node graph, per-step completion conditions and input schemas. Apache-2.0, Docker compose."),
 ("119", C, "AgentDescent", "Parallel, merge-based self-evolution of skill folders, prompts and harnesses against a cases file, with a ledger and explicit apply; works with OpenAI-compatible endpoints. MIT, Python."),
 ("120", C, "Kenfold", "Self-hosted shared memory for several agent CLIs over MCP with per-agent provenance and secret rejection. MIT, Go, Docker compose."),
 ("121", C, "Tree-sitter Analyzer", "Local code-intelligence MCP/CLI: structure, call graph, change impact, mis-wire audit; no model. MIT, Python."),
 # --- skipped (handoff date)
 ("s1012a", S, "Skales", "Agent skills tool; GitHub license field reads NOASSERTION."),
 ("s1012b", S, "SubQ Snap", "Snapshot assistant that runs on a hosted model API only."),
 ("s1012c", S, "Anthropic-Cybersecurity-Skills", "Large pack of offensive/defensive cybersecurity prompts for Claude."),
 ("s1012d", S, "jev-mcp", "MCP server for typed decisions that requires a TypeSafe Jev API key."),
 ("s1011a", S, "mcp-gateway", "MCP gateway/proxy; GitHub license field reads NOASSERTION."),
 ("s1015a", S, "Llamatik", "Kotlin library for building on-device LLM mobile apps."),
 ("s1015b", S, "Infisical", "Secrets management platform (vaults, rotation, SaaS + self-host)."),
 ("s1015c", S, "Auto Runtime", "Agent runtime published under a source-available license (not OSI open source)."),
 ("s1015d", S, "BrowserCode", "Browser sandbox for running hosted coding CLIs in a web tab."),
 ("s1015e", S, "tuxevil-rotator", "Tool that rotates between multiple LLM provider accounts to stretch free tiers."),
 ("s1015f", S, "Skill of Skills", "A directory website listing agent skills."),
 ("s1015g", S, "GhosttyEXTREME", "Terminal enhancement for the Ghostty terminal, macOS only."),
 ("s1015h", S, "ClaudeWatch", "Dashboard of Claude Code session usage."),
 ("s1015i", S, "CamouFlow", "Anti-detect browser profiles with proxy rotation."),
 ("s1015j", S, "Physical AI OS", "Operating layer for robot hardware."),
 ("s1015k", S, "fauxnix", "Unix-like agent shell environment for Windows only."),
 ("s1015l", S, "squirrelscan", "Website SEO QA scanner."),
 ("s1015m", S, "pi-subagents", "Subagent extension that only works inside the pi coding agent."),
 ("s1015n", S, "Kling 4", "New hosted video generation model release."),
 ("s1006a", S, "Reflection Beam", "501B parameter model announcement; weights not released yet."),
 ("s1006b", S, "CYBER-FROST", "De-refused fine-tune distributed in EXL3, sized for DGX-class GPUs."),
 ("s1006c", S, "LangGraph", "Agent graph framework (already tracked in the catalog)."),
 ("s1007a", S, "VibeFrame", "Video editing agent that needs paid video generation provider APIs."),
 ("s1007b", S, "Airgorah", "WiFi auditing / attack tool."),
 ("s1007c", S, "toolgate", "Tool-routing layer that requires a TypeSafe API key."),
 ("s1013a", S, "Asqav SDK", "Agent SDK; GitHub license field reads NOASSERTION."),
 ("s1013b", S, "Rojo Compass", "Roblox development tooling."),
 ("s1013c", S, "Seekter", "AI job search assistant."),
 ("s1014a", S, "ZizkaDB", "Agent database; GitHub license field reads NOASSERTION."),
 ("s1014b", S, "Faucet", "Turns SQL databases into REST/MCP APIs."),
 ("s1014c", S, "invisible_dots", "Computer-use VMs built to evade anti-bot checks."),
 ("s1014d", S, "Awesome Free LLM APIs", "List of free hosted LLM API tiers that need provider signups."),
 ("s1014e", S, "RED-SNOW", "321B model run in EXL3 on an NVIDIA DGX Spark."),
]
TPL = "Candidate from today's X intake: {name}. {desc}\nDecision (CATALOG or SKIP):"

def main():
    here = Path(__file__).resolve().parent
    cases = [{"id": i, "name": n, "prompt": TPL.format(name=n, desc=d), "gold": g} for i, g, n, d in ROWS]
    rng = random.Random(230)
    train, held = [], []
    for lab in (C, S):
        grp = [c for c in cases if c["gold"] == lab]
        rng.shuffle(grp)
        k = round(len(grp) * 2 / 3)
        train += grp[:k]; held += grp[k:]
    for name, rows in (("cases.jsonl", cases), ("train.jsonl", train), ("heldout.jsonl", held)):
        (here / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"cases={len(cases)} train={len(train)} heldout={len(held)} seed=230")

if __name__ == "__main__":
    main()
