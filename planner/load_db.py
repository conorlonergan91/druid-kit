"""Load the public QuestieDB WoW Forever data *with* its Forever corrections and crowd-sourced traces
(Questie users' QuestieTrace data: custom Forever quests, real NPC/object spots), into routekit/db.json.

Sources (GPLv3): github.com/Questie/QuestieDB data/Forever + src/corrections/Forever.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

from lupa.lua51 import LuaRuntime

# Usage: python3 load_db.py [path to a QuestieDB clone]   (git clone https://github.com/Questie/QuestieDB)
HERE = os.path.dirname(os.path.abspath(__file__))
Q = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("QUESTIEDB", "/tmp/QuestieDB")
OUT = os.path.join(HERE, "db.json")
DATA = os.path.join(HERE, "data")

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(r"""
modules = {}
QuestieLoader = {
  CreateModule = function(self, name) modules[name] = modules[name] or {}; return modules[name] end,
  ImportModule = function(self, name) modules[name] = modules[name] or {}; return modules[name] end,
}
LibQuestieDB = { Enum = {}, config = { flavorByName = { Forever = "Forever" } } }
-- anything else a fix file reaches for: a forgiving stub
local stubmt = {}
stubmt.__index = function(t, k) local v = setmetatable({}, stubmt); rawset(t, k, v); return v end
stubmt.__call = function() return nil end
setmetatable(_G, { __index = function(t, k) return setmetatable({}, stubmt) end })
function runchunk(src, name)
  local f, e = loadstring(src, name)
  if not f then return "LOAD " .. tostring(e) end
  local ok, err = pcall(f, nil, LibQuestieDB)
  if not ok then return "RUN " .. tostring(err) end
  return nil
end
""")


def run(path):
    err = L.globals().runchunk(Path(path).read_text(encoding="utf-8"), os.path.basename(path))
    if err:
        print("warn", path, str(err)[:160])


for f in ("constants", "zones", "quests", "expansions", "professions", "items", "factions", "phases"):
    p = f"{Q}/src/corrections/enum/{f}.lua"
    if os.path.exists(p):
        run(p)


def load_data(path, var):
    src = Path(path).read_text(encoding="utf-8")
    head, rest = src.split(f"QuestieDB.{var} = [[", 1)
    L.execute(head.replace('QuestieLoader:ImportModule("QuestieDB")', 'QuestieLoader:ImportModule("QuestieDB")'))
    return L.execute(rest.rsplit("]]", 1)[0])


quests = load_data(f"{Q}/data/Forever/foreverQuestDB.lua", "questData")
npcs = load_data(f"{Q}/data/Forever/foreverNpcDB.lua", "npcData")
objects = load_data(f"{Q}/data/Forever/foreverObjectDB.lua", "objectData")
items = load_data(f"{Q}/data/Forever/foreverItemDB.lua", "itemData")

L.execute(r"""
local E = LibQuestieDB.Enum
local fx = E.byExpansion.Forever or {}
local QDB = QuestieLoader:CreateModule("QuestieDB")
QDB.raceKeys = fx.raceKeys or (E.byExpansion.TBC or {}).raceKeys
QDB.classKeys = fx.classKeys or (E.byExpansion.TBC or {}).classKeys
QDB.sortKeys = E.sortKeys
QDB.questFlags = E.questFlags
QDB.specialFlags = E.specialFlags
QuestieLoader:CreateModule("ZoneDB").zoneIDs = E.zoneIDs
local function addKeys(keys) if not keys then return end
  local extra = {}
  for name, idx in pairs(keys) do extra[name .. "_add"] = idx + 1000 end
  for k, v in pairs(extra) do keys[k] = v end
end
addKeys(QDB.questKeys); addKeys(QDB.npcKeys); addKeys(QDB.objectKeys); addKeys(QDB.itemKeys)
""")

CORR = f"{Q}/src/corrections/Forever"
files = {
    "quest": [
        f"{CORR}/generated/foreverBaseQuest.lua",
        f"{CORR}/foreverQuestFixes.lua",
        f"{CORR}/traces/foreverQuestTraces.lua",
        f"{CORR}/traces/foreverQuestRelationTraces.lua",
    ],
    "npc": [
        f"{CORR}/generated/foreverBaseNpc.lua",
        f"{CORR}/foreverNPCFixes.lua",
        f"{CORR}/traces/foreverNpcTraces.lua",
    ],
    "object": [
        f"{CORR}/generated/foreverBaseObject.lua",
        f"{CORR}/foreverObjectFixes.lua",
        f"{CORR}/traces/foreverObjectTraces.lua",
    ],
    "item": [
        f"{CORR}/generated/foreverBaseItem.lua",
        f"{CORR}/foreverItemFixes.lua",
        f"{CORR}/traces/foreverItemTraces.lua",
    ],
}
L.execute(r"""
function merge(dst, src)
  if type(src) ~= "table" or type(dst) ~= "table" then return src end
  for k, v in pairs(src) do
    if type(v) == "table" and type(dst[k]) == "table" then merge(dst[k], v) else dst[k] = v end
  end
  return dst
