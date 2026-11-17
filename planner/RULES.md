# Routing rules (v1)
- Follow quest density, not zone level ranges: work a hub until it runs thin, then leave in one planned trip.
- One trip, many jobs: every long trip also picks up flight paths, trains, shops, hands in class quests and accepts the next hub's quests.
- Hearth is a free teleport: set it in the hub you'll return to; hearth only from the far end of a cluster.
- Batch at hubs: accept everything in one visit, hand everything in in one visit.
- Overlap objectives: kill/loot for several quests in the same area on the way; collect items before you have the quest.
- Cut low-value quests (long walks for small XP, solo elites, off-route turn-ins, dungeon quests without a likely group) by abandoning them.
- Level gates with small explicit grinds ("grind to 18 and 75% at <spot>") next to the next hand-in, never low-XP filler quests.
- Buy quest items and cheap upgrades from vendor/AH when faster than farming (after a money check).
- Class detours only ride on trips already planned (Teleport: Moonglade, Darnassus flights); train whenever passing a trainer.
- One interaction per step, NPC named, coordinates for every place, a warning only where it's dangerous; rewards chosen in the step.

## Added in v2 (general lessons from scoring)
- Choosing the next hub: for each candidate hub (including ones on the other continent, reached through a capital
  and a boat/flight), count the quests and quest XP available in the band from 4 levels below you to 1 level
  above you. Pick the hub with the most XP per hour of travel+questing. Quests 1-4 levels below you are the
  fastest XP there is (quick kills, little risk, still full green XP); prefer a hub full of them over a hub of
  quests above your level.
- When a zone's remaining quests are mostly above your level, or need a long walk each, leave early rather than
  grind towards them. Don't push into a higher zone just because it is the "next" zone on the map.
- Free XP is never cut: quests started by clicking objects or items (wanted posters, books, washed-up items,
  crates), deliveries and breadcrumbs that point where you're going anyway, and quick profession/cooking/fishing
  starter quests near your path. Cut by XP per minute, not by type; these are short and high value.
- Class quest chains: take every class-quest step whose giver and hand-in are in places you already visit (they
  are cheap XP), plus anything that gives combat power. Abandon an optional utility chain (travel forms, poison
  cure) at the first step that would need a trip of its own; the trainer visits you make anyway are the only
  class trips.
- Escorts and long chains whose next step is in another zone: take only if the next step lands where you are going.
- Capitals are hubs too: when passing through, accept every quest that starts there for your next hub, train, and
  hand in deliveries.
- Count trips: every return to a hub you've left must carry several hand-ins or a class-required visit. Aim for
  one visit per hub per level band.

## Added in v3
- Estimate time per quest by level difference, not a flat number: about 4 min when the quest is 3+ levels below
  you, 6 min at your level, 8-10 min when it's above you. Low-level hubs are faster than their XP total suggests.
- Tie-breakers between hubs within ~35% of each other: prefer the one reached through the capital where you
  train and pick up other quests (the trip does double duty), the one whose hand-ins all sit in one town with a
  flight path, and the one with a dungeon or chain pick-ups that will pay off later.
- Starting area clean-up: quests that start and end inside the area you're already working (including short
  "plant/deliver this" follow-ups) stay in; cut only those that need a separate return trip.

## Added in v4
- Two different level windows:
  - Finishing the hub you're in (no travel cost): quests up to 3 levels above you are fine solo, and quests that
    become available as you level stay on the list. Don't leave a hub while it still has reachable quests you
    can do within that window; take them in order of level as you grow into them.
  - Choosing a NEW hub (travel cost): use the band from 4 below to 1 above your level *on arrival*, and compare
    hubs at the level you'll actually be when you get there.
- So the move to a new hub usually happens later than "when the easy quests run out": first squeeze the current
  hub's higher quests, then travel.

