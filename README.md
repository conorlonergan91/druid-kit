# Druid Kit

[![CI](https://github.com/conorlonergan91/druid-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/conorlonergan91/druid-kit/actions/workflows/ci.yml)

A World of Warcraft addon for levelling a Druid on **WoW Forever** (Interface 16001). It puts a step-by-step levelling
guide, action-bar setup, bag and bank management, loot advice, a party healing view and a navigation arrow into one
addon, built for big readable text and alerts that never rely on colour alone.

A second, small addon, **ClaudeProgress**, exports the character's state (level, quests, gear, bags, bank, recipes,
talents) to SavedVariables. That snapshot is read outside the game to regenerate the guide, so the guide always
reflects where the character actually is.

## Features

Full behaviour, every command and what a tester can check: [docs/FEATURES.md](docs/FEATURES.md).

| Area | What it does |
| --- | --- |
| Step tracker (`Alt+N`, `/dk steps`) | Route window: one action at a time (accept, do, hand in, go, fly, train, learn a flight path, set the hearth), ticked off from quest, zone, trainer, flight and level events. An arrow you set yourself (`/way`, a pin, a map click, a guide **Go**) never ticks a step. The route's quests are accepted and handed in with the reward picked (hold Shift to do it yourself); skipped quests are left alone. Time and deaths per step are logged for the next re-plan. |
| Route planner (`planner/`) | An LLM agent plans the route; a Python toolkit does the maths (hub ranking, stop order, clustering, group value, a simulator) and an eval loop scores plans. See [planner/README.md](planner/README.md). |
| Guide (`Shift+J`, `Alt+1-8`, `/guide`) | Tabbed guide window with a jump bar and **Go** buttons that start the navigation arrow. Content is generated from JSON. |
| Action bars (`/dk bars`) | Lays out caster, Bear, Cat and Prowl bars by how easy each key is to reach, with melee abilities as small `/startattack` macros. Binds G to Cat Form unless you chose a key with `/dk catkey`. `/dk load backup` restores the old bars and keys. New spells go onto their key when learned. |
| Healing mode (`Alt+H`) | Swaps the caster bar and gear between questing and healing sets. |
| Bag check (`Alt+B`) | Upgrades to equip, what to use, bank or sell, and a drop list with a confirmed **Destroy** that re-checks the slot. Quest items that look orphaned are only listed to check. At a vendor it sells junk, unusable gear, unused materials and worse bandages by itself (12 per visit at most, never potions, food or quest items) and repairs. |
| Bank check | Opens with the bank: what to take out and what to store, including gear for later levels and dungeon packing. |
| Loot rolls | NEED / GREED / PASS advice that weighs your gear, the item's value and who in the party wears it; Greeds by itself on materials and items you can't use (`/dk autoroll off`). Full bags while looting: TAKE or SKIP per item. |
| Navigation (`Alt+G`, `/way`) | On-screen arrow with yards and turn directions from a map click, a pin, a guide **Go** or `/way`. Route steps can chain waypoints; the arrow warns when you stop getting closer, and the path you walk is logged so the planner can turn it into waypoints. |
| Party view | Health in words and symbols, heal buttons that mirror the action bar, HoT timers, cure and buff buttons. |
| Helpers | Pre-pull HUD, rest prompt, catch-up tracker towards a friend's level, profession training reminders, dungeon quests and quest sharing. |

## Engineering notes

- **Taint-safe.** WoW protects action bars, key bindings and secure buttons in combat. Bar changes asked for in combat
  wait for combat to end and then run in order; key commands are refused until then. Nothing changes bars or keys at
  login, and every bar or key change ends with a prompt to reload the UI, so Blizzard frames keep working in combat.
- **Safe with your items.** Destroy and Sell check the bag slot again at the moment they run; quest items, library books
  and Waylaid Crates are never sold or destroyed; the vendor autopilot stops at what the Buyback tab can return.
- **Defensive against the client.** WoW Forever mixes classic and modern APIs (`C_Container`, `C_TradeSkillUI`,
  `C_Map`, interaction-manager events) and returns hidden ("secret") values in combat. Calls go through small wrappers
  that try both API generations and treat unreadable values as unknown.
- **Own navigation arrow.** The arrow projects map coordinates into yards itself (map size worked out from world
  positions of its corners) and compares the bearing with the player's facing. It also sets the game's map waypoint.
- **Accessibility first.** Every alert is a word, letter or icon; colour is only ever a second signal.
- **Guide as data.** `tools/make_guide.py` turns a JSON guide into `DruidKit_Guide.lua` (guide tabs, the step
  tracker's route and nearby vendors), so content changes never touch addon code; CI checks the generated file is up
  to date. Routes are plain Python data (`tools/example_route.py`); `tools/build_now.py` puts one into the guide JSON
  and rebuilds the Now tab. `tools/route_check.py` checks the route's travel against the save: no hearth that isn't
  set, no flight that isn't learned, and it warns about a flight master the route passes without an `fp` step.

## Repository layout

```
DruidKit/          the addon (Lua 5.1, loaded in toc order)
  DruidKit.lua         guide window, action-bar layouts, key bindings, slash commands
  DruidKit_Bags.lua    bag check, sell/bank lists, loot helper, roll advice
  DruidKit_Bank.lua    bank check
  DruidKit_Trainers.lua trainer pins, Go to window, navigation arrow, /way
  DruidKit_Steps.lua   step tracker: route window, auto-advance, automatic quest accept and hand-in
  DruidKit_Party.lua   party healing view
  DruidKit_Helpers.lua HUD, catch-up tracker, profession lines
  DruidKit_Style.lua   shared window styling, key map window
  DruidKit_Dungeons.lua dungeon quests, quest sharing, quest XP line
  DruidKit_DungeonData.lua generated dungeon quest data (QuestieDB-derived, see NOTICE)
  DruidKit_Guide.lua   generated guide content, route and vendors (do not edit by hand)
ClaudeProgress/    character-state exporter
tools/             guide generator, route builder and examples
planner/           route-planning toolkit (rk.py), agent rules and task, eval tools
docs/              feature behaviour (FEATURES.md) and UI style rules
knowledge/         WoW Forever facts registry
skills/            the Claude skill that runs updates (personal details stay in a private handoff file)
.claude/agents/    one small agent per job (research, data, planning, steps, bags, review, QA, deploy)
tests/             tests that run the real addon code against a mocked WoW API
```

## Tests

The tests run the real addon Lua in a **Lua 5.1** runtime (the version WoW uses) through lupa's `lupa.lua51` module,
with the WoW API mocked in `tests/wowenv.py` and `tests/mocks/`. They cover the step tracker, bars and keys, bag and
sell rules, bank, rolls, navigation, party view, helpers, dungeons, the exporter, and the guide, route and planner tools.

```sh
pip install -r requirements-dev.txt
sh tests/run_all.sh          # one line per test file, non-zero exit on failure (needs `timeout`)
ruff check . && ruff format --check .
```

CI runs a Lua 5.1 syntax check, ruff (lint and format), a check that `DruidKit_Guide.lua` matches its JSON, and
`tests/run_all.sh` on every push.

## Install

Copy `DruidKit/` and `ClaudeProgress/` into `World of Warcraft/_forever_/Interface/AddOns/`, start the game, then
type `/dk bars` and `/dk keys`. `/dk` lists the main commands; [docs/FEATURES.md](docs/FEATURES.md) has all of them.

To rebuild the guide from JSON:

```sh
python3 tools/make_guide.py tools/example_guide.json DruidKit/DruidKit_Guide.lua
```

## How it was built

I designed and directed this project and built it with Claude as an AI pair programmer: I set the requirements from
playing, tested every change in game, and Claude wrote most of the code and tests. Commits are co-authored to reflect that.

## Licence

MIT for this project's own code. See [LICENSE](LICENSE).

Some data is derived from Questie / QuestieDB, which is GPLv3: `DruidKit/DruidKit_DungeonData.lua` and the town spots
in `planner/travel.json`. That data stays under GPLv3 and is credited in [NOTICE](NOTICE). The QuestieDB data itself
(`planner/db.json`, `planner/data/`) is built locally and not committed.
