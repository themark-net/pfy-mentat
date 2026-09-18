# #228 DevBot handoff — Gab cloud lane + local recommend sync

**Design PASS (DoD):** 2026-09-18 PT  
**Cite:** GitHub **#228** only. Do not reopen **#76**. Catalog **70–75 HOLD**.  
**Implement against:** `DESKTOP-SPEC.md` + this file. Prefer Grok Build on nimo (`machineId` 5c5c138b-c5f6-4ba5-a8d0-fe204735e5cc).  
**Do not** implement from Design Bot. **Do not** scrape Gab private HTML. **Do not** claim Gab hosts downloadable weights.

---

## Founder locks

- Gab does **not** publish local-download ranking. “Best” = cloud router `model=auto` on `https://gab.ai/v1`.
- Map Gab open-weight families → Ollama pulls filtered for nimo (~64 GiB 8060S VRAM; ~61 GiB RAM).
- FreeToken-first local spine **unchanged**.
- Product copy only. Operate-or-FAIL.

---

## DoD (must all PASS)

1. **Cloud lane UX** — Loop wizard + Attach usable for Gab OpenAI-compatible endpoint `https://gab.ai/v1`:
   - `model=auto` (default cloud “best”)
   - pin-by-id from `GET /v1/models`
   - Missing key / Plus-required → FAIL + next (docs: gab.ai/docs/api-auth; Plus/max plan)
2. **Local ranking sync** into existing recommend/try (#207):
   - Fetch `GET https://gab.ai/v1/models` (auth optional)
   - Filter open-weight families (gemma / qwen / deepseek / glm / kimi / …)
   - Map → Ollama tags + size estimate
   - Host fit: `fits` / `tight` / `won't-fit` (nimo profile)
   - Surface in Engine recommend/try — do not replace FreeToken-first order
3. **Pull path** — UI + `./pfy` action: `ollama pull` for recommended-not-yet-local that **fit**; tight = confirm; won't-fit = disabled + FAIL + next; never auto-pull 405B-class without explicit opt-in
4. **Honesty** — chip/one-liner: `gab auto ≠ local ranking`; never imply Gab auto ranks local weights; never imply Gab hosts GGUF
5. **Tests** — offline fixture of Gab `/models` JSON; CI needs no network
6. **Holds** — #225 Launch session intact; no Env tab; catalog 70–75 HOLD; #76 stays closed

---

## Wireframe paints (product)

### Loop / wizard — Gab cloud

```
lane       cloud/subscription
endpoint   Gab · https://gab.ai/v1
model      ● auto   ○ pin [id]
key        set | FAIL missing · next Plus + API key docs
chip       gab auto · cloud router
[ Launch session ]
```

### Engine — recommend sync + Pull

```
recommend  local sync · Gab families
chip       gab auto ≠ local ranking
row        tag · size · fits|tight|won't-fit · local|not-local
[ Pull ]   fits + not-local only
won't-fit  FAIL + next smaller Q4 ≤32B
```

### FAIL+next map

| Condition | Paint | Next |
|-----------|-------|------|
| No Gab key | FAIL key missing | set `GAB_API_KEY` / Plus docs |
| Plus required (403) | FAIL plus required | max/Plus plan |
| won't-fit | disabled Pull + FAIL | smaller tag / free VRAM |
| Pull fails | FAIL pull | retry / check Ollama |
| Sync network fail | FAIL sync (show last fixture/cache or empty honest) | Refresh sync |

---

## Non-goals

- Scrape private Gab HTML
- Claim Gab hosts downloadable weights
- Auto-pull 405B (or similar) without opt-in
- Reopen #76; lift catalog 70–75; Env tab; change FreeToken-first spine
- Equate Gab Intent Engine auto with local recommend order

---

## nimo fit (guidance for mapper)

- Prefer ≤~32B Q4 for snappy loops
- 70B–120B only when free VRAM ≥40 GiB **and** opt-in
- Overlap already local is fine to show as `local` (gemma4:26b, qwen3-coder:30b, qwen3-coder-next, qwen2.5-coder:32b, gpt-oss:120b, glm-4.7-flash, …)

---

## Suggested build order

1. Wizard/Attach Gab endpoint + auto/pin + key FAIL+next  
2. Offline Gab `/models` fixture + mapper (family → Ollama tag + size)  
3. Host-fit classifier → paint into #207 recommend UI  
4. Pull action (GUI + CLI) gated by fits/tight  
5. Honesty chips  
6. CI tests green without network  

---

## Success check (founder)

Attach Gab cloud with `auto` works under Plus key. Engine recommend shows Gab open-weight families as Ollama rows with honest fit. Pull fetches a fits-not-local tag. Window never says Gab auto is a local ranking.
