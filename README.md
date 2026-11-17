# Druid Kit

[![CI](https://github.com/conorlonergan91/druid-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/conorlonergan91/druid-kit/actions/workflows/ci.yml)

A World of Warcraft addon for levelling a Druid on **WoW Forever** (Interface 16001). It puts a step-by-step levelling
guide, action-bar setup, bag and bank management, loot advice, a party healing view and a navigation arrow into one
addon, built for big readable text and alerts that never rely on colour alone.

A second, small addon, **ClaudeProgress**, exports the character's state (level, quests, gear, bags, bank, recipes,
talents) to SavedVariables. That snapshot is read outside the game to regenerate the guide, so the guide always
reflects where the character actually is.

## Features

| Area | What it does |
| --- | --- |
| Step tracker (`Alt+N`, `/dk steps`) | RestedXP-style route window: one action at a time (accept, do, hand in, go, fly, train), ticked off automatically from quest, zone and level events. The arrow follows the current step, and the route's quests are accepted and handed in with the right reward picked (hold Shift to do it yourself). Each step shows time spent against the plan and deaths; after 2 deaths or a long overrun it suggests grouping up or **Skip**, which sets the quest aside and logs it for the next re-plan. |
| Route planner (`planner/`) | An LLM agent plans the route; a Python toolkit does the maths: hub ranking by XP/hour, travelling-salesman stop order with precedence, objective clustering, group value, and a simulator that models travel, XP, training and class forms. A blind eval loop scores plans against a reference route. See [planner/README.md](planner/README.md). |
| Guide (`Shift+J`, `Alt+1-8`) | Tabbed guide window with a jump bar and **Go** buttons that start the navigation arrow. Content is data, generated from JSON. |
| Action bars (`/dk bars`) | Lays out caster, Bear, Cat and Prowl bars by how easy each key is to reach. Melee abilities are placed as small `/startattack` macros so auto attack never drops. New spells go onto their key the moment they're learned. |
| Healing mode (`Alt+H`) | Swaps bars and gear between questing and healing sets in one keypress. |
| Bag check (`Alt+B`) | Upgrades to equip, what to sell or bank, and a safe **Sell junk** that never sells quest items, library books or Waylaid Crates. Keeps your best two food and drink stacks and offers the rest; recipes are checked against your profession rank (learn now, bank for later, or sell). |
| Bank check | Opens with the bank: what to take out and what to store, including gear for later levels. |
| Loot rolls | NEED / GREED / PASS advice that weighs your gear, the item's value, what Druids can wear and which party members wear that armour type. |
| Navigation (`Alt+G`, `/way`) | Click anywhere on the world map, a trainer pin or a guide step to get an on-screen arrow with distance in yards and turn directions. Route steps can chain waypoints (cave entrance, ramp, bridge); the arrow warns when you stop getting closer, and the path you actually walk is recorded so the planner can turn it into waypoints for next time. |
| Party view | Health shown in words and symbols, heal buttons that mirror the action bar, HoT timers. |
| Helpers | HUD (food buff, rested XP), catch-up tracker towards a friend's level, profession training reminders. |

## Engineering notes

- **Taint-safe.** WoW protects action bars and key bindings in combat. Bar and key changes only happen out of combat,
  never at login, and always finish with a prompt to reload the UI, so Blizzard frames keep working in combat.
- **Defensive against the client.** WoW Forever mixes classic and modern APIs (`C_Container`, `C_TradeSkillUI`,
  `C_Map`, interaction-manager events) and returns hidden ("secret") values in combat. Every call goes through small
  wrappers that try both API generations and treat unreadable values as unknown.
- **No dependency on the client's waypoint UI.** The navigation arrow projects map coordinates into yards itself
  (map size worked out from world positions of its corners) and compares the bearing with the player's facing.
- **Accessibility first.** Every alert is a word, letter or icon; colour is only ever a second signal.
- **Guide as data.** `tools/make_guide.py` turns a JSON guide into `DruidKit_Guide.lua`, so content changes never
  touch addon code. Routes are plain Python data (`tools/example_route.py`); `tools/build_now.py` turns one into the
  step tracker's route and the guide's Now tab. `tools/route_check.py` checks the route's travel against the save: no hearth
  that isn't set, no flight that isn't learned, and an `fp` step at every flight master the route passes.

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
  DruidKit_Style.lua   shared window styling
  DruidKit_Guide.lua   generated guide content (do not edit by hand)
ClaudeProgress/    character-state exporter
tools/             guide generator, route builder and examples
planner/           route-planning toolkit (rk.py), agent rules and task, eval tools
skills/            the Claude skill that runs updates (personal details stay in a private handoff file)
tests/             tests that run the real addon code against a mocked WoW API
```

## Tests

The tests load the addon's Lua files into a **Lua 5.1** runtime (the version WoW uses) via
[lupa](https://github.com/scoder/lupa), with the WoW API mocked in `tests/mocks/`. They cover bag and sell rules,
quest-item protection, roll advice, bar layouts and macros, healing mode, the guide window, trainer pins, navigation
maths, the step tracker (skip, hide, struggling advice), food and recipe rules, the planner's maths and the exporter.

```sh
pip install -r requirements-dev.txt
sh tests/run_all.sh          # one line per test, non-zero exit on failure
ruff check .
```

CI runs a Lua 5.1 syntax check, ruff and the full test suite on every push.

## Install

Copy `DruidKit/` and `ClaudeProgress/` into `World of Warcraft/_forever_/Interface/AddOns/`, start the game, then
type `/dk bars` and `/dk keys`. `/dk` lists every command; the Help tab in the guide explains each feature.

To rebuild the guide from JSON:

```sh
python3 tools/make_guide.py tools/example_guide.json DruidKit/DruidKit_Guide.lua
```

## How it was built

I designed and directed this project and built it with Claude as an AI pair programmer: I set the requirements from
playing, tested every change in game, and Claude wrote most of the code and tests. Commits are co-authored to reflect that.

## Licence

MIT. See [LICENSE](LICENSE).
