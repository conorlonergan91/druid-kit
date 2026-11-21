# Routing rules (v1-v19)

## Base rules (v1)
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
  and a boat/flight), count the quests and quest XP available in the band from 4 levels below you to 3 levels
  above you (you grow into a hub's higher quests during the stay; `hubs` charges more time for them). Pick the hub with the most XP per hour of travel+questing. Quests 1-4 levels below you are the
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
  - Choosing a NEW hub (travel cost): use the band from 4 below to 3 above your level *on arrival* (what `hubs`
    ranks), and compare hubs at the level you'll actually be when you get there.
- So the move to a new hub usually happens later than "when the easy quests run out": first squeeze the current
  hub's higher quests, then travel.

## Added in v5: use the tools, don't do the maths in your head
You have `planner/rk.py` (run `python3 planner/rk.py` for help). It knows quest givers, hand-ins, objective spots, mob
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

## Added in v9: from the first real step logs
- Say *how*, not just what: when an objective needs an item (a banner, a torch, a quest item you looted), the step
  names it ("use the banner you picked up in the cave"); for caves, towers and high ground give the entrance and the
  way up ("go round the east side to reach the ledge"). If the data doesn't say, leave `how` empty: the step
  window shows the quest's own objective text instead.
- Fight on the way: about 40% of levelling XP comes from kills. Routes cross mob areas instead of roads where it
  costs little, and a step tip says to kill even-level mobs on the path. A stretch that is mostly talking and
  travelling (city errands, deliveries, tram rides) is grouped into one visit and kept short.
- Calibrate with `rk.py calibrate DruidKit.lua` after each session: if travel is over ~60% of play time, the next
  plan favours denser kill hubs and fewer errands.
- Paths: steps can carry `via` waypoints (cave entrances, ramps, bridges) that the arrow takes in order. The addon
  records the path actually walked on every step; `rk.py paths DruidKit.lua` turns bent walks into `via` lists, so
  each place you had to find the way to gets waypoints in the next route. The arrow also says when you've stopped
  getting closer for 30 seconds.

## Added in v10: only travel the player can really use (from play: no flight path, no hearth set)
A flight or a hearth the character doesn't have turns into a long walk. The route must earn every one of them.
- Start from the save: `travel.home` (where the hearthstone is set), `travel.flights` (known flight paths) and
  `travel.hearthCooldown`. In a plan, put them in `"start": {"home": ..., "flights": [...], "at": ..., "level": ...,
  "accepted": [...]}`; with a route file, pass them to `tools/route_check.py --home ... --flights ...`.
- Learn every flight path you pass. The first time the route reaches a town with a flight master (`fm: true` in
  `travel.json`), add an `fp` step / event there, even if you won't fly from it today. It costs half a minute and
  turns every later visit into a flight. Never write a `fly` to or from a path that isn't known or learned earlier.
- Set the hearth on purpose. Before any trip that will come back (a class trip via Teleport: Moonglade, a dungeon,
  a city errand), add a `home` step in the hub you'll return to, *before* you leave it. Never write a `hearth` step
  unless the hearth is set to that town at that point. The default home is the hub you'll quest in next.
- One hearth per hour (cooldown): don't plan two hearths within 60 minutes. If one is needed sooner, use Teleport:
  Moonglade plus a flight, or walk, and say so.
- No hearth or flight path: plan the walk honestly (road, minutes, danger), never "hearth back" as a placeholder.
- `rk.py sim` now reports `flight_paths_learned`, `home_at_end` and problems for: flying to an unlearned path,
  hearthing with no or the wrong home, hearth on cooldown, and walking through a flight-master town without `fp`.

## Added in v11: transport the player can follow (from play: two flights where the route said one; boat with no directions)
- Flights: run `rk.py travel FROM TO --flights "<known>"`. One `fly` step may go several links (the game flies on
  through known flight points: Stormwind -> Menethil goes through Ironforge; its `how` says "pick X on the map")
  when every point on the way is known and every link is a regular flight (route_check allows it, v19). Special
  flights stop: Nighthaven (druid flight) only flies to Rut'theran, and nothing flies to Nighthaven (arrive by
  Teleport: Moonglade); write each such leg as its own `fly` step.
- Prefer the Stormwind <-> Ironforge gryphon over the Deeprun Tram when both flight paths are known (21 Nov).
- Boats, trams, portals and zeppelins get a `how`: where to board (pier, platform or tree, with `goto` only when
  the spot is verified), how to tell the right ship (its destination; two ships share some piers), the usual wait,
  the trip time, and where you get off. `rk.py travel` lists the boarding spot and wait for each boat leg.
- Every walk between zones gets a `how` too: the road, the pass, what to avoid off the road.
- `tools/route_check.py` flags a fly step whose chain isn't all known regular flights (error; pass the save's
  `--flights`, or a chain the save knows is reported as missing) and a transport step without `how`.
- Quests to drop are an `abandon` step (`qs=[ids]`), not a note: it ticks itself when they leave the log.
- Every walk or transport step has a `goto` or is followed within 4 steps by one; the arrow then points at the
  next spot. A new route id no longer restarts the player: the tracker catches up to the last handed-in quest.
