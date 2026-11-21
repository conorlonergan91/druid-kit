# Route planner

This folder holds the tools and agent instructions that plan the levelling route the addon's step window follows.
The split is simple: an LLM agent makes the routing decisions, and `rk.py` does the arithmetic for it (distances,
travel times, stop order, XP and time estimates, training and grouping). An eval loop scores the agent's plans so the
rules can be improved in a general way rather than by hand-tuning one route.

```
planner/
  rk.py           CLI: quest facts, hub ranking, stop ordering (TSP), clustering, party value, plan simulation
  load_db.py      builds db.json + data/ from a QuestieDB clone (not committed: GPLv3 data)
  travel.json     towns, boats, flights, portals with minutes; zone sizes in yards (hand-made estimates)
  RULES.md        the planning rules the agent follows (v1-v19, one section per version)
  TASK.md         the planner agent's task and output format
  AGENT.md        the agents (one job each, defined in ../.claude/agents/), flows, hand-off files and gates
  ROUTING.md      routing decisions distilled from studying good routes (no route text copied)
  eval/           blind-eval tools: quest pack, reference builder, scorer
```

## Setup

```sh
pip install lupa
git clone --depth 1 https://github.com/Questie/QuestieDB /tmp/QuestieDB
python3 planner/load_db.py /tmp/QuestieDB      # writes planner/db.json and planner/data/
python3 planner/rk.py                          # prints the commands
```

`db.json` merges QuestieDB's WoW Forever data with its Forever corrections and the crowd-sourced traces Questie users
report (custom Forever quests, real NPC and object spots). About 5,900 quests.

## Commands

| Command | What it answers |
|---|---|
| `quest ID` | giver, hand-in, objective spot, kill estimate, mob level, elite, XP |
| `available --level L --done F` | quests you can take now, by zone |
| `hubs --level L --from TOWN --current ZONE --done F` | XP/hour per hub over your stay (-4..+3 levels), trip time included, plus a grind baseline and `opens_at_level` |
| `loop --zone Z --from TOWN --level L --quests ...` | stop order: nearest neighbour + 2-opt with accept-before-do-before-hand-in precedence |
| `cluster --quests ... [--radius YD]` | objective areas close enough for one outing |
| `crowd ID...` | mobs packed round a quest's targets and whether they flee (RULES v13c) |
| `party --level L [--party N] --quests ...` | where grouping pays in a group of N (default `GROUP_SIZE` = 3, as xpsim; kills shared, mob XP split) |
| `travel A B` | minutes between towns (Dijkstra over runs, boats, flights, Teleport: Moonglade) |
| `sim plan.json` | replays a plan: level reached, hours, hours to 20, trainer visits, missed spell ranks, forms, problems |

## The model (rough by design, good for comparing options)

- Run speed 7 yd/s; quest drops ~45%; kill time scales with level difference; pure grinding 1.8x slower than
  kills done while questing.
- Classic quest XP penalty above +5 levels; mob XP `5L+45` adjusted by level difference.
- Power: each untrained even-level spell rank makes fights ~5% slower (cap 35%); Bear Form ~12% faster,
  Aquatic Form 3%, Cat Form ~8%. Training trips cost real travel to the cheapest trainer.

## Results so far

Blind plans for a Night Elf Druid, scored against a strong reference route on levels 1-20
(selection F1 45%, order 25%, zone sequence 20%, hearth spots 10%), averaged over 3 runs:

| Rules | Match | Simulated hours to 20 | Spread |
|---|---|---|---|
| v6 (tools, 1-20 horizon) | 71.3 | 14.5 | 68.6-73.8 |
| v8 (1-30 horizon, training and forms modelled) | 70.1 | 13.6 | 69.8-70.4 |

v8 diverges from the reference on purpose at 18-19 (it saves Redridge for 22-24 because it plans to 30) and is
faster and steadier by the simulator's estimate.
