# Druid Kit UI style

One look, one way of saying things, one key map. Owners: **ui-ux-reviewer** (look and wording) and
**keybind-manager** (keys). `python3 tools/ui_audit.py` checks the code against this file; `tests/ui_test.py`
fails when a change adds a new finding (the current backlog is in `docs/ui_baseline.json`).

## The player

Colour-blind and eyesight not great; plays on a Mac, often reads replies on a phone. So: big, clear text; every
state is a word (+ icon or sound); colour is only ever a second signal.

## Text

| Use | Size | Notes |
|---|---|---|
| Alerts in the middle of the screen | 24, THICKOUTLINE | RaidWarning style; words + sound |
| Main line (what to do now) | 15-16 | white |
| Body, list rows, buttons' tooltips | 13-14 | light grey or white |
| Secondary (headers, "Then:", reasons) | **13 minimum** | never below 13 |

- Font: `Fonts\FRIZQT__.TTF` with `OUTLINE` everywhere. Never named templates (GameFontHighlightHuge).
- Sentences: verb first, short ("Sell it", "Right-click it in your bags"). Numbers and names, not vague words.

## Colours (always paired with a word)

| Colour | Code | Means | Paired word |
|---|---|---|---|
| Orange | `ff7c0a` | alert, stop title | "BAGS FULL", "WARNING" |
| Green | `7fd35b` | labels, go, take | "TAKE", "Done", "+12" |
| Yellow | `ffd100` | quest and item names, actions | the name itself |
| Grey | `9d9d9d` | coordinates, later, done | "(later)", "(done)" |
| Red | `ff6060` | danger, skip | "SKIP", "danger" |
| Blue | `3fc7eb` | water | "underwater" |

## Panels

- Every window and box is built with `DruidKit_Style` (`S.window`, `S.header`, `S.item`, `S.note`): same backdrop,
  border, title bar, close button, drag to move, position saved.
- Strata: windows `DIALOG`; always-on pieces (step window, arrow, HUD) `MEDIUM`/`HIGH`; alerts `HIGH`.
- Width: list windows 360; boxes next to Blizzard frames anchor to them (loot help next to the loot window).
- In combat: no Show/Hide on protected frames (alpha instead); no SetPoint to textures.

## Buttons

| Kind | Size | Examples |
|---|---|---|
| Standard | 64 x 22 | Done, Skip, Sell, Equip, Go |
| Wide | 96 x 22 | Sell junk, Sell all |
| Compact row (step window, 5 across) | 64 x 20 | < Prev, Next >, Go, Now, Vendor |
| Full width (one per box) | box width - 20 | Destroy <item> |

- Label = the action in one or two words; tooltip = what happens and how to undo it.
- Destructive actions ask first (StaticPopup). Nothing is sold, destroyed or equipped without a click.

## Alerts

`RaidNotice` text (words) + a sound + a chat line with the same words. At most one alert of a kind per minute.
Examples: "BAGS FULL, but this loot is worth taking: …", "Starts a quest: …", "LEFT ON THE CORPSE: …".

## Key map

Player's key ease: 3 easiest, then 2/4, then 1/5; 6 and beyond are a stretch. Bindings never change at login or in
combat; a change ends with the reload prompt (taint rules).

| Key | Binding | Does |
|---|---|---|
| Shift+J | DRUIDKIT_TOGGLEGUIDE | guide window |
| Alt+1 … Alt+8 | DRUIDKIT_TAB1, DRUIDKIT_TAB2, DRUIDKIT_TAB3, DRUIDKIT_TAB4, DRUIDKIT_TAB5, DRUIDKIT_TAB6, DRUIDKIT_TAB7, DRUIDKIT_TAB8 | guide tabs (Now, Quests, Combat, World, Crafting, Help, Talents, Dungeons) |
| Alt+N | DRUIDKIT_STEPS | step window and arrow on/off |
| Alt+B | DRUIDKIT_BAGS | bag check |
| Alt+G | DRUIDKIT_GOTO | Go to window |
| Alt+H | DRUIDKIT_TOGGLEMODE | healing / questing bars and gear |
| Option+W (or Ctrl+W) | TOGGLEAUTORUN | autorun (set by /dk keys) |
| Shift+1 … Shift+8, Shift+F | action bar slots | bar layouts (/dk bars) |

Step window buttons: Back · Done · Skip · Hide (row 1); < Prev · Next > · Go · Now · Vendor (row 2).

Slash commands: `/dk steps` (`reset`, `unskip`, `log`, `vendor`, `vendorprompt`), `/dk auto`, `/dk arrow`,
`/dk bars`, `/dk keys`, `/dk heal`, `/dk quest`, `/dk healset`, `/dk questset`, `/dk save|load|list`, `/dk herbs`,
`/dk go`, `/way`, `/guide`, `/claude`.

## Review checklist (ui-ux-reviewer, for every UI change)

1. `tools/ui_audit.py`: no new finding.
2. Every new state has a word; colour only repeats it.
3. Text 13+; the main line readable at a glance.
4. Built with DruidKit_Style; standard button sizes; tooltip says what happens.
5. New key or button: in this key map and in the guide's Commands/Help tab (guide-writer).
6. No new key collides with a default WoW binding the player uses; taint rules respected.