end
function apply(db, patch)
  local n = 0
  for id, fields in pairs(patch) do
    if type(fields) == "table" then
      db[id] = db[id] or {}
      for key, val in pairs(fields) do
        if type(key) == "number" and key > 1000 then
          local base = key - 1000
          if type(db[id][base]) == "table" then merge(db[id][base], val) else db[id][base] = val end
        else
          db[id][key] = val
        end
      end
      n = n + 1
    end
  end
  return n
end
function loadfix(src, name)
  local before = {}
  for k in pairs(modules) do before[k] = true end
  local err = runchunk(src, name)
  if err then return nil, err end
  -- the module just created has a :Load() returning the patch table
  for k, m in pairs(modules) do
    if type(m) == "table" and rawget(m, "Load") and not rawget(m, "_done") then
      m._done = true
      local ok, patch = pcall(m.Load, m)
      if ok then return patch end
      return nil, patch
    end
  end
  return nil, "no Load()"
end
""")
db = {"quest": quests, "npc": npcs, "object": objects, "item": items}
for kind, paths in files.items():
    for p in paths:
        if not os.path.exists(p):
            continue
        res = L.globals().loadfix(Path(p).read_text(encoding="utf-8"), os.path.basename(p))
        patch, err = res if isinstance(res, tuple) else (res, None)
        if patch is None:
            print("skip", os.path.basename(p), str(err)[:140])
            continue
        n = L.globals().apply(db[kind], patch)
        print("applied", os.path.basename(p), n)

QK = {k: v for k, v in L.globals().modules["QuestieDB"].questKeys.items() if not k.endswith("_add")}
NK = {k: v for k, v in L.globals().modules["QuestieDB"].npcKeys.items() if not k.endswith("_add")}
OK = {k: v for k, v in L.globals().modules["QuestieDB"].objectKeys.items() if not k.endswith("_add")}
IK = {k: v for k, v in L.globals().modules["QuestieDB"].itemKeys.items() if not k.endswith("_add")}


def py(v, depth=0):
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    if depth > 8:
        return None
    try:
        keys = list(v.keys())
    except Exception:
        return str(v)
    if keys and all(isinstance(k, int) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
        return [py(v[k], depth + 1) for k in sorted(keys)]
    return {str(k): py(v[k], depth + 1) for k in keys}


def rows(table, keys):
    out = {}
    for i in table.keys():  # noqa: SIM118 (a Lua table, not a dict)
        rec = table[i]
        if rec is None:
            continue
        out[str(i)] = {name: py(rec[idx]) for name, idx in keys.items() if rec[idx] is not None}
    return out


DB = {
    "questKeys": QK,
    "quests": rows(quests, QK),
    "npcs": rows(npcs, NK),
    "objects": rows(objects, OK),
    "items": rows(items, IK),
}
Path(OUT).write_text(json.dumps(DB, ensure_ascii=False), encoding="utf-8")
print("wrote", OUT)


# Side tables rk.py reads from data/: subzone -> parent zone, Forever quest XP, Classic Era quest ids.
os.makedirs(DATA, exist_ok=True)
shutil.copy(os.path.join(Q, "support/Forever/Zones/subZoneToParentZone.lua"), DATA)
xpdir = os.path.join(Q, "support/Forever/QuestXP")
for f in os.listdir(xpdir):
    if f.startswith("xpDB-") and f.endswith(".lua"):
        shutil.copy(os.path.join(xpdir, f), DATA)
classic = Path(Q, "data/Classic/classicQuestDB.lua").read_text(encoding="utf-8")
ids = sorted(int(m) for m in re.findall(r"^\[(\d+)\]\s*=", classic, re.M))
Path(DATA, "classic_quest_ids.json").write_text(json.dumps(ids))
print("data/ written:", len(ids), "classic quest ids")
