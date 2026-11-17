---
name: wow-forever-druid-update
description: Use for any WoW Forever / DruidKit request from the player, especially "update": load the handoff from the Mac, re-plan the route with the planner tools, update the guide, doc and addon.
---

# WoW Forever Druid — DruidKit

Everything personal (the player, their character and realm, friends, accessibility needs, document ids, private
details) lives in `HANDOFF.md` on the player's Mac, never in this skill or the public repo.

## First, every new session
1. On the Mac (device_bash), read `$HOME/mnt/World of Warcraft/_claude_druidkit/HANDOFF.md` and `STRUCTURE.md`
   (layout templates for every guide tab and the doc: change content, never layout). Read `TALENTS.md` and
   `PROFESSIONS.md` only when the request touches talents or professions. HANDOFF holds the player profile, current
   state, file paths, the fast update order and hard-won lessons; follow its privacy rules.
2. Restore the workspace: stage `_claude_druidkit/build/*` and `_claude_druidkit/test/*` to `/home/claude/build` and
   `/home/claude/test`; the live addon in `_forever_/Interface/AddOns/DruidKit/` is the source of truth for the Lua.
   `pip install lupa --break-system-packages` if needed, then run `test/run_all.sh` once.
3. Planner: restore `_claude_druidkit/routekit/` (or `planner/` from the repo). If `db.json` is missing, clone
   https://github.com/Questie/QuestieDB and run `load_db.py <clone>`.

## Hard rules
- Verify every quest, levelling, talent and fight tip against WoW Forever sources. Say plainly what is unverified.
- Accessibility per HANDOFF: alerts are words, letters or icons, never colour alone.
- Bars and gear swap only on the player's key (Alt+H). Nothing automatic.
- Action bars: never call SetBinding/SaveBindings at login, never write Blizzard globals; code that changes slots or
  keys ends with the DRUIDKIT_RELOAD popup. Check `General.log` for "tainted by 'DruidKit'" on every update.
- Only verified quest IDs and coordinates in routes; when unsure, give the name only (title match) or a note step.
- Paid levelling guides are off-limits. Free RestedXP routes (CC BY-NC-SA) may be studied for decisions and used to
  score plans, never copied into a route.

## The route (step tracker)
`build/route_vN.py` holds ROUTE: sections of one-action steps (accept / turnin / complete / goto / fly / hearth /
train / level / note / fp / home; `fp` = learn the flight path in town `to`, `home` = set the hearthstone in `to`;
both tick themselves) with `q`, `name`, `npc`, `where`, `goto [zone, x, y]`, `to`, `pick`, `tip`, plus `est`
(projected minutes), `party=True` on kill steps worth a group, `how` (the item to use, the way in) and `via`
(waypoints the arrow takes first: `[zone or map id, x, y, "label"]`). Keep headlines short; detail goes in `where`/`tip`.
`build_now.py` puts it into guide.json and the Now tab; `make_guide.py` emits `DruidKitRoute`. Same route `id` keeps
the player's progress; a new id restarts it (finished steps skip themselves).

## Planner: let code do the maths
- `rk.py hubs --level L --from TOWN --current ZONE --done done.json`: XP/hour per hub over the stay, with a grind
  baseline. Build done.json from the save's `completed.quests`.
- `available`, `cluster`, `loop` (TSP stop order), `party`, `travel`, `sim plan.json` (hours, training, forms).
- Rules: `planner/RULES.md`. Routing lessons: `planner/ROUTING.md`. Agents and eval loop: `planner/AGENT.md`.
- Rule changes are tested with blind planner subagents (3 runs per version, averaged) and `eval/score.py --cut20`.

## On "update"
1. In one device_bash call: save mtime; parse `ClaudeProgress.lua` (level, XP, zone, gold, skills, inventory, bank,
   recipes, quests, completed, travel = hearth home + cooldown + known flight paths) with a small Lua-table reader; grep `Logs/General.log` for "Lua Error" / "tainted".
   If the save is older than the last update, say so instead of re-planning.
2. Read `DruidKitDB.stepLog` (secs, deaths, xp against `est`; how = done / ticked / skipped) and `DruidKitDB.skipQ`.
   For each skipped quest decide: drop it, or come back stronger or with a group. Recalibrate `est` where actuals
   differ a lot. Run `rk.py calibrate <DruidKit.lua>` (fight vs travel share) and `rk.py paths <DruidKit.lua>`
   (walked paths -> `via` waypoints for caves, ramps and other hard-to-find places).
3. Re-plan from where the player is with the planner tools and RULES.md. Quest log: list exactly which quests to
   abandon (far below level, far away, needs an absent group, unknown item sources). Bags: Bag check handles food
   and drink (best two stacks each) and recipes (profession rank); name concrete items to sell or bank from the save.
4. Edit the route file. Travel must be real (RULES v10): an `fp` step at every flight master the route passes
   for the first time, a `home` step before any trip that hearths back, no `fly`/`hearth` the save doesn't support.
   Every flight leg is its own `fly` step (check with `rk.py travel FROM TO --flights ...`), and every boat, tram,
   portal or cross-zone walk has a `how` (where to board, which ship, the wait, where you get off; RULES v11).
   Run `tools/route_check.py <route> --home <travel.home> --flights "<a;b;...>"` and fix every ERROR and warning.
   If `travel.flightsKnown` is false, ask the player to open any flight master's map once. Then run `build_now.py`
   (You lines) then `make_guide.py`; Lua 5.1 `loadstring` check on every
   file; `test/run_all.sh`.
5. Update the Quest Guide doc (ids in HANDOFF). Read it first; one heading plus ordered lists in a single replace
   (whole-block replace needs ifHash + ifRev).
6. Deploy via a fresh `/mnt/user-data/outputs/deploy-<HHMM>/` folder with one `device_commit_files` call (force) to
   the live addon and `_claude_druidkit/build/`, plus HANDOFF state notes; verify with `wc -c`.
7. Reply short and phone-friendly: what changed, the next 3-5 actions in order, then reload advice. /reload for Lua
   changes; full quit (Cmd+Q) for new files, .toc or Bindings.xml. A /reload saves with the OLD code, so new save
   fields need a second /reload.
8. Code and skill changes also go to the public repo (sanitised: no personal details, example guide/route only).
   Keep tests and ruff green, tidy commits with the co-author lines, push, check CI.
