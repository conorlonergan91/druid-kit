# Agents

Small agents with one job each. Code does the maths and the checks; agents make judgement calls; gates stop bad
releases. Definitions live in `.claude/agents/` (one file per agent, usable as Claude Code / Cowork subagents).

## Review of the old setup (17-18 Nov play)

The old setup had three roles: a blind planner, an orchestrator for the eval loop, and one "route update" role that
did everything else. Most problems in play came from that last role doing too many jobs at once:

| What went wrong in play | Missing responsibility | Now owned by |
|---|---|---|
| Route said one flight Nighthaven -> Auberdine (it is two) | facts checked against Forever, flight data | wow-researcher, data-keeper |
| No flight paths learned, hearth never set, player walked | travel gate | step-writer, travel-checker |
| Boat step with no directions; collectables with no spots | step-writing standard | step-writer |
| New route id threw the player back to step 1 | tidy + catch-up | route-tidier, addon-engineer |
| Quest item that starts a quest never right-clicked | step `how`, addon notice | step-writer, addon-engineer |
| Bags full, loot lost, mage scrolls offered to "use" | bag planning + item rules | bag-advisor, addon-engineer |
| Generated guide broke the addon (`[[[Name]]]`) | release gate | qa-gatekeeper |
| A reused deploy folder sent a stale file | release process | deployer |
| Feedback fixed once but not turned into a rule | triage to owners + lessons | feedback-triager |
| Quest Guide doc and Commands tab drifted | player-facing text | guide-writer |

## The agents

| Agent | One job | Kind |
|---|---|---|
| wow-researcher | Verify facts with sources; Forever vs Classic | research |
| data-keeper | db.json, travel.json (links, boats, banks), vendors, corrections | data |
| save-reader | Save -> state.json; stale save, Lua errors, flights, hearth, bags | script-first |
| log-analyst | Step log, skips, walked paths, travel share -> findings | analysis |
| route-tidier | Drop done/passed/skipped steps | script-first |
| hub-strategist | Where next: hub order, class trips, training, horizon | planning |
| loop-sequencer | Stop order inside a hub, party flags, timed quests | planning |
| step-writer | Route file: one action per step, spots, `via`, `how`, fp/home/abandon, sell stops | writing |
| travel-checker | Flights, hearth, boats usable by this character | gate (script) |
| bag-advisor | Quest items later (bank/drop), vendors, sell stops | planning |
| plan-reviewer | Checklist critic before release | review |
| addon-engineer | Lua features and fixes, test first | build |
| qa-gatekeeper | Tests, lint, Lua syntax of generated files, rules, accessibility, drift | gate |
| deployer | Fresh deploy folder, md5 verify, HANDOFF, repo patch/push | release |
| guide-writer | Now tab, Commands tab, Quest Guide doc | writing |
| feedback-triager | Player feedback -> owned tickets with acceptance tests + rules | triage |
| rules-tuner | Blind planner runs and scoring for rule changes | eval |

## Flows

**"update"** (the player played since the last save)

```
save-reader -> log-analyst -> route-tidier
   -> [route still right?] yes: step-writer edits in place
                           no:  hub-strategist -> loop-sequencer -> step-writer
   -> travel-checker + bag-advisor -> plan-reviewer -> qa-gatekeeper -> deployer -> guide-writer -> reply
```

**Feedback or a feature request**

```
feedback-triager -> (wow-researcher | data-keeper | addon-engineer | step-writer rule)
   -> qa-gatekeeper (new test fails on old code, passes now) -> deployer -> guide-writer -> reply
```

**Rule change** — rules-tuner runs 3 blind planners per version and compares averages before RULES.md changes.

## Hand-off files (all under `build/`)

`state.json` (save-reader) · `findings.json` (log-analyst) · `outline.json` (hub-strategist) · `loops.json`
(loop-sequencer) · `route_vN.py` (step-writer) · `items.json`, `vendors.json` (bag-advisor, data-keeper) ·
`research/*.json` (wow-researcher) · `tickets.json` (feedback-triager).

## Gates nothing ships without

1. travel-checker: no ERROR.
2. qa-gatekeeper: tests + lint green; every generated Lua file loadstring-checked; the real step tracker loads the
   new guide with mocked state and lands on the right first step.
3. plan-reviewer: APPROVED (route changes only).

## Cost

Script-first agents (save-reader, route-tidier, travel-checker) and the gates can run as plain commands in the main
session; spawn subagents for the judgement jobs only when the work is big (a full re-plan, a new feature). Small
fixes go straight through the triage -> engineer -> qa -> deploy path.

## Blind planner (eval)

Works in a folder that holds only `TASK.md`, `RULES.md`, a quest pack (`quests.csv` from `eval/build_pack.py`) and
a copy of the tools (`rk.py`, `db.json`, `travel.json`, `data/`). Prompt:

> You are a levelling-route planner. Work ONLY inside `<folder>`. Read TASK.md and the rules file there and follow
> them exactly. Do not read any other file or folder, and do not use web search or web fetch. Use `tools/rk.py`
> heavily (hub choice at arrival level and ~3 levels later, clustering, stop order, training trips and the final
> sim). Write `plan.json` in the format TASK.md gives, run `python3 tools/rk.py sim plan.json`, fix every problem it
> reports. Reply with the summary field and the final sim output only.

## Data sources and licences

- QuestieDB (GPLv3): loaded at runtime by `load_db.py`; nothing from it is committed.
- Reference routes used for scoring (RestedXP's free Forever routes, CC BY-NC-SA): parsed locally by
  `eval/build_reference.py` to score plans; never committed, never copied into a route. Paid routes are off-limits.
