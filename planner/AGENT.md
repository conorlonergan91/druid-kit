# Agents

Three roles, each with a narrow job. Code does the maths; agents make judgement calls; a separate scorer checks them.

## 1. Planner subagent (blind)

Works in a folder that holds only `TASK.md`, `RULES.md`, a quest pack (`quests.csv` from `eval/build_pack.py`)
and a copy of the tools (`rk.py`, `db.json`, `travel.json`, `data/`). It may not read anything else or use the web,
so it can't copy an existing route. Prompt:

> You are a levelling-route planner. Work ONLY inside `<folder>`. Read TASK.md and the rules file there and follow
> them exactly. Do not read any other file or folder, and do not use web search or web fetch. Use `tools/rk.py`
> heavily (hub choice at arrival level and ~3 levels later, clustering, stop order, training trips and the final
> sim). You may write helper scripts inside the folder. Write `plan.json` in the format TASK.md gives, run
> `python3 tools/rk.py sim plan.json`, fix every problem it reports, and keep `untrained_ranks_now` low throughout.
> Reply with the summary field and the final sim output only.

Its usual loop: `hubs` -> `available` -> `cluster` -> `loop` per hub, keeping `done.json` current, then `sim` and fix.

## 2. Orchestrator (the main session)

- Builds the blind folders, launches 3 planners per rules version in parallel, scores each plan with
  `eval/score.py plan.json --cut20` (plans to 30, scored on 1-20) and `rk.py sim` (hours to 20, training).
- Reads where plans diverge from the reference (zone runs, missed/extra quests) and changes the rules or the
  tools in a *general* way (e.g. "judge a hub over your whole stay", "escorts are not a reason to enter a zone"),
  never by naming the reference's choices.
- Compares averages, not single runs: one run of the same rules varied by 5 points.

## 3. Route update (for the player)

On "update": read the game save (level, XP, zone, quest log, bags, skills) and the addon's step log, then:

1. Re-plan from where the player is with `rk.py hubs` / `available` / `loop` and RULES.md.
2. Pick quests to abandon (far below level, far away, needs a group that isn't there, items with unknown sources).
3. Write the route as one-action steps (`tools/example_route.py` format) with `est` (projected minutes from
   `quest_minutes`) and `party` (worth grouping) on kill steps.
4. `build_now.py` + `make_guide.py`, Lua syntax check, `tests/run_all.sh`, deploy.
5. Next time, the step log closes the loop: each step records play time, deaths and XP against `est`, and Skip marks
   quests the player gave up on. The re-plan decides per skipped quest: drop it, or come back stronger / in a group.

## Data sources and licences

- QuestieDB (GPLv3): loaded at runtime by `load_db.py`; nothing from it is committed.
- Reference routes used for scoring (RestedXP's free Forever routes, CC BY-NC-SA): parsed locally by
  `eval/build_reference.py` to score plans; never committed, never copied into a route. Paid routes are off-limits.
