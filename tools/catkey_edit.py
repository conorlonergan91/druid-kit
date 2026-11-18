"""Adds /dk catkey (Cat Form on G) and /dk runkey (autorun on Cmd+W) to DruidKit.lua. Run: python3 catkey_edit.py <file>"""
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:60], s.count(a))
    s = s.replace(a, b)
rep('''function DruidKit_SetDefaultKeys()''', '''-- One key for one action, on request only, out of combat. Never takes a key in use unless forced.
-- Mac: Cmd is "META-" in a binding. If the client refuses it, SetBinding returns false and we say so.
local function keyName(k) return (k:gsub("META%-", "Cmd+"):gsub("CTRL%-", "Ctrl+"):gsub("ALT%-", "Option+"):gsub("SHIFT%-", "Shift+")) end
local function bindOne(key, action, label, force, spell)
  if InCombatLockdown() then say("after combat, please."); return false end
  local current = GetBindingAction and GetBindingAction(key)
  if current == action then say(keyName(key) .. " already " .. label .. "."); return true end
  if current and current ~= "" and not force then
    say(("%s is used for %s, so I didn't change it."):format(keyName(key), current)); return false
  end
  local ok
  if spell and SetBindingSpell then ok = safe(SetBindingSpell, key, spell) else ok = safe(SetBinding, key, action) end
  if ok == false then say("the game won't bind " .. keyName(key) .. "."); return false end
  safe(SaveBindings, GetCurrentBindingSet and GetCurrentBindingSet() or 1)
  say(keyName(key) .. " now " .. label .. ".")
  return true
end

-- Cat Form on G (player's choice), else Cmd+F. Binds the spell, so it works whatever slot the form has.
local function setCatKey(key, force)
  if not isKnown("Cat Form") then say("you don't have Cat Form yet (level 20 quest)."); return end
  local keys = (key and key ~= "") and { key:upper() } or { "G", "META-F" }
  for _, k in ipairs(keys) do
    if bindOne(k, "SPELL Cat Form", "turns you into Cat Form", force, "Cat Form") then
      DruidKitDB.catKeySet = k; askReload(); return
    end
  end
  say("type /dk catkey G force to take G, or /dk catkey <key>.")
end
DruidKit_SetCatKey = setCatKey

-- Autorun on Cmd+W (player's choice). Option+W and ` stay as spares. A double tap of W can't be a binding.
local function setRunKey(key, force)
  local k = (key and key ~= "") and key:upper() or "META-W"
  if bindOne(k, "TOGGLEAUTORUN", "toggles autorun", force) then DruidKitDB.runKeySet = k; askReload()
  else say("type /dk runkey " .. k .. " force to take it, or /dk runkey <key>. Option+W still works.") end
end
DruidKit_SetRunKey = setRunKey

function DruidKit_SetDefaultKeys()''')
rep('''  pcall(setDefaultGuideKey); pcall(setDefaultTabKeys); pcall(setDefaultBagsKey); pcall(setDefaultGoKey); pcall(setDefaultAutorunKey); pcall(setDefaultModeKey); pcall(setDefaultStepsKey)''', '''  pcall(setDefaultGuideKey); pcall(setDefaultTabKeys); pcall(setDefaultBagsKey); pcall(setDefaultGoKey); pcall(setDefaultAutorunKey); pcall(setDefaultModeKey); pcall(setDefaultStepsKey)
  if not DruidKitDB.runKeySet then pcall(setRunKey) end
  if not DruidKitDB.catKeySet and isKnown("Cat Form") then pcall(setCatKey) end''')
rep('''  elseif cmd == "keys" then''', '''  elseif cmd == "catkey" or cmd == "runkey" then
    local key, force = (rest or ""):match("^(%S*)%s*(%S*)")
    if key:lower() == "force" then key, force = "", "force" end
    key = key:gsub("^[Cc][Mm][Dd]%+", "META-")
    ;(cmd == "catkey" and DruidKit_SetCatKey or DruidKit_SetRunKey)(key, force == "force")
  elseif cmd == "keys" then''')
open(p, "w", encoding="utf-8").write(s)
print("ok", p)
