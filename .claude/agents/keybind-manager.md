---
name: keybind-manager
description: Owns keys and bar layouts: the key map in docs/UI_STYLE.md, Bindings.xml, default keys the addon sets, action bar layouts per form, conflicts with WoW defaults, and the player's key-ease order. Use when a feature wants a key, a new spell or form needs a bar slot, or a key stops working.
tools: Bash, Read, Write
---

# Keybind manager

**One job:** every key does one clear thing, is easy to reach, and never taints.

- Player's key ease: 3 easiest, then 2/4, then 1/5; 6+ a stretch. Modifier keys: Alt for Druid Kit windows,
  Shift for extra bar slots.
- New binding: Bindings.xml entry + `BINDING_NAME_*` + a default key set only out of combat and never at login
  (with the reload prompt), only if the key is free (`GetBindingAction`), else say which key it uses instead.
  Bindings.xml changes need a full quit (Cmd+Q), not /reload.
- New spell or form: its slot in the bar layout for that form (caster, Bear, Cat, Prowl), melee spells as
  `/startattack` macros.
- Keep the key map in `docs/UI_STYLE.md` and the guide's Help/Commands text in step (guide-writer); `tests/ui_test.py`
  fails if a binding is missing from the key map.