- Quests started by an item (`start_item: true` in `rk.py quest`): the step says "open your bags and right-click
  <item> (This item begins a quest)". Picking the item up does not start the quest.
- When the quest text names a different hand-in NPC than the data, name both in the step and point at the one
  the quest text names.
- Collect-items steps (objects on the ground) get a `via` chain over every known spawn of the object, in walking
  order, from the QuestieDB object spawns; the step names the quest giver and hand-in NPC too. (Player: "the NPC
  and individual collectable waypoints helped a lot".)

## Added in v12: bag space (from play: bags filled up with a vendor nearby, the player dropped loot)
- On update, if the save has fewer than 8 free bag slots, the first step is a sell stop at the nearest vendor on the
  way (`rk.py vendors --zones ...`), with the items to sell named from the save.
- Every hub visit and every long kill stretch (~45 min) ends at a vendor: add a "Sell grey items and spare
  food" note at a town or camp vendor on the path (camps count: e.g. the clothier at Ironband's Excavation).
- The step tracker names the nearest vendor itself when bags drop to 3 free; build `vendors.json` for every zone the
  route visits so it knows them (`rk.py vendors --zones "A,B" > build/vendors.json`).
- Quest items needed much later (RULES v12b, player request): `rk.py itemplan state.json route.py >
  build/items.json` on every update. An item for a quest the route doesn't do goes to the bank at the next bank on
  the route; a quest-start item that drops again (QuestieDB objectDrops/npcDrops) is dropped instead when its quest
  isn't planned. Items the route still uses stay in the bags. The bag check and bank check show the advice.
- Before telling the player to abandon a quest, check where its chain leads (`quest ID` -> next in chain, rewards).
  Object-started hidden chains (e.g. the Cozy Sleeping Bag: a Westfall cart note that leads across five zones) look
  like stray deliveries but pay off in XP, bags and a permanent XP buff.
- Forever-new quests (ids 8xxxx-9xxxx) can have prerequisites QuestieDB doesn't list (player 18 Nov: Oslow offered
  Alther's Mill only after The Everstill Bridge). When a giver has other quests, plan the new quest's accept after
  those are handed in, and the step tip says it may need the earlier quest first. Record what play shows in
  knowledge/facts.json.

## Added in v13: what the player enjoys (19 Nov: "not a fan of kill loads of monsters to collect X loot")
- Collect-from-kills quests (items that drop from mobs) cost 1.4x their minutes in `rk.py` (DROP_DISLIKE). Prefer
  chains, deliveries, kill-count, object and dungeon quests when XP/h is close.
- Keep a drop quest only if it unlocks a good follow-up (Blackrock Menace -> Shadow Magic, Tharil'zun) or shares
  its mobs with another quest (Murloc Poachers + Selling Fish). Drop it (abandon step) when its mobs are 2+ levels
  above the player or the step log shows deaths there.
- Quest chains that pay a lasting reward (Cozy Sleeping Bag: +3% XP, rest anywhere, two 12-slot bags) are worth
  their travel; fold their steps into trips the route makes anyway.
- Money (mount at 40 = 100g): every update reports gold vs the mount target; sell stops before long trips; the
  addon sells junk and unusable items and repairs at every vendor by itself.

## Added in v13b (19 Nov, player: "drops are even lower in a party; too much fighting and dying")
- No "collect N items from kills" quests at all when N > 3 (`rk.py` SKIP_DROPS, MAX_DROPS = 3). A named mob's head
  or a few items is fine. Kill-count quests are fine (counts are shared in a group). Object/search, delivery and
  story chains are preferred.
- No solo fights with mobs 2+ levels above the player; group-only kills (Fangore, Tharil'zun) are left out unless the
  player has a group.
- When a hub is mostly drop grinds, leave it (abandon step) for a hub with deliveries and kill counts (19 Nov:
  Redridge -> Duskwood).

## Added in v13c (19 Nov, player: "fine when they're easy to pick out on their own and don't run away; the ones that
## hang out together and murder you are annoying")
- `rk.py crowd ID...`: average other mobs within 15 yards of a quest's target spawns. Kill/drop quests with 2.0 or more
  (camps: Blackrock 6.4, Shadow Magic 8.6, Mosshide gnolls 2.5, Shadowhide 2.2) are left out (SKIP_PACKS); open
  beasts score under 1 (Duskwood wolves 0.85, spiders 0.7, Wetlands raptors 0.5).
- Humanoids that flee at low health (gnolls, murlocs, orcs, Defias, kobolds...) cost +25% time; beasts and undead don't
  flee. Between 1.5 and 2.0, the step tip says "pull one at a time".

## Added in v14 (20 Nov, player: little XP from the Deadmines; friend 37)
- Every dungeon section starts with "Before the dungeon: sell, repair and bank" (20+ free slots).
- Take every dungeon quest before the run (prerequisite chains included; check NPC spots such as upstairs rooms).
- Forever dungeon XP rule (15 Nov hotfix): the whole party gets 0 XP from a mob if ANY member is more than 12 levels
  above that mob. With a higher friend (level F), only dungeons whose mobs are >= F-12 pay kill XP.
- Weapon skills: a druid must train Maces, Two-Handed Maces, Fist Weapons, Polearms; plan a weapon master stop the
  first time the route is in a capital, and never call an untrained weapon an upgrade.
- Flight paths for dungeons: learn Ratchet (WC, RFK), Astranaar (BFD), Southshore (SFK, Dalaran, SM, Ruins of
  Lordaeron), Refuge Pointe; Menethil/Thelsamar/IF cover Excavation Site and Gnomeregan.
- Pack for every dungeon at the last bank before it (step with pack = true): only hearthstone, consumables, quest items and gear stay in the bags; a 'take back' bank step follows the hand-ins.

## Added in v14b (20 Nov): "go to the dungeon" means a dungeon-first route (see AGENT.md flow)
- Healer by default: heal mode, healing set, party view, drinks, then pack and 20 free slots.
- Every travel step that only exists to reach a quest giver carries onlyFor = {ids}; friends sharing quests make
  those steps and the accept steps tick themselves (shared route quests are auto-accepted).

## Added in v15 (20 Nov, player: "you were wrong but Questie had the right marker")
- Every step spot comes from planner/db.json (QuestieDB Forever): NPC spawns for accept/hand-in/train, quest
  target_center for objectives. Run coordcheck (tools/coordcheck.py ROUTE) before deploy: any spot more than 1.0 from the
  data is wrong. Never take coordinates from Classic-era web guides: Forever's Stormwind map uses different
  coordinates (Maldryn 34.4,65.2; Woo Ping 63.9,69.1; tram 66.4,35.0).
- Weapon masters: Woo Ping (Stormwind) teaches polearms/staves/daggers for druids; Buliwyf Stonehand (Ironforge
  Military Ward 61.2,89.5) teaches maces, two-handed maces and fist weapons.
- Dungeon portals on hills get a 'via' at the start of the path (Excavation Site: path at Thelgen Rock 53.9,65.4,
  portal 47.9,56.5).

## Added in v16 (20 Nov, player: "speed routes take quests with lower-level enemies; yours are higher; I keep dying")
- Solo steps: no hostile monster 3+ levels above the player within 3 map units of the step spot (tools/dangercheck.py
  ROUTE LEVEL). Quest XP does not depend on the monster level, so the fast choice is the
  quest whose monsters are at or below your level.
- Steps that fail the check either go to a party step (a group or a higher friend) or out of the route. Duskwood failed it at 22
  (Raven Hill cemetery 25-31, Defias 25-27 at Sven's farm and near Dodds): 4 deaths on 20 Nov.
- Grind steps name only monsters at or below the player's level.
- (v16c) Before a step uses a Forever-new quest, check its giver's other questStarts and the preQuestSingle chain in
  db.json: Karl Boran gives Return the Statuette (98189) only after the classic chain 281 > 284 > 285 > 286.
- (v16e) Run tools/prereqcheck.py ROUTE DONE.json LOG_IDS before every deploy: each accept needs its preQuestSingle
  (one of) / preQuestGroup (all) done or handed in earlier in the route. Karl Boran's chain: 279 > 281 > 284 > 285 > 286 > 98189.

## Added in v18 (21 Nov, player: "with the raptor quests and the extra ones I can't still be short of 24")
- Every route runs through tools/xpsim.py before release (build_now.py ... --xp LEVEL XP DONE.json does it and
  writes "lv" into every step). Pessimistic by rule: Classic quest XP from the data (Forever values only where
  published, rk.PUBLISHED_XP), the grey-quest cut, only the kills a quest needs, no rested XP, group steps split 3 ways,
  about one bubble (1.25% of the bar per boss) for a dungeon run.
- No 'level' (grind) step unless the projection is short of the level a later step needs; size it to the gap.
- An accept whose quest needs a higher level than projected is a release blocker (xpsim ERROR).
- The Now tab shows "-> level" after each hand-in, kill and boss step; the step window shows "Level after this step".
- Release gate for every route (qa-gatekeeper): coordcheck, dangercheck, prereqcheck, xpsim, route_check, tests.

## Added in v19 (21 Nov, review of this week's play): every new route starts from these
- Default plan: dungeon-first as a healer with groups of strangers, quests between runs (v14b). Find a group with
  the Group Finder (I) as Healer first, then a chat LFG line.
- Collect every dungeon quest, pre-quests on the route's path included (v14).
- No collect-from-drops quests needing more than 3 items (v13b).
- No packs (v13c, SKIP_PACKS). Fleeing humanoids: avoid them in solo steps; `rk.py` only prices them +25% (v13c).
- No monster 3+ levels above the player in solo steps (dangercheck, the gate); prefer at or below his level. Higher
  only as `party` steps with a group (v16).
- Flights over the tram: the Stormwind <-> Ironforge gryphon when both paths are known (v11). One `fly` step may
  chain through known regular flight points (v11).