## Added in v5: use the tools, don't do the maths in your head
You have `tools/rk.py` (run `python3 tools/rk.py` for help). It knows quest givers, hand-ins, objective spots, mob
levels, quest XP, travel minutes (boats, flights, roads) and a time/XP model. Let it do the arithmetic; you make the
decisions.
- Keep `done.json` (list of handed-in quest ids) up to date as you plan.
- At every "where next?" moment run `hubs --level <L> --from <town> --current <zone> --done done.json`. Use its
  XP/hour ranking with the v2-v4 rules (tie-breakers, double-duty trips). `opens_at_level` tells you when a hub
  becomes worth it: plan to arrive at that level, not before.
- Inside a hub: `available --level <L> --done done.json` for the candidates, `cluster --quests ...` to see which
  objectives share an area (do them on one outing), then `loop --zone <Z> --from <town> --level <L> --quests ...`
  for the stop order. Write the plan in that order; batch accepts and hand-ins at the town.
- Quests with `spot_known: false` have unknown objective spots: keep them only if cheap.
- `party --level <L> --quests ...` shows where grouping with strangers pays (kills are shared; quest mob XP is split).
  The plan stays solo, but add a `{"kind": "travel", "text": "LFG: ..."}` note before quests it flags as worth
  grouping, and keep elite quests only if that note makes them realistic.
- When finished, run `sim plan.json`; fix every problem it lists (prerequisite order, level gates).

## Added in v6
- `hubs` now values each hub over your whole stay (quests from 4 below to 3 above, the higher ones costing more
  time) and adds deliveries/breadcrumbs that start in a capital or your current hub and end in that hub. Trust its
  ranking over "it's the next zone on the map"; a capital on the way (training, many new pick-ups) counts for the
  hub it leads to.
- Class quests that open at a level you reach inside the plan (e.g. a form/ability quest at 20) are milestones:
  look them up with `available` at that level and end the plan with them if they open by 20.
- Quests flagged `forever_new: true` are part of this game; treat them like any other quest.

## Added in v7
- Plan with the horizon in mind: before leaving a hub in the high teens, run `hubs` at your arrival level AND at
  ~3 levels higher. Prefer a direction whose zones keep paying for the next several levels (one region you can
  stay in: e.g. a capital plus neighbouring zones with flight paths) over a slightly better one-off zone that you'd
  have to leave again soon.
- Escorts and deliveries that point into a zone are not a reason to go there. Re-run `hubs` first; take them only
  if that zone wins on its own (or they end where you're going anyway).
- Dungeons stay out (solo plan), but quests whose objectives are outside dungeons are fine.

## Added in v8: getting stronger is part of the route
Speed comes from power as much as from routing. `sim` now models it and reports `trainer_visits`,
`untrained_ranks_now`, `slowdown_from_missed_training_min` and `forms`:
- Druid spell ranks come at every even level from 4. Each trainer level you skip makes fights ~5% slower (up to 35%).
  Trainers: Shadowglen, Dolanaar, Darnassus, Nighthaven (Moonglade) and Stormwind. From 10, Teleport: Moonglade
  reaches Nighthaven from anywhere in seconds, then hearth back — so a training trip costs about two minutes plus
  a hearth. Put a `{"kind": "train"}` event at least every 2-4 levels, ideally right before a hearth or when
  passing a trainer anyway; never let `untrained_ranks_now` sit above 1 for long.
- Class quests that grant forms change speed for the rest of the route: Bear Form (Body and Heart, 10) ~12%
  faster fights, Aquatic Form (16) faster travel along coasts, Cat Form (The Great Cat Spirit chain, 20) ~8%
  faster. Do them as soon as they open, riding on a training trip.
- Talent points arrive by themselves each level from 10; they need no trip. Note in the summary which tree you
  assume (Feral for solo speed).
- Professions: take the free Camping 101 / First Aid starters; First Aid (bandages) cuts downtime, and
  skinning/herbalism pay for training and upgrades along the route. Train profession ranks only at trainers
  you're already passing.
- Weapon upgrades: on town visits where a vendor sells a clearly better weapon (staff/mace) for your level, add a
  `{"kind": "travel", "text": "Buy <item> from <vendor> if your weapon is worse"}` note. No extra trips for it.
