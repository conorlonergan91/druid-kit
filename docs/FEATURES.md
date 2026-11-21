# Druid Kit features: expected behaviour

What each part of the addon does today, and rules a tester can check in game. Each section says how to open the
feature, what it does, and an **Expected behaviour** list, including what it never does and what changes in combat.

Words used here:

- **Route**: the list of steps the step window follows (`DruidKitRoute`, generated into `DruidKit_Guide.lua`).
- **In combat**: WoW blocks addons from changing action bars, key bindings and "secure" buttons (buttons that cast
  spells or use items) while you are fighting. Druid Kit either queues such actions until combat ends or refuses them.
- **Reload**: `/reload`. After any bar or key change the addon offers a "Reload now" popup, because changes made by
  addon code can break Blizzard's bars in combat until the UI is reloaded. Nothing reloads by itself.

## Keys and slash commands

Druid Kit ships no default keys (`Bindings.xml` only names the actions). `/dk keys` binds the keys below, out of
combat, and only on keys that are free. Each key is offered once: if you later clear it, `/dk keys` leaves it alone.
All of them can be changed in Options > Keybindings > AddOns > Druid Kit.

| Key (after `/dk keys`) | Action |
| --- | --- |
| Shift+J | Open or close the guide |
| Alt+1 to Alt+8 | Open a guide tab (Now, Quests, Combat, World, Crafting, Help, Talents, Dungeons) |
| Alt+N | Show or hide the step window and its arrow |
| Alt+B | Open or close Bag check |
| Alt+G | Open or close Go to |
| Alt+H | Switch healing / questing mode |
| `` ` `` (under Esc), Alt+W (or Ctrl+W if Alt+W is taken), Cmd+W | Toggle autorun |
| G (else Cmd+F) | Cat Form, once you know it |

| Command | What it does |
| --- | --- |
| `/dk` | Short help. Unknown commands show it too. |
| `/dk bars` | Lay out the action bars and keys (see Action bars). Queued if in combat. |
| `/dk newspells` | Put every known layout spell onto its empty key (caster form only). Queued if in combat. |
| `/dk keymap` | Window listing every key: forms, each bar, Druid Kit keys. |
| `/dk keys` | Bind the default keys above (refused in combat). |
| `/dk catkey [KEY] [force]` | Bind Cat Form to KEY (default G, then Cmd+F). Won't take a used key without `force`. |
| `/dk runkey [KEY] [force]` | Bind autorun to KEY (default Cmd+W). Same rules. |
| `/dk save NAME` / `/dk load NAME` / `/dk list` | Save, load (queued in combat) or list action-bar layouts. `/dk load backup` goes back to before your first `/dk bars`. |
| `/dk heal` / `/dk quest` (`/dk bear`) | Healing or questing mode. Queued if in combat. |
| `/dk healset` / `/dk questset` (`/dk bearset`) | Save the gear you are wearing as that mode's set. |
| `/dk herbs` | Turn Find Herbs tracking back on. |
| `/dk steps` | Show or hide the step window. Also: `/dk steps reset`, `unskip`, `log`, `vendor [kind]`, `vendorprompt`, `keys`. |
| `/dk auto` | Automatic quest accept and hand-in on or off. |
| `/dk arrow` | Route arrow on or off. |
| `/dk bags` | Open or close Bag check. |
| `/dk autosell [on\|off]` | Vendor autopilot on or off (blank = on). |
| `/dk autoroll [on\|off]` | Automatic Greed on or off (off until you turn it on; blank = show which and how to change it). |
| `/dk mount` (`/dk gold`) | Mount money line. |
| `/dk pack [off]` | Dungeon packing in Bank check on or off. |
| `/dk go` (`/dk goto`) | Open or close Go to. |
| `/dk trainers [on\|off]` | Trainer and town pins on the maps (blank = toggle). |
| `/dk party test\|on\|off\|size small\|normal\|big\|reset` | Party view controls (refused in combat; `reset` waits for the end of combat). |
| `/dk catchup [LEVEL\|NAME]` | Catch-up target: a level, a friend or guild member by name, or blank for your highest friend. |
| `/dk tracker on\|off`, `/dk hud on\|off`, `/dk rest on\|off` | Show or hide the helper panels. |
| `/dk unlock` / `/dk lock` | Show the helper panels and party preview so you can drag them / lock them again. |
| `/dk resetpos [NAME]` | Forget where you dragged the windows and put them all (or just NAME) back at their default place now; names what it moved. See Window positions. |
| `/dk dq` (`/dk dungeons`) | Dungeon quest list. |
| `/dk share [on\|off]` | Quest share window; `on`/`off` sets whether it opens when someone joins your group. |
| `/dk questxp [off]` | Quest XP line above the XP bar on or off. |
| `/guide [N]` | Open or close the guide, or tab N. |
| `/way [ZONE] X Y [LABEL]`, `/way clear` | Navigation arrow to map coordinates (`/way` only when no other addon owns it). |
| `/dkway ...` | Same as `/way`, always available. |
| `/claude` | ClaudeProgress: take a full snapshot now. |

## Window positions

Every window starts in one place, chosen so the middle of the screen (your character and the mob in front of it)
stays clear while you fight, and so no two windows that stay on screen overlap. Defaults are measured on a 16:9
screen and anchored to the screen edges or centre, so they follow wider screens; on 4:3 the step window and the roll
box reach into the middle, drag them if they bother you. Drag a window and it stays there (the party view after
`/dk unlock`); `/dk resetpos` puts every window back, `/dk resetpos NAME` just one.

| Name | Window | Default place | Why |
|---|---|---|---|
| `arrow` | Navigation arrow | top centre, under the zone name | travel: where you look while running, above your character |
| `steps` | Step window (Buff button on its bottom row) | bottom right, above the action bars | travel: right side, below the minimap and the game's quest tracker, clear of buffs |
| `tracker` | Catch-up tracker | top right, left of the quest tracker, under your buffs | always on, out of the way |
| `herb` | Find Herbs button | under the catch-up tracker | travel prompt |
| `party` | Party view | left, under your portrait, where the game's party frames are | combat: near the middle, never on it. One column of cards, so its normal size fits the left third of the screen without shrinking the text; turn off the game's party frames (Interface options, Raid & Party) if they show under it |
| `rolls` | Loot roll advice | top centre, at the top edge | combat: rolls come mid-fight; above the arrow |
| `warn` | "AUTO ATTACK OFF" warning | bottom centre, just above the action bars | combat: near the keys you press |
| `rest`, `hud` | Rest prompt, pre-pull check | under your character, above the warning's spot | out of combat only (hidden in combat) |
| `questxp` | Quest XP line | on top of the XP bar (bottom centre without one) | out of combat |
| `guide`, `lore`, `dungeons`, `share`, `goto`, `keys` | Guide, quest lore, dungeon quests, quest share, Go to, key map | top left, where the game opens the quest log and spellbook | reading windows, opened by you |
| `bags`, `bank`, `loot` | Bag check, Bank check, bags-full loot help | right, beside the game's bags | item lists: the bags open with a vendor, the bank and loot (loot help sits next to the loot window when it is open) |

**Expected behaviour**

- Windows that share a place (the reading windows; the item lists) cover each other when two are open, like the
  game's own panels. Opened windows cover the step window and tracker; nothing you open lands on your character.
- `/dk resetpos` forgets every dragged spot (spots saved by older versions too; the guide keeps its size) and moves
  the windows back at once. The party view holds secure buttons, so in combat it moves when combat ends ("after
  combat: party"). An unknown NAME lists the names. `/dk party reset` does the same for the party view.

## Step tracker

**Open:** Alt+N, `/dk steps`, or the **Route** button left on screen when the window is hidden. It opens by itself
at login when a route is loaded, unless you hid it.

**What it does:** shows one route step at a time (accept, do, hand in, go to, fly, hearth, train, learn a flight
path, set the hearth, level, abandon, boss, note), its details, and the next two steps. The navigation arrow points
at the step's spot, taking any "via" waypoints (cave entrance, ramp, bridge) first. Quests on the route are accepted
and handed in for you. Each step tracks time against the plan's estimate, deaths, XP and the path you walk; a log of
every step (`/dk steps log` shows the last 10) is kept for the next re-plan. Each step is logged once, when it is
first finished, whether that is before or after a catch-up, an unskip or a reset; a skipped step is logged as skipped,
and once more with its real time if you unskip it and finish it.

Buttons: **Back**, **Done**, **Skip**/**Unskip**, **Lore** (quest story on parchment, top left), **Keys** (key map), **Hide**;
second row **< Prev**, **Next >** (look without changing anything), **Go** (arrow to the step you're looking at),
**Now**, **Vendor** (arrow to the nearest vendor of a chosen kind in this zone), and **Buff** (uses the next elixir,
flask or scroll whose buff you lack).

**Expected behaviour**

- Accept steps tick when the quest is in your log (also when someone shares it) or already handed in.
- Hand-in steps tick when the game says the quest is done. Do steps tick when every objective is finished.
- Go to steps tick only when you arrive at the route's own arrow target, or when you enter the town (subzone) the step
  names, matched whole in any case ("Goldshire, Elwynn Forest" is Goldshire; "Stormwind" is Stormwind City). The
  zone only counts when the step names the zone itself. Hearth and fly steps match towns the same way. Arriving at a `/way` point, a trainer pin, a map click, a guide **Go** target, a vendor or a **Go** on
  another step never ticks the route; the route arrow comes back when you arrive there, or with **Now**.
- Hearth steps tick when you arrive at the named town. If your hearthstone is set elsewhere, the step warns you.
- Fly steps tick when you take a flight to the named town (or arrive there). Picking another town says which town the
  step wants. Reaching the flight master (the arrow's spot) or opening its flight map never ticks a fly step. If the flight path isn't known, the step warns you to walk.
- Learn flight path steps tick only when that flight path is known (seen on a flight map, needs ClaudeProgress) or
  when you open the flight map at that town's flight master. Another town's flight master does not tick it.
- Train steps tick when you close the trainer the step names, or, if it names none, a druid trainer from the trainer
  pins. A profession trainer, weapon master or riding trainer never ticks it.
- Set hearth steps tick when your hearthstone is set to the named town. Level steps tick at that level. Abandon steps
  tick when the quests are gone from your log. Boss steps tick when that boss dies (encounter end, or the boss is your
  dead target or the corpse you loot), or with **Done**.
- A "Sell ..." note step ticks 4 seconds after you open a vendor. A note step that asks for free bag space ticks when
  you have that many free slots. Other notes tick only with **Done**.
- A travel step is treated as done once the next quest step after it in the same section is done (you got there
  another way).
- **Skip** on a quest step sets every step of that quest aside and records it for the next re-plan; your quest log
  keeps the quest. **Skip** on any other step just ticks it. **Unskip** (after **< Prev** to the step) or
  `/dk steps unskip` brings skipped quests back.
- Skipped quests, and quests the route passed while catching up, are never auto-accepted or auto handed in. Other
  route quests still are.
- Auto-accept only takes route quests from about the current step onwards; auto hand-in takes any other route quest. Hold
  Shift while talking to the quest giver to do it yourself; `/dk auto` turns it off.
- The reward is the one the route names; else the biggest upgrade for your current role; else the one that sells for
  the most. If the rewards can't be read, or one of them can't be compared (an idol, an on-use trinket), you pick: chat
  names the item it can't compare.
- At login, and when a new route loads, the window jumps to just after the last route quest you handed in, within the
  section you are working on. It stops at the first route quest still in your log. A whole earlier section you never
  started is not passed. It tells you how many steps it passed, and if you have quests from a later section.
- A new route keeps the ticks you gave by hand to non-quest steps (matched by step text, not number).
- After 2 deaths on a step, or a long overrun of the estimate, the window suggests grouping up (group quests) or
  **Skip**.
- When 3 or fewer bag slots are free, the window names the nearest known vendor in the zone; the same line goes to
  chat at most every 5 minutes. `/dk steps vendorprompt` turns it off.
- `/dk steps reset` restarts the route; finished steps skip themselves again without being logged twice.
- The arrow warns when you stop getting closer (more than 40 yards away and not 10 yards closer in 30 seconds).
- Dungeon steps marked `inside` show no arrow: the game gives no position inside a dungeon. The arrow is not pointed at
  the step's own spot or at the next step outside, and a route arrow left from before is cleared (an arrow you set
  yourself stays). Their details stay short: the step's how-to, progress for a Do step, then "Next:" with the next
  boss still alive on the route and the first line of its tactic.
- Boss steps read "Boss: NAME (level N)" and list every tactic line the route gives for that fight (the window does
  not cut them, so routes keep it to 3 short lines), then "Ticks when the boss dies, or press Done."
- Other steps end their details with "Level after this step (pessimistic): N" when the route has it: the planner's
  projection (tools/xpsim.py) with Classic quest XP, no rested XP, only the kills quests need and group steps split
  3 ways, so you are usually at or above it. Inside and boss steps don't show it.
- Never: ticks a step from an arrow you set yourself; registers the combat log; changes your quest log selection for
  good (it reads quest text and puts your selection back).
- Combat: the window can move and hide in combat. The **Buff** button is secure: it keeps its item until combat ends,
  and if you hide the window in combat it turns invisible and hides properly after combat.

## Route planner

Not part of the addon. `planner/` holds the tools and agent rules that plan the route the step window follows, and an
eval loop that scores plans. See [planner/README.md](../planner/README.md). The route is written as Python data
(`tools/example_route.py`), checked with `tools/route_check.py`, put into the guide JSON with `tools/build_now.py`, and
turned into `DruidKit_Guide.lua` with `tools/make_guide.py` (see Guide window).

## Guide window

**Open:** Shift+J or `/guide` (toggle); Alt+1 to Alt+8 or `/guide N` for a tab. Also Options > AddOns > Druid Kit >
**Open guide**.

**What it does:** a tabbed, movable, resizable window. Each tab has a jump bar (one button per section) and sections
with an optional **Go** button that starts the navigation arrow. Content comes from `DruidKit_Guide.lua`, which is
generated from JSON by `tools/make_guide.py` (never edited by hand); `/reload` picks up a new version.

**Expected behaviour**

- The window remembers its size, position and last tab. Esc closes it. Pressing a tab's key while that tab is open
  closes the window.
- Hovering a tab shows its Alt key; hovering a jump button shows the full section title.
- **Go** sets the arrow to the section's spot. It never ticks a route step.
- With no guide file the window says so instead of failing.
- At login, if any Alt+1 to Alt+8 tab key isn't set, chat says "type /dk keys". Keys are never bound at login.

## Action bars and keys

**Open:** `/dk bars`, `/dk newspells`, `/dk keymap`, `/dk keys`, `/dk catkey`, `/dk runkey`, `/dk save`/`load`/`list`.

**What it does:** `/dk bars` places a fixed layout: caster bar (keys 1 to =), Bear Form bar, Cat Form bar, Prowl bar,
bottom-left bar (R, Shift+1 to Shift+8) and bottom-right bar (Shift+F), ordered so the most used spells sit on the
easiest keys. Melee abilities go in as small "DK" macros that also start auto attack (`/startattack`); Prowl openers
stay plain spells so stealth isn't broken. It binds R, Shift+1 to Shift+8, Shift+F, F (first form button, Bear Form)
and G (Cat Form by spell). The chat lists each bar's keys.

**Expected behaviour**

- Only spells you know are placed. A layout key whose spell you don't know yet is emptied, and listed in chat.
- The first `/dk bars` saves your bars and every key it takes as the `backup` layout, before changing anything. Later
  `/dk bars` runs keep that backup (adding any key not taken before), so `/dk load backup` always puts back the bars
  and key bindings from before your first `/dk bars`. Only `/dk save backup` replaces it (bars only).
- G is bound to Cat Form only if you know Cat Form and haven't chosen a Cat Form key with `/dk catkey`. A
  `/dk catkey` choice is kept. Once `/dk load backup` puts back the old G, `/dk bars` and `/dk keys` bind Cat Form again.
- `/dk bars` overwrites the keys it uses even if they were bound to something else (they are in the backup).
  `/dk keys`, `/dk catkey` and `/dk runkey` never take a used key unless you add `force`.
- A spell you learn goes onto its layout key by itself about 1.5 seconds later, in caster form only, and the old bars
  are saved as `autosave` first (`/dk load autosave` undoes it). The `backup` layout is left alone.
- `/dk save NAME` saves bars only (no keys). `/dk load NAME` empties layout slots that are empty in the saved layout.
- Saved macros are found by name, so a layout still loads after macros were added or removed.
- After any change a "Reload now" popup appears (after combat if you are fighting).
- Combat: `/dk bars`, `/dk load`, `/dk newspells`, `/dk heal` and `/dk quest` asked for in combat say they will run
  when combat ends, then run in the order asked, each once. For the mode switch the last mode asked wins: Alt+H twice
  in combat changes nothing (no gear swap, no Reload popup; it says the mode stays). `/dk keys`, `/dk catkey` and `/dk runkey` are refused
  ("after combat, please").
- Never: changes bars or keys at login.

Related helpers:

- **Find Herbs**: after login, death or resurrection, Find Herbs tracking is switched back on. If the game won't let
  it, a "Click to turn on Find Herbs" button appears; it hides after the click (only out of combat). `/dk herbs` does
  the same on demand.
- **Auto attack warning**: in Bear or Cat Form, in combat, next to an enemy target and not swinging for 1.5 seconds,
  "AUTO ATTACK OFF: press R" shows in large text. The addon cannot start attacks itself.
- **Key map** (`/dk keymap`, **Keys** button): read live from your bindings and bars.

## Healing mode

**Open:** Alt+H (toggle), `/dk heal`, `/dk quest`. Save sets with `/dk healset` and `/dk questset`.

**What it does:** swaps the caster bar (keys 1 to =) between the questing layout and a healing layout, and puts on the
gear set saved for that mode. Bear, Cat, Prowl and Shift-key bars don't change.

**Expected behaviour**

- Leaving a mode saves that mode's bars; entering a mode restores its saved bars, then fills in any newly learned
  layout spells. The first time in a mode, the guide layout is applied.
- Gear: each saved piece not worn is equipped if it's in your bags. Chat says how many pieces are missing (check the
  bank) or that no set is saved yet.
- Bag check keeps both sets and gear that's better for the other role; Bank check offers to store the other mode's
  gear (except while packing for a dungeon) and to take out the current mode's set.
- `/dk heal` or `/dk quest` for the mode you're already in re-wears that mode's set ("gear re-worn"), with no bar
  change and no reload popup.
- Combat: queued until combat ends, then runs; a mode switch is followed by a reload popup. Asking for the current
  mode with `/dk heal` or `/dk quest` in combat re-wears its set after combat; Alt+H back to it changes nothing.

## Bag check and selling

**Open:** Alt+B or `/dk bags`. The vendor autopilot runs by itself when you open any vendor.

**What it does:** a window with these lists:

- **Upgrades to put on**, with **Equip**. Upgrades also get a tooltip line and a banner when they reach your bags.
- **Use these**: quest starters (right-click), bigger bags, containers with loot, recipes you can learn now.
- **Gear you're keeping**: saved set pieces, gear better for your other role, and gear it can't compare (no stats to
  score for either role, such as idols and on-use trinkets, or an off-hand while you wield a two-hander). Gear that
  scores for only one role (a plain weapon in healing mode) is compared like any other.
- **Cooking ingredients you're keeping**: raw meat, fish and other cooking ingredients that still give Cooking skill
  (see below), with the reason.
- **Bank these**: recipes and other items for a higher profession rank, gear for a higher level, library books, quest
  items needed much later.
- **Quest items to check**: quest items that look like they belong to no quest you have, or that the plan says to
  drop, and quest starters for quests you've already done. Shown only, with no button.
- **Auction House**: items Auctionator's last scan prices well above the vendor price (needs Auctionator).
- **Sell at a vendor**: exactly what the autopilot would sell, with **Sell** and **Sell all** while a vendor is open.
- **Bags full? Drop these first**: up to 5 items, cheapest first, with **Destroy** (or **Sell** at a vendor).

**Expected behaviour**

- Never sold, destroyed or offered: items a quest in your log needs, quest items, library books and Waylaid Crates.
  Quest items that look orphaned appear only under "Quest items to check".
- **Destroy** asks first. When you confirm, it checks the bag slot again and refuses if a different item is there now,
  a different stack size, or if the item has become protected (for example your quest needs it).
- The autopilot re-checks each item just before selling it (same item, same stack size, not protected).
- The drop list's **Sell** (and the Sell list's **Sell**) only sells if the same item and stack size are still in that
  slot, it isn't protected, and a vendor is open.
- Autopilot at a vendor (unless `/dk autosell off`): sells grey junk, gear druids can't use or that's worse than yours,
  items for another class or a profession you don't have (never one you only need a higher rank for), materials none
  of your recipes use, and worse bandages (once you hold 10 of your best bandage). A red "Requires Engineering (150)"
  line on its own doesn't make gear unusable: a rank you'll reach is banked. Then it repairs if you can afford
  it, says what it sold and the mount money line, and reminds you the vendor's Buyback tab can undo it.
- At most 12 items are sold per vendor visit (the Buyback tab's size), counting the autopilot, **Sell**, **Sell all**
  and **Sell junk** together. Past that they sell nothing more and say how many are left; close the vendor and talk to
  it again for the rest.
- The autopilot never sells potions, elixirs, flasks or scrolls, any food or drink, herbs, quest items, library books,
  Waylaid Crates, materials a recipe in your bags uses, Bind on Equip greens or better, anything worth more on the
  Auction House, your saved set gear, gear it can't compare, or your best fishing pole.
- Food and drink: your best 2 food and best 2 drink items you can use now are kept (every stack of each), plus one for
  a later level. Cooked food that gives Well Fed is always kept. Other food is offered in the drop list only.
- Cooking ingredients (reagents of the Classic trainer and common vendor cooking recipes in `DruidKit_Bags.lua`, or of
  any Cooking recipe you know) are kept, never sold, offered in Sell all or the drop list, or stored by Bank check,
  while either: Cooking is below its current cap, or not learned yet (any Cooking trainer teaches it): "Cooking 40/75:
  cook it for skill"; or a recipe you don't know, can learn at your rank and isn't grey yet uses it: "trainable recipe
  Crab Cake uses it" ("vendor recipe ..." for one sold by a cooking supplier). "Trainable" means at any Cooking
  trainer, not one near you. Which recipes you know is read from the Cooking window (open it once after learning
  one). At the cap with no such recipe they are sold like any unused material. If the skill
  list can't be read they are kept. The loot helper says take them, with the same reason.
- Recipes: "learn now", "bank till skill X", "already known" or "not your profession" (sell). A recipe whose
  profession rank can't be read is kept and not listed.
- **Sell junk** (button on the vendor window) sells grey items only, skipping protected ones.
- Every autopilot and Sell junk sale goes to a sold log (last 60) for the next update.
- Combat: **Equip** is refused in combat.

**Loot helper** (part of this file): when your bags are full and you open loot, a box says TAKE or SKIP for each
item and why ("take: can't compare" for gear it can't judge), with a **Destroy** button for your cheapest droppable item (same confirm and re-check as above).
Upgrades, set pieces, green or better gear, and valuable items get an on-screen alert with a sound; if you close the
loot and leave one behind, a "LEFT ON THE CORPSE" alert follows. Nothing is dropped without your click.

## Bank check

**Open:** opens by itself on the right, beside your bags, when you talk to a banker; closes with the bank.

**What it does:** two lists, **Take out** and **Put in the bank**, each with per-item buttons and **Take all** /
**Store all**.

**Expected behaviour**

- Store suggestions: library books, quest items needed much later, recipes and other items for a higher profession
  rank, gear for a higher
  level, gear for the role you're not playing, and materials none of your recipes use (herbs only once your Alchemy
  window has been read; never cooking ingredients Bag check keeps for Cooking skill).
- Take-out suggestions: items your quests need, your current mode's gear set, reagents for recipes that still give
  skill-ups, active quest items, potions, food and bandages, and upgrades.
- It never suggests taking back library books, items needing a higher profession rank, or items it says to bank for
  later.
- **Take**, **Store** and the all buttons check the bag slot again and move nothing if a different item is there now.
- Which materials you use is learned when you open your profession windows (Alchemy, First Aid, Cooking...). Until
  then it asks you to open them.
- Dungeon packing (`/dk pack`, or a route step marked "pack"): everything a dungeon doesn't need is offered to the
  bank. Hearthstone, quest items, consumables and wearable gear stay. `/dk pack off` after the run.

## Loot rolls

**Open:** appears by itself when a group roll starts.

**What it does:** a "Loot roll advice" window: NEED, GREED or PASS with the reason, and Need / Greed / Pass buttons
(the advised one is marked `>Greed<`).

**Expected behaviour**

- NEED only for upgrades for you. A small upgrade that someone else in the party wears is advised as GREED to be
  fair; for a big cloth upgrade it says to ask in party chat first. Bind on pickup gear up to 4 levels above you that
  will be a clear upgrade can be NEED.
- Recipes and crafting materials: GREED. Gear druids can never wear: GREED.
- Gear it can't compare (idols, on-use trinkets, an off-hand while you wield a two-hander), at any level: YOUR CALL,
  with no button marked and no automatic roll.
- Automatic Greed is off until you type `/dk autoroll on`. Older versions turned it on for any `/dk autoroll` but
  `off`, so the first login with this version turns it off once; after that `/dk autoroll on` sticks. When on:
  crafting materials, gear druids can't use, and non-upgrades nobody in the party wears are greeded for you, with a
  chat line saying `/dk autoroll off` stops it. It confirms the bind-on-pickup prompt only for rolls it made itself.
  When off, those rolls show in the window with their advice like any other.
- Never: rolls Need for you, or rolls on anything it didn't advise Greed on (including gear it can't compare).

## Navigation arrow and /way

**Open:** `/way`, `/dkway`, a left-click on a zone or city map (Ctrl+click on any map), a Druid Kit map or minimap
pin, a guide **Go** button, the **Go to** window (Alt+G, `/dk go`), or the step tracker.

**What it does:** a large on-screen arrow with the target name, the distance in yards and a turn word ("bear left",
"behind you: turn round"). It also sets the game's own map waypoint. Trainer pins (Druid, your professions) and town
pins (bank, auction house, flight master, innkeeper, mailbox, Waylaid Crate camp) show on the world map and minimap.

**Expected behaviour**

- `/way 52.7 53.8` uses your current map; `/way Westfall 52.7 53.8 Gryan` names zone and label; `/way`, `/way clear`
  or `/way off` stops. `/way` is only registered when no other addon (TomTom) already has it.
- Within 12 yards it says "you've arrived" and clears. Right-click the arrow to stop; drag it to move.
- Indoors or in a dungeon it says it can't track; on another continent it says so.
- The arrow (and who set it) survives a reload.
- A trainer pin moves to where you stand when you open that trainer; bank, flight master and similar pins are learned
  the first time you use one.
- **Go to** lists the nearest Druid trainer, your professions' trainers and the town services on this continent, a
  Waylaid Crate hand-in if you carry one, **Map icons** (turns on the minimap's town tracking) and **Clear waypoint**.
- Arrivals only tick a route step when the route set the arrow (see Step tracker).

## Party view

**Open:** shows by itself in a party (`/dk party on|off`). `/dk party test` shows a preview of 5 copies of you;
`/dk unlock` lets you drag it.

**What it does:** a card per person (you, party, pets): portrait, health and mana bars with numbers, your Rejuvenation
and Regrowth timers, and up to 7 of your own healing buttons taken from your action bars (one click casts on that
person, with the bar's cooldown). Clicking a card: left targets, right Rejuvenation, Shift Regrowth, Ctrl Healing
Touch, Alt Cure Poison.

**Expected behaviour**

- States are words: "LOW 42%" under 50%, "!! 25%" under 30% with a pulsing card, "DEAD", an "AGGRO" tag on a non-tank
  being hit, "TARGET" on your target. Out-of-range cards are dimmed.
- Fix buttons on the portrait: `!` Mark of the Wild missing, `T` Thorns missing on whoever is tanking (each only once
  you know the spell), `P` poison, `C` curse (both pulse), `R` dead (Revive, or Rebirth in combat).
- Out of combat a fix button only takes clicks while it is shown. The game won't let that change mid-fight, so from the
  start of combat until it ends `P`, `C` and `R` take clicks even while faded: one that appears in combat works at
  once, and a click on a faded one tries the cure or Rebirth on that person (at worst a wasted cast or an error)
  instead of reaching the card. `!` and `T` keep their state for the fight: one that appears in combat becomes
  clickable when combat ends, and one that disappears stops taking clicks then.
- Which spells get buttons is read from your bars out of combat only.
- `/dk party test`, `on`, `off` and `size` are refused in combat; `reset` moves it back when combat ends.
- Cards are in one column (you on top), so it fits the left third of the screen with the middle clear.
- Size: `normal` is as big as fits the left third of the screen and 85% of its height (never past full size, never
  under 0.8 so the text stays readable; about 0.86 on 16:9), `small` 0.8 and `big` 1.2 times that; never wider than
  62% of the screen or taller than it. A size change waits for the end of combat (a reload in combat too).
- A dragged spot is kept in screen units, so a size change doesn't move it (spots from older versions were saved at
  full size).
- Errors are logged to the saved variables instead of breaking the view.

## Helpers: HUD, rest prompt, catch-up, professions

**Open:** shown by themselves. `/dk hud|rest|tracker on|off`, `/dk catchup ...`, `/dk unlock` / `/dk lock`.

**What it does and expected behaviour**

- **HUD (pre-pull check)**: Mark of the Wild, Thorns and Rejuvenation icons (a "!" when missing), health and mana
  (HP below 80% or MP below 70% is "not ready"), enemies nearby from nameplates, "FED" or "EAT: +5% XP" below max
  level, and READY / not ready. Hidden in combat and while dead.
- **Rest prompt**: "Eat & drink" when HP is under 70% or MP under 50%, "Resting" while eating, "Ready" when back to 95%
  / 90%. Hidden in combat.
- **Catch-up tracker**: your XP per hour (last hour), time to the next level, and how far you are behind the target.
  The default target is your highest saved friend (friends list and Battle.net friends in WoW). Guild members are
  never saved as friends (only findable by name this session), and the addon never removes anyone from your saved
  friends, even when they go offline, leave your list or are in your guild.
  `/dk catchup 22` targets a level; `/dk catchup NAME` targets a friend or guild member by name (start of the name is
  enough), and says if they can't be found. Blank goes back to the default. Gap advice appears for a named or friend
  target.
- **Professions** (in the tracker): "! Train", "! Expert" or "! Capped" lines for Alchemy, Cooking, Fishing, First
  Aid and Herbalism when you are near the rank cap, with where to train. A gold line counts towards the 100g riding
  at level 40 against the same per-level target as the mount money line (`/dk mount`): on track, or BEHIND by how much.
- Level up: a banner, a talent point reminder, new spells on even levels, and how many quests in your log turned grey.
- Gear under 50% durability: one on-screen warning until repaired. 2 or fewer free bag slots: a warning at most every
  5 minutes.
- Never plays for you: these are reminders only.

## Dungeons

**Open:** `/dk dq` (or the guide's Dungeons tab), `/dk share`, `/dk questxp`. Boss steps live in the step tracker.

**What it does and expected behaviour**

- **Dungeon quests** (`/dk dq`): dungeons near your level with quests left, each quest marked done (hidden), ready to
  hand in, in your log, available or locked (with the reason: level, or the quest to do first), its XP, and where it
  starts. **Go** sets the arrow to the quest giver for available or locked quests.
- **Quest share** (`/dk share`): your dungeon quests that someone in your party lacks, with **Share** and **Share all**.
  It opens by itself when someone joins your group and there is something to share (at most once a minute);
  `/dk share off` stops that. Not used in raids.
- **Quest XP line**: above the XP bar, "Quests to hand in: N · +XP · level X after" for completed quests in your log.
  `/dk questxp off` hides it.
- Data comes from `DruidKit_DungeonData.lua`, generated from QuestieDB data (see NOTICE). Quest XP uses Questie when
  it is loaded.

## ClaudeProgress exporter

**Open:** a separate addon; `/claude` takes a full snapshot. WoW writes it to disk on `/reload` or logout.

**What it does:** saves the character's state to `ClaudeProgressDB`: level, XP, money, position, quests and
objectives, skills, talents, action bars, gear, bag gear, quest rewards, completed quests, flight paths and hearth,
bags, bank, recipes and durability. Druid Kit reads the known flight paths from it for flight steps.

**Expected behaviour**

- A quick snapshot is taken at login and every 60 seconds. It never touches the quest log: no headers opened, no quest
  selected. Quests under collapsed headers are kept from the previous snapshot, and quest rewards from the last full
  pass.
- A full pass runs at logout and on `/claude`: it opens collapsed quest headers, reads every quest's rewards, then
  collapses the headers again and restores your selection. In combat, `/claude` takes a quick snapshot instead.
- While the game is quitting and bags or XP read as empty, the previous good snapshot is kept.
- The bank is saved while it is open; recipes when you open a profession window; flight paths when you open a flight
  map; talents when they change.
- Never changes anything in game.
