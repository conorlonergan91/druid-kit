-- Druid Kit: trainer pins on the world map and minimap.
-- Herbalism, Alchemy, Cooking, Fishing, First Aid and Druid trainers (Alliance, WoW Forever).
-- Data: Warcraft Tavern's WoW Forever trainer lists. If you open a trainer and the pin is off,
-- the pin moves to where you're standing (remembered per character).
--   /dk trainers on|off

local CATS = {
  herb  = { label = "Herbalism",  icon = "Interface\\Icons\\Trade_Herbalism" },
  alch  = { label = "Alchemy",    icon = "Interface\\Icons\\Trade_Alchemy" },
  cook  = { label = "Cooking",    icon = "Interface\\Icons\\INV_Misc_Food_15" },
  fish  = { label = "Fishing",    icon = "Interface\\Icons\\Trade_Fishing" },
  aid   = { label = "First Aid",  icon = "Interface\\Icons\\Spell_Holy_SealOfSacrifice" },
  druid = { label = "Druid",      icon = "Interface\\Icons\\Ability_Druid_Maul" },
  bank  = { label = "Bank",            icon = "Interface\\Icons\\INV_Misc_Bag_10" },
  ah    = { label = "Auction House",   icon = "Interface\\Icons\\INV_Misc_Coin_01" },
  fly   = { label = "Flight master",   icon = "Interface\\Icons\\Ability_Mount_Gryphon_01" },
  inn   = { label = "Innkeeper",       icon = "Interface\\Icons\\INV_Drink_05" },
  mail  = { label = "Mailbox",         icon = "Interface\\Icons\\INV_Letter_15" },
  crate = { label = "Waylaid Crate camp", icon = "Interface\\Icons\\INV_Crate_01" },
}
local SERVICE = { bank = true, ah = true, fly = true, inn = true, mail = true, crate = true }

-- { category, name, rank/note, zone, place, x, y }
local TRAINERS = {
  { "alch", "Cyndra Kindwhisper", "Apprentice", "Teldrassil", "Dolanaar", 57.6, 60.7 },
  { "alch", "Milla Fairancora", "Apprentice", "Darnassus", "Craftsmen's Terrace", 55.4, 22.9 },
  { "alch", "Ainethil", "Expert", "Darnassus", "Craftsmen's Terrace", 55.5, 23.1 },
  { "alch", "Sylvanna Forestmoon", "Expert", "Darnassus", "Craftsmen's Terrace", 56.1, 24.3 },
  { "alch", "Kylanna", "Journeyman", "Ashenvale", "Silverwind Refuge", 50.8, 67.1 },
  { "alch", "Kylanna Windwhisper", "Artisan", "Feralas", "Feathermoon Stronghold", 32.6, 43.7 },
  { "alch", "Alchemist Narett", "Journeyman", "Dustwallow Marsh", "Theramore Isle", 64.0, 47.6 },
  { "alch", "Alchemist Mallory", "Apprentice", "Elwynn Forest", "Outside Stormwind", 39.8, 48.4 },
  { "alch", "Tel'Athir", "Apprentice", "Stormwind City", "Mage Quarter", 55.5, 85.4 },
  { "alch", "Lilyssia Nightbreeze", "Journeyman", "Stormwind City", "Mage Quarter", 55.5, 85.4 },
  { "alch", "Vosur Brakthel", "Apprentice", "Ironforge", "Tinker Town", 67.0, 54.2 },
  { "alch", "Tally Berryfizz", "Journeyman", "Ironforge", "Tinker Town", 67.2, 54.2 },
  { "alch", "Ghak Healtouch", "Apprentice", "Loch Modan", "Thelsamar", 37.0, 49.3 },
  { "alch", "Iaadaria Bitterwind", "Apprentice", "Zephras Isle", "Valanaar", 66.3, 79.5 },
  { "alch", "Valiena Swiftgale", "Apprentice", "Zephras Isle", "Valanaar", 59.3, 76.2 },
  { "alch", "Nyassa Swiftdraught", "Apprentice", "Zephras Isle", "Shen'dar Village", 43.7, 43.4 },

  { "herb", "Eleyna Duskbreeze", "Apprentice", "Teldrassil", "Shadowglen", 59.8, 41.3 },
  { "herb", "Malorne Bladeleaf", "Artisan", "Teldrassil", "Dolanaar", 57.7, 60.6 },
  { "herb", "Firodren Mooncaller", "Artisan", "Darnassus", "Temple Gardens", 47.9, 68.6 },
  { "herb", "Malvor", "Artisan", "Moonglade", "Nighthaven", 45.6, 46.8 },
  { "herb", "Cylania Rootstalker", "Artisan", "Ashenvale", "Silverwind Refuge", 50.6, 67.0 },
  { "herb", "Brant Jasperbloom", "Artisan", "Dustwallow Marsh", "Theramore Isle", 64.1, 47.5 },
  { "herb", "Herbalist Pomeroy", "Artisan", "Elwynn Forest", "Outside Stormwind", 39.9, 48.3 },
  { "herb", "Nancy Songflower", "Apprentice", "Elwynn Forest", "Northshire", 52.4, 43.8 },
  { "herb", "Shylamiir", "Artisan", "Stormwind City", "The Park", 31.4, 62.9 },
  { "herb", "Tannysa", "Artisan", "Stormwind City", "Mage Quarter", 54.5, 83.9 },
  { "herb", "Reyna Stonebranch", "Artisan", "Ironforge", "Great Forge", 55.6, 58.0 },
  { "herb", "Emrys Flintbeard", "Apprentice", "Dun Morogh", "Coldridge Valley", 28.8, 66.7 },
  { "herb", "Kali Healtouch", "Artisan", "Loch Modan", "Thelsamar", 36.6, 48.4 },
  { "herb", "Alma Jainrose", "Artisan", "Redridge Mountains", "Lakeshire", 16.8, 46.8 },
  { "herb", "Telurinon Moonshadow", "Artisan", "Wetlands", "Menethil Harbor", 8.0, 55.9 },
  { "herb", "Syriel Nightrain", "Artisan", "Zephras Isle", "Valanaar", 57.9, 75.5 },
  { "herb", "Halassa Fernbreeze", "Artisan", "Zephras Isle", "Shen'dar Village", 43.1, 43.5 },

  { "cook", "Zarrin", "Journeyman", "Teldrassil", "Dolanaar", 57.1, 61.2 },
  { "cook", "Alegorn", "Journeyman", "Darnassus", "Craftsmen's Terrace", 48.9, 21.3 },
  { "cook", "Stephen Ryback", "Journeyman", "Stormwind City", "Old Town", 78.3, 53.1 },
  { "cook", "Tomas", "Journeyman", "Elwynn Forest", "Goldshire", 44.3, 66.0 },
  { "cook", "Daryl Riknussun", "Journeyman", "Ironforge", "The Great Forge", 60.4, 38.1 },
  { "cook", "Gremlock Pilsnor", "Journeyman", "Dun Morogh", "Kharanos", 47.6, 52.4 },
  { "cook", "Cook Ghilm", "Journeyman", "Dun Morogh", "Gol'Bolar Quarry", 68.4, 54.5 },
  { "cook", "Crystal Boughman", "Journeyman", "Redridge Mountains", "Lakeshire", 17.7, 43.6 },
  { "cook", "Nyalah Brightfire", "Journeyman", "Zephras Isle", "Valanaar", 60.6, 72.7 },
  { "cook", "Zerril Softbreeze", "Journeyman", "Zephras Isle", "Shen'dar Village", 43.8, 43.9 },

  { "fish", "Androl Oakhand", "Journeyman", "Teldrassil", "Rut'theran Village", 55.8, 93.5 },
  { "fish", "Astaia", "Journeyman", "Darnassus", "Temple Gardens", 47.5, 56.5 },
  { "fish", "Brannock", "Journeyman", "Feralas", "Feathermoon Stronghold", 32.2, 41.4 },
  { "fish", "Arnold Leland", "Journeyman", "Stormwind City", "Trade District", 55.1, 69.6 },
  { "fish", "Lee Brown", "Journeyman", "Elwynn Forest", "Goldshire", 47.6, 62.3 },
  { "fish", "Grimnur Stonebrand", "Journeyman", "Ironforge", "The Forlorn Cavern", 48.5, 6.2 },
  { "fish", "Paxton Ganter", "Journeyman", "Dun Morogh", "Iceflow Lake", 35.6, 40.4 },
  { "fish", "Warg Deepwater", "Journeyman", "Loch Modan", "The Loch", 40.5, 39.4 },
  { "fish", "Matthew Hooper", "Journeyman", "Redridge Mountains", "Lakeshire", 21.5, 51.0 },
  { "fish", "Harold Riggs", "Journeyman", "Wetlands", "Menethil Harbor", 8.2, 58.3 },
  { "fish", "Baelann Swiftcurrent", "Journeyman", "Zephras Isle", "Valanaar", 63.2, 75.7 },
  { "fish", "Fenn Fairweather", "Journeyman", "Zephras Isle", "Shen'dar Village", 45.0, 48.4 },

  { "aid", "Byancie", "Journeyman", "Teldrassil", "Dolanaar", 55.4, 56.9 },
  { "aid", "Dannelor", "Journeyman", "Darnassus", "Craftsmen's Terrace", 51.5, 13.7 },
  { "aid", "Shaina Fuller", "Journeyman", "Stormwind City", "Cathedral Square", 52.9, 44.9 },
  { "aid", "Michelle Belle", "Journeyman", "Elwynn Forest", "Goldshire", 43.4, 65.7 },
  { "aid", "Nissa Firestone", "Journeyman", "Ironforge", "The Great Forge", 54.8, 58.6 },
  { "aid", "Thamner Pol", "Journeyman", "Dun Morogh", "Kharanos", 47.2, 52.6 },
  { "aid", "Fremal Doohickey", "Journeyman", "Wetlands", "Menethil Harbor", 10.8, 61.1 },
  { "aid", "Melasa Fairmend", "Journeyman", "Zephras Isle", "Valanaar", 63.1, 72.6 },
  { "aid", "Naleeia Tattermend", "Journeyman", "Zephras Isle", "Shen'dar Village", 43.1, 46.3 },

  { "druid", "Kal", "Druid trainer", "Teldrassil", "Dolanaar", 56.0, 61.6 },
  { "druid", "Mardant Strongoak", "Druid trainer (to level 6)", "Teldrassil", "Shadowglen", 58.6, 40.3 },
  { "druid", "Denatharion", "Druid trainer", "Darnassus", "Cenarion Enclave", 34.8, 7.7 },
  { "druid", "Fylerian Nightwing", "Druid trainer", "Darnassus", "Cenarion Enclave", 33.6, 8.6 },
  { "druid", "Mathrengyl Bearwalker", "Druid trainer", "Darnassus", "Cenarion Enclave", 35.2, 8.3 },
  { "druid", "Loganaar", "Druid trainer", "Moonglade", "Nighthaven", 52.5, 40.6 },
  { "druid", "Golhine the Hooded", "Druid trainer", "Felwood", "Talonbranch Glade", 62.0, 24.4 },
  { "druid", "Maldryn", "Druid trainer", "Stormwind City", "The Park", 34.4, 65.2 },
  { "druid", "Sheldras Moontree", "Druid trainer", "Stormwind City", "The Park", 36.0, 67.3 },
  { "druid", "Theridran", "Druid trainer", "Stormwind City", "The Park", 36.0, 64.3 },
  { "druid", "Naeluna Swiftmend", "Druid trainer", "Zephras Isle", "Shen'dar Village", 45.2, 44.3 },
  { "druid", "Lotheluum Starbreeze", "Druid trainer", "Zephras Isle", "Valanaar", 64.0, 75.1 },
  { "druid", "Xyton Silverwind", "Druid trainer (to level 6)", "Zephras Isle", "Thendal Village", 41.7, 23.4 },
  -- Azeroth Commerce Authority camp where Elwynn, Redridge and Duskwood meet (Mobalytics; moves itself when you talk to her)
  { "crate", "Marcy Baker", "hand in Waylaid Crates (approximate spot)", "Redridge Mountains", "Three Corners camp", 9.7, 70.9 },
}

-- Known map IDs for the classic zones; anything else (Zephras Isle) is looked up by name.
local KNOWN_MAPS = {
  ["Teldrassil"] = 1438, ["Darnassus"] = 1457, ["Moonglade"] = 1450, ["Ashenvale"] = 1440,
  ["Felwood"] = 1448, ["Feralas"] = 1444, ["Dustwallow Marsh"] = 1445, ["Stormwind City"] = 1453,
  ["Elwynn Forest"] = 1429, ["Ironforge"] = 1455, ["Dun Morogh"] = 1426, ["Loch Modan"] = 1432,
  ["Redridge Mountains"] = 1433, ["Wetlands"] = 1437,
}

local DB
local pins = {}          -- resolved: { cat, name, note, zone, place, mapID, x, y, cont, wa, wb }
local byMap = {}         -- mapID -> list of pins
local nameIndex          -- lower-case map name -> mapID (built only if needed)

local function mapName(id)
  local info = C_Map and C_Map.GetMapInfo and C_Map.GetMapInfo(id)
  return info and info.name
end

local function findMap(zone)
  local id = KNOWN_MAPS[zone]
  if id and mapName(id) == zone then return id end
  if not nameIndex then
    nameIndex = {}
    local ok, kids = pcall(C_Map.GetMapChildrenInfo, 947, nil, true)
    if ok and type(kids) == "table" then
      for _, m in ipairs(kids) do
        local k = m.name and m.name:lower()
        if k and not nameIndex[k] then nameIndex[k] = m.mapID end
      end
    end
    if not next(nameIndex) then
      for i = 1, 3000 do
        local n = mapName(i)
        if n and not nameIndex[n:lower()] then nameIndex[n:lower()] = i end
      end
    end
  end
  return nameIndex[zone:lower()] or id
end

local function worldPos(mapID, x, y)
  if not (C_Map.GetWorldPosFromMapPos and CreateVector2D) then return end
  local ok, cont, pos = pcall(C_Map.GetWorldPosFromMapPos, mapID, CreateVector2D(x, y))
  if ok and cont and pos then
    local a, b = pos:GetXY()
    return cont, a, b
  end
end

local function resolve()
  wipe(pins); wipe(byMap)
  local moved = DB.trainerFix or {}
  for _, t in ipairs(TRAINERS) do
    local mapID = findMap(t[4])
    if mapID then
      local fix = moved[t[2]]
      local p = { cat = t[1], name = t[2], note = t[3], zone = t[4], place = t[5],
                  mapID = fix and fix.map or mapID, x = (fix and fix.x or t[6] / 100), y = (fix and fix.y or t[7] / 100) }
      p.cont, p.wa, p.wb = worldPos(p.mapID, p.x, p.y)
      table.insert(pins, p)
      byMap[p.mapID] = byMap[p.mapID] or {}
      table.insert(byMap[p.mapID], p)
    end
  end
  -- Banks, auction houses, flight masters, inns and mailboxes you've used (learned, not guessed).
  for _, l in ipairs(DB.places or {}) do
    local p = { cat = l.cat, name = l.name, note = "learned when you used it", zone = l.zone or "", place = l.place or "",
                mapID = l.map, x = l.x, y = l.y, learned = true }
    p.cont, p.wa, p.wb = worldPos(p.mapID, p.x, p.y)
    table.insert(pins, p)
    byMap[p.mapID] = byMap[p.mapID] or {}
    table.insert(byMap[p.mapID], p)
  end
end

local function tooltip(owner, p)
  GameTooltip:SetOwner(owner, "ANCHOR_RIGHT")
  if p.isTarget then
    GameTooltip:AddLine("Your waypoint", 1, 0.82, 0)
    GameTooltip:AddLine(p.name, 1, 1, 1)
    GameTooltip:AddLine("Click: stop navigating", 0.5, 0.83, 0.36)
    GameTooltip:Show()
    return
  end
  GameTooltip:AddLine(p.name, 1, 0.82, 0)
  local c = CATS[p.cat]
  local what = (p.cat == "druid") and p.note or SERVICE[p.cat] and (c.label .. " (" .. p.note .. ")") or (c.label .. " trainer (" .. p.note .. ")")
  GameTooltip:AddLine(what, 1, 1, 1)
  GameTooltip:AddLine(("%s, %s  (%.1f, %.1f)"):format(p.place, p.zone, p.x * 100, p.y * 100), 0.7, 0.7, 0.7)
  GameTooltip:AddLine("Click: set a waypoint and show the way", 0.5, 0.83, 0.36)
  GameTooltip:Show()
end

local function styleIcon(f, p, size)
  f:SetSize(size, size)
  if not f.icon then
    f.border = f:CreateTexture(nil, "BACKGROUND")
    f.border:SetPoint("TOPLEFT", -1, 1); f.border:SetPoint("BOTTOMRIGHT", 1, -1)
    f.border:SetColorTexture(0, 0, 0, 0.85)
    f.icon = f:CreateTexture(nil, "ARTWORK")
    f.icon:SetAllPoints()
    f.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
  end
  f.icon:SetTexture(p.icon or CATS[p.cat].icon)
  f.border:SetColorTexture(p.cat == "druid" and 1 or 0, p.cat == "druid" and 0.49 or 0, p.cat == "druid" and 0.04 or 0, 0.9)
end

-- Waypoints: the game's own map pin and on-screen arrow (C_Map user waypoint + super-tracking).
local function say(msg) print("|cff7fd35bDruid Kit:|r " .. msg) end
local function setWaypoint(p)
  if not p then return end
  local label = p.name .. " (" .. (p.place ~= "" and p.place or CATS[p.cat].label) .. ")"
  local ok = false
  if C_Map and C_Map.SetUserWaypoint and UiMapPoint and UiMapPoint.CreateFromCoordinates then
    local can = not C_Map.CanSetUserWaypointOnMap or C_Map.CanSetUserWaypointOnMap(p.mapID)
    if can then
      ok = pcall(C_Map.SetUserWaypoint, UiMapPoint.CreateFromCoordinates(p.mapID, p.x, p.y))
      if ok and C_SuperTrack and C_SuperTrack.SetSuperTrackedUserWaypoint then pcall(C_SuperTrack.SetSuperTrackedUserWaypoint, true) end
    end
  end
  if not ok and TomTom and TomTom.AddWaypoint then
    ok = pcall(TomTom.AddWaypoint, TomTom, p.mapID, p.x, p.y, { title = label })
  end
  local arrow = DruidKit_NavTo and DruidKit_NavTo(p.mapID, p.x, p.y, label)
  if arrow or ok then
    say("heading to " .. label .. ". Follow the big arrow; right-click it to stop.")
  else
    say(("go to %s: %s, %.1f, %.1f (open the map with M)."):format(label, p.zone, p.x * 100, p.y * 100))
  end
  if WorldMapFrame and WorldMapFrame:IsShown() and WorldMapFrame.SetMapID then pcall(WorldMapFrame.SetMapID, WorldMapFrame, p.mapID) end
end
DruidKit_SetWaypoint = setWaypoint

-- World map ----------------------------------------------------------------------
DruidKitTrainerPinMixin = MapCanvasPinMixin and CreateFromMixins(MapCanvasPinMixin) or {}
function DruidKitTrainerPinMixin:OnLoad()
  if self.UseFrameLevelType then self:UseFrameLevelType("PIN_FRAME_LEVEL_AREA_POI") end
  if self.SetScalingLimits then self:SetScalingLimits(1, 1.0, 1.25) end
  self:SetScript("OnEnter", function(s) if s.data then tooltip(s, s.data) end end)
  self:SetScript("OnLeave", function() GameTooltip:Hide() end)
  self:SetScript("OnMouseUp", function(s, button)
    if button ~= "LeftButton" or not s.data then return end
    if s.data.isTarget then if DruidKit_NavClear then DruidKit_NavClear() end else setWaypoint(s.data) end
  end)
  if self.SetPassThroughButtons then pcall(self.SetPassThroughButtons, self, "RightButton") end   -- right-click still zooms out
end
function DruidKitTrainerPinMixin:OnAcquired(p, x, y)
  self.data = p
  styleIcon(self, p, 14)
  self:SetPosition(x, y)
end

local provider
local function addWorldMapProvider()
  if provider or not (WorldMapFrame and MapCanvasDataProviderMixin and WorldMapFrame.AddDataProvider) then return end
  provider = CreateFromMixins(MapCanvasDataProviderMixin)
  function provider:RemoveAllData()
    self:GetMap():RemoveAllPinsByTemplate("DruidKitTrainerPinTemplate")
  end
  -- One bad pin must never break the whole map: Blizzard asserts on odd positions.
  local function addPin(map, data, x, y)
    if type(x) ~= "number" or type(y) ~= "number" or x ~= x or y ~= y then return end
    pcall(map.AcquirePin, map, "DruidKitTrainerPinTemplate", data, x, y)
  end
  function provider:RefreshAllData()
    self:RemoveAllData()
    local map = self:GetMap()
    local cur = map:GetMapID()
    if not cur then return end
    local t = DruidKit_NavTarget and DruidKit_NavTarget()
    if t then
      local tx, ty = DruidKit_NavProject and DruidKit_NavProject(t, cur)
      if tx and ty and tx >= 0 and tx <= 1 and ty >= 0 and ty <= 1 then
        addPin(map, { isTarget = true, cat = "druid", name = t.label,
          icon = "Interface\\Icons\\INV_Misc_Map_01" }, tx, ty)
      end
    end
    if not (DB and DB.trainersOn) then return end
    for _, p in ipairs(byMap[cur] or {}) do addPin(map, p, p.x, p.y) end
    -- city trainers also on the zone map around them (Darnassus on Teldrassil)
    for mapID, list in pairs(byMap) do
      local info = mapID ~= cur and C_Map.GetMapInfo(mapID)
      if info and info.parentMapID == cur then
        local ok, l, r, t, b = pcall(C_Map.GetMapRectOnMap, mapID, cur)
        if ok and l then
          for _, p in ipairs(list) do
            addPin(map, p, l + p.x * (r - l), t + p.y * (b - t))
          end
        end
      end
    end
  end
  WorldMapFrame:AddDataProvider(provider)
end
DruidKit_RefreshMapPins = function() if provider then pcall(provider.RefreshAllData, provider) end end

-- Minimap --------------------------------------------------------------------------
local OUTDOOR = { [0] = 466 + 2 / 3, 400, 333 + 1 / 3, 266 + 2 / 3, 200, 133 + 1 / 3 }
local INDOOR  = { [0] = 300, 240, 180, 120, 80, 50 }
local mmPins, mmUsed = {}, 0

local function mmPin(i)
  local f = mmPins[i]
  if not f then
    f = CreateFrame("Frame", nil, Minimap)
    f:SetFrameLevel(Minimap:GetFrameLevel() + 5)
    f:EnableMouse(true)
    f:SetScript("OnEnter", function(s) if s.data then tooltip(s, s.data) end end)
    f:SetScript("OnLeave", function() GameTooltip:Hide() end)
    f:SetScript("OnMouseUp", function(s) if s.data then setWaypoint(s.data) end end)
    mmPins[i] = f
  end
  return f
end

local function updateMinimap()
  local used = 0
  if DB and DB.trainersOn and Minimap:IsVisible() then
    local pa, pb, _, inst = UnitPosition("player")
    if pa then
      local zoom = Minimap:GetZoom() or 0
      local diameter = (IsIndoors and IsIndoors() and INDOOR or OUTDOOR)[zoom] or 400
      local scale = Minimap:GetWidth() / diameter
      local radius = Minimap:GetWidth() / 2 - 5
      local rotate = GetCVar and GetCVar("rotateMinimap") == "1"
      local facing = rotate and (GetPlayerFacing() or 0) or 0
      local cs, sn = math.cos(facing), math.sin(facing)
      for _, p in ipairs(pins) do
        if p.cont == inst and p.wa then
          local north, west = p.wa - pa, p.wb - pb
          local dx, dy = -west * scale, north * scale
          if rotate then dx, dy = dx * cs - dy * sn, dx * sn + dy * cs end
          if dx * dx + dy * dy <= radius * radius then
            used = used + 1
            local f = mmPin(used)
            f.data = p
            styleIcon(f, p, 12)
            f:ClearAllPoints()
            f:SetPoint("CENTER", Minimap, "CENTER", dx, dy)
            f:Show()
          end
        end
      end
    end
  end
  for i = used + 1, mmUsed do mmPins[i]:Hide() end
  mmUsed = used
end

-- Fix a pin when you stand at that trainer ------------------------------------------
local function here()
  local map = C_Map.GetBestMapForUnit("player")
  local pos = map and C_Map.GetPlayerMapPosition(map, "player")
  if not pos then return end
  local x, y = pos:GetXY()
  return map, x, y
end
local function learnPlace(cat)
  local map, x, y = here()
  if not map then return end
  DB.places = DB.places or {}
  local name = UnitName("npc") or CATS[cat].label
  local info = C_Map.GetMapInfo(map)
  for _, l in ipairs(DB.places) do
    if l.cat == cat and l.map == map and math.abs(l.x - x) < 0.02 and math.abs(l.y - y) < 0.02 then
      l.x, l.y, l.name = x, y, name
      resolve(); if provider then provider:RefreshAllData() end
      return
    end
  end
  table.insert(DB.places, { cat = cat, name = name, map = map, x = x, y = y, zone = info and info.name or "",
                            place = (GetSubZoneText and GetSubZoneText()) or "" })
  resolve(); if provider then provider:RefreshAllData() end
end
local function onTrainerShow()
  local name = UnitName("npc")
  if not name then return end
  for _, t in ipairs(TRAINERS) do
    if t[2] == name then
      local map = C_Map.GetBestMapForUnit("player")
      local pos = map and C_Map.GetPlayerMapPosition(map, "player")
      if pos then
        local x, y = pos:GetXY()
        DB.trainerFix = DB.trainerFix or {}
        DB.trainerFix[name] = { map = map, x = x, y = y }
        resolve()
        if provider then provider:RefreshAllData() end
      end
      return
    end
  end
end

-- Wire up -----------------------------------------------------------------------------
local ev = CreateFrame("Frame")
ev:RegisterEvent("PLAYER_LOGIN")
ev:RegisterEvent("TRAINER_SHOW")
for _, e in ipairs({ "GOSSIP_SHOW", "MERCHANT_SHOW", "BANKFRAME_OPENED", "AUCTION_HOUSE_SHOW", "TAXIMAP_OPENED", "MAIL_SHOW",
                     "CONFIRM_BINDER", "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" }) do pcall(ev.RegisterEvent, ev, e) end
local CLASSIC_EVENT = { BANKFRAME_OPENED = "bank", AUCTION_HOUSE_SHOW = "ah", TAXIMAP_OPENED = "fly", MAIL_SHOW = "mail", CONFIRM_BINDER = "inn" }
local function interactionCat(t)
  local E = Enum and Enum.PlayerInteractionType
  if not E then return end
  if t == E.Banker then return "bank" elseif t == E.Auctioneer then return "ah" elseif t == E.TaxiNode then return "fly"
  elseif t == E.MailInfo then return "mail" elseif t == E.Binder or t == E.Innkeeper then return "inn" end
end
ev:SetScript("OnEvent", function(_, e, a1)
  if DB and e ~= "PLAYER_LOGIN" and e ~= "TRAINER_SHOW" then
    local cat = CLASSIC_EVENT[e] or (e == "PLAYER_INTERACTION_MANAGER_FRAME_SHOW" and interactionCat(a1))
    if cat then pcall(learnPlace, cat); return end
    if e == "GOSSIP_SHOW" or e == "MERCHANT_SHOW" then pcall(onTrainerShow) end   -- fixes the crate camp pin too
    return
  end
  if e == "PLAYER_LOGIN" then
    DruidKitDB = DruidKitDB or {}
    DB = DruidKitDB
    if DB.trainersOn == nil then DB.trainersOn = true end
    local ok, err = pcall(resolve)
    if not ok then print("|cff7fd35bDruid Kit:|r trainer pins failed to load: " .. tostring(err)) return end
    pcall(addWorldMapProvider)
  elseif e == "TRAINER_SHOW" and DB then
    pcall(onTrainerShow)
  end
end)
local acc = 0
ev:SetScript("OnUpdate", function(_, el)
  acc = acc + el
  if acc < 0.1 then return end
  acc = 0
  if DB then pcall(updateMinimap) end
end)

function DruidKit_TrainersCommand(arg)
  if not DB then return end
  if arg == "on" then DB.trainersOn = true elseif arg == "off" then DB.trainersOn = false
  else DB.trainersOn = not DB.trainersOn end
  if provider then provider:RefreshAllData() end
  updateMinimap()
  print("|cff7fd35bDruid Kit:|r trainer pins " .. (DB.trainersOn and "on." or "off."))
end

-- "Go to" window: the nearest trainer / bank / auction house etc., one click sets a waypoint.
--   /dk go   (or the Druid Kit "Go to" key binding)
local goPanel
local PROF_CAT = { ["Alchemy"] = "alch", ["Herbalism"] = "herb", ["Cooking"] = "cook", ["Fishing"] = "fish", ["First Aid"] = "aid" }
local function myProfessionCats()
  local out = {}
  if GetNumSkillLines and GetSkillLineInfo then
    for i = 1, (GetNumSkillLines() or 0) do
      local name, header = GetSkillLineInfo(i)
      if name and not header and PROF_CAT[name] then table.insert(out, PROF_CAT[name]) end
    end
  end
  return out
end
local function nearest(cat)
  local pa, pb, _, inst = UnitPosition("player")
  local best, bestD
  for _, p in ipairs(pins) do
    if p.cat == cat and p.cont and p.cont == inst and p.wa and pa then
      local d = math.sqrt((p.wa - pa) ^ 2 + (p.wb - pb) ^ 2)
      if not bestD or d < bestD then best, bestD = p, d end
    end
  end
  if not best and not pa then
    local here = C_Map.GetBestMapForUnit("player")
    for _, p in ipairs(byMap[here] or {}) do if p.cat == cat then return p end end
  end
  return best, bestD
end
local function hasCrate()
  for bag = 0, 4 do
    local n = (C_Container and C_Container.GetContainerNumSlots and C_Container.GetContainerNumSlots(bag)) or 0
    for slot = 1, n do
      local info = C_Container.GetContainerItemInfo(bag, slot)
      local link = info and info.hyperlink
      if link and link:find("Waylaid") then return true end
    end
  end
end
local function enableTownTracking()
  local want = { "Banker", "Auctioneer", "Flight Master", "Innkeeper", "Mailbox", "Trainer" }
  local n, on = 0, {}
  local getN = C_Minimap and C_Minimap.GetNumTrackingTypes or GetNumTrackingTypes
  local getI = C_Minimap and C_Minimap.GetTrackingInfo or GetTrackingInfo
  local setT = C_Minimap and C_Minimap.SetTracking or SetTracking
  if not (getN and getI and setT) then say("this game version has no town tracking menu."); return end
  for i = 1, (getN() or 0) do
    local a, b, c = getI(i)
    local name, active = a, c
    if type(a) == "table" then name, active = a.name, a.active end
    for _, w in ipairs(want) do
      if name and name:find(w) then
        if not active then pcall(setT, i, true) end
        n = n + 1; table.insert(on, name); break
      end
    end
  end
  say(n > 0 and ("minimap now shows: " .. table.concat(on, ", ") .. ".") or "no town tracking options found on the minimap menu.")
end

local function yards(d) return d and (" · " .. (d < 1000 and ("%d yd"):format(math.floor(d)) or ("%.1fk yd"):format(d / 1000))) or "" end
local function refreshGo()
  local S = DruidKitStyle
  local f = goPanel
  S.begin(f)
  if hasCrate() then
    S.header(f, "You have a Waylaid Crate", CATS.crate.icon)
    local p, d = nearest("crate")
    if p then S.item(f, nil, CATS.crate.icon, 1, "Hand it in: " .. p.name, p.place .. ", " .. p.zone .. yards(d), "Go", function() setWaypoint(p) end)
    else S.note(f, "The crate camp is in Redridge, where Elwynn, Redridge and Duskwood meet.") end
  end
  S.header(f, "Trainers", "Interface\\Icons\\INV_Misc_Book_09")
  local cats = { "druid" }
  for _, c in ipairs(myProfessionCats()) do table.insert(cats, c) end
  for _, c in ipairs(cats) do
    local p, d = nearest(c)
    local label = CATS[c].label .. (c == "druid" and " trainer" or "")
    if p then
      S.item(f, nil, CATS[c].icon, 1, label .. ": " .. p.name, (p.note ~= "" and p.note .. " · " or "") .. p.place .. yards(d), "Go", function() setWaypoint(p) end)
    else
      S.note(f, label .. ": none on this continent. Take the boat or tram first.")
    end
  end
  S.header(f, "Town", "Interface\\Icons\\INV_Misc_Bag_10", nil, "Map icons", enableTownTracking)
  for _, c in ipairs({ "bank", "ah", "fly", "inn", "mail", "crate" }) do
    local p, d = nearest(c)
    if p then
      S.item(f, nil, CATS[c].icon, 1, CATS[c].label .. ": " .. p.name, p.place .. ", " .. p.zone .. yards(d), "Go", function() setWaypoint(p) end)
    elseif c ~= "crate" then
      S.note(f, CATS[c].label .. ": not learned on this continent yet. Ask a city guard (they flag it on your map); after you use one once, it's here.")
    end
  end
  S.note(f, "|cff9d9d9dGo sets the game's waypoint: an arrow on screen and a pin on your map. Clicking a Druid Kit pin on the map or minimap does the same.|r")
  S.finish(f)
end

function DruidKit_ToggleGo()
  if not DB then return end
  if not goPanel then
    goPanel = DruidKitStyle.window("DruidKitGoTo", "Go to", "Interface\\Icons\\INV_Misc_Map_01", 400, 470)
    local clear = CreateFrame("Button", nil, goPanel, "UIPanelButtonTemplate")
    clear:SetSize(110, 22); clear:SetPoint("BOTTOMRIGHT", -10, 8); clear:SetText("Clear waypoint")
    clear:SetScript("OnClick", function()
      if DruidKit_NavClear then DruidKit_NavClear() end
      say("waypoint cleared.")
    end)
  end
  if goPanel:IsShown() then goPanel:Hide() return end
  local ok, err = pcall(refreshGo)
  if not ok then say("Go to failed: " .. tostring(err)) return end
  goPanel:Show()
end
BINDING_NAME_DRUIDKIT_GOTO = "Open / close Go to (trainers, bank, auction house)"


-- Navigation arrow ---------------------------------------------------------------------------
-- Our own big on-screen arrow, so it works whatever the client or other addons do with waypoints.
-- Words as well as the arrow: where, how far, which way to turn. Drag to move; right-click to stop.
local nav            -- { mapID, x, y, label, wx, wy, cont }
local arrowF
local function navSay(m) print("|cff7fd35bDruid Kit:|r " .. m) end

local function toWorld(mapID, x, y)
  if not (C_Map and C_Map.GetWorldPosFromMapPos and CreateVector2D) then return end
  local ok, cont, pos = pcall(C_Map.GetWorldPosFromMapPos, mapID, CreateVector2D(x, y))
  if ok and cont and pos then return cont, pos end
end
-- Where the target sits on another map (normalised; may be outside 0-1)
-- Worked out from where the map's corners sit in the world (the same call the arrow already relies on),
-- because C_Map.GetMapPosFromWorldPos doesn't return a usable position in this client.
local function vecXY(v)
  if type(v) ~= "table" then return end
  local a, b
  if v.GetXY then a, b = v:GetXY() end
  a, b = a or v.x, b or v.y
  if type(a) == "number" and type(b) == "number" then return a, b end
end
function DruidKit_NavProject(t, mapID)
  if not (t and t.cont and t.pos) then return end
  local c0, o = toWorld(mapID, 0, 0)
  local c1, ex = toWorld(mapID, 1, 0)
  local c2, ey = toWorld(mapID, 0, 1)
  if not (o and ex and ey) or c0 ~= t.cont or c1 ~= t.cont or c2 ~= t.cont then return end
  local ox, oy = vecXY(o); local ux, uy = vecXY(ex); local vx, vy = vecXY(ey); local px, py = vecXY(t.pos)
  if not (ox and ux and vx and px) then return end
  ux, uy, vx, vy, px, py = ux - ox, uy - oy, vx - ox, vy - oy, px - ox, py - oy
  local det = ux * vy - uy * vx
  if det == 0 then return end
  return (px * vy - py * vx) / det, (ux * py - uy * px) / det
end
function DruidKit_NavTarget() return nav end

-- Width and height of a map in yards (worked out from its corners, so it needs no special API).
local sizes = {}
function DruidKit_MapYards(mapID)
  if sizes[mapID] then return sizes[mapID][1], sizes[mapID][2] end
  local _, a = toWorld(mapID, 0, 0)
  local _, b = toWorld(mapID, 1, 0)
  local _, c = toWorld(mapID, 0, 1)
  if not (a and b and c) then return end
  local ax, ay = vecXY(a); local bx, by = vecXY(b); local cx, cy = vecXY(c)
  if not (ax and bx and cx) then return end
  local w = math.sqrt((bx - ax) ^ 2 + (by - ay) ^ 2)
  local h = math.sqrt((cx - ax) ^ 2 + (cy - ay) ^ 2)
  if w <= 0 or h <= 0 then return end
  sizes[mapID] = { w, h }
  return w, h
end

local function clearNative()
  if C_Map and C_Map.ClearUserWaypoint then pcall(C_Map.ClearUserWaypoint) end
end
function DruidKit_NavClear(quiet)
  nav = nil
  if arrowF then arrowF:Hide() end
  clearNative()
  if DruidKit_RefreshMapPins then DruidKit_RefreshMapPins() end
  if DB then DB.navTarget = nil end
  if not quiet then navSay("navigation stopped.") end
end

local function buildArrow()
  arrowF = CreateFrame("Frame", "DruidKitArrow", UIParent)
  arrowF:SetSize(240, 120)
  arrowF:SetFrameStrata("HIGH"); arrowF:SetClampedToScreen(true)
  arrowF:SetMovable(true); arrowF:EnableMouse(true); arrowF:RegisterForDrag("LeftButton")
  arrowF:SetScript("OnDragStart", arrowF.StartMoving)
  arrowF:SetScript("OnDragStop", function(f)
    f:StopMovingOrSizing()
    local _, _, _, x, y = f:GetPoint()
    if DB then DB.arrowPos = { x, y } end
  end)
  arrowF:SetScript("OnMouseUp", function(_, b) if b == "RightButton" then DruidKit_NavClear() end end)
  local pos = DB and DB.arrowPos
  arrowF:SetPoint("CENTER", UIParent, "CENTER", pos and pos[1] or 0, pos and pos[2] or 200)
  arrowF.tex = arrowF:CreateTexture(nil, "ARTWORK")
  arrowF.tex:SetSize(64, 64); arrowF.tex:SetPoint("TOP", 0, 0)
  arrowF.tex:SetTexture("Interface\\Minimap\\MinimapArrow")
  arrowF.name = arrowF:CreateFontString(nil, "OVERLAY")
  arrowF.name:SetFont("Fonts\\FRIZQT__.TTF", 15, "OUTLINE"); arrowF.name:SetPoint("TOP", arrowF.tex, "BOTTOM", 0, -2)
  arrowF.name:SetWidth(240); arrowF.name:SetWordWrap(true); arrowF.name:SetTextColor(1, 0.82, 0)
  arrowF.info = arrowF:CreateFontString(nil, "OVERLAY")
  arrowF.info:SetFont("Fonts\\FRIZQT__.TTF", 15, "OUTLINE"); arrowF.info:SetPoint("TOP", arrowF.name, "BOTTOM", 0, -2)
  arrowF.info:SetWidth(240); arrowF.info:SetTextColor(1, 1, 1)
  local acc2 = 0
  arrowF:SetScript("OnUpdate", function(f, el)
    acc2 = acc2 + el
    if acc2 < 0.05 then return end
    acc2 = 0
    pcall(DruidKit_NavUpdate)
  end)
  arrowF:Hide()
end

local function turnWord(rel)
  local d = math.deg(rel)
  local a = math.abs(d)
  if a <= 20 then return "straight ahead" end
  if a >= 150 then return "behind you: turn round" end
  local side = d > 0 and "left" or "right"
  if a <= 60 then return "bear " .. side end
  return "turn " .. side
end

function DruidKit_NavUpdate()
  if not nav then return end
  local here = C_Map.GetBestMapForUnit and C_Map.GetBestMapForUnit("player")
  local pp = here and C_Map.GetPlayerMapPosition and C_Map.GetPlayerMapPosition(here, "player")
  if not pp then
    arrowF.tex:Hide(); arrowF.info:SetText("Can't track here (indoors or in a dungeon).")
    return
  end
  local pcont, ppos = toWorld(here, pp:GetXY())
  if not pcont or pcont ~= nav.cont then
    arrowF.tex:Hide(); arrowF.info:SetText("On another continent. Take a boat or flight there.")
    return
  end
  -- Work in yards on your current map: x east, y south.
  local tx, ty = DruidKit_NavProject(nav, here)
  local px, py = pp:GetXY()
  local w, h = DruidKit_MapYards(here)
  if not (tx and ty and w) then arrowF.tex:Hide(); arrowF.info:SetText("") return end
  local east, south = (tx - px) * w, (ty - py) * h
  local dist = math.sqrt(east * east + south * south)
  nav.dist = dist
  -- Not getting closer for a while (a wall, a cliff, the wrong side of a river): say so.
  local now = GetTime and GetTime() or 0
  if not nav.best or dist < nav.best - 10 then nav.best, nav.bestT = dist, now end
  local stuck = dist > 40 and nav.bestT and (now - nav.bestT) > 30
  if stuck and not nav.stuckSaid then
    nav.stuckSaid = true
    if DruidKit_OnNavStuck then pcall(DruidKit_OnNavStuck, nav.label, dist) end
  elseif not stuck then
    nav.stuckSaid = nil
  end
  if dist < 12 then
    -- Clear first: the step tracker may set the next waypoint (a via chain) from OnArrive.
    local label = nav.label
    navSay("you've arrived: " .. label .. ".")
    DruidKit_NavClear(true)
    if DruidKit_OnArrive then pcall(DruidKit_OnArrive, label) end
    return
  end
  local bearing = (math.atan2 or math.atan)(-east, -south)          -- 0 = north, positive = towards west (same as facing)
  local facing = GetPlayerFacing and GetPlayerFacing()
  arrowF.tex:Show()
  if facing then
    local rel = bearing - facing
    rel = (rel + math.pi) % (2 * math.pi) - math.pi
    arrowF.tex:SetRotation(rel)
    arrowF.info:SetText(("%d yards, %s"):format(math.floor(dist + 0.5), turnWord(rel))
      .. (stuck and "\nNot getting closer: go round, or check the map (M)" or ""))
  else
    arrowF.tex:SetRotation(bearing)
    arrowF.info:SetText(("%d yards (arrow points north-up)"):format(math.floor(dist + 0.5)))
  end
end

-- Start navigating. Returns true if the arrow could start.
function DruidKit_NavTo(mapID, x, y, label)
  if not (mapID and x and y) then return false end
  local cont, pos = toWorld(mapID, x, y)
  if not cont then return false end
  nav = { mapID = mapID, x = x, y = y, label = label or "waypoint", cont = cont, pos = pos }
  if DB then DB.navTarget = { mapID = mapID, x = x, y = y, label = nav.label } end
  if not arrowF then
    local ok = pcall(buildArrow)
    if not ok or not (arrowF and arrowF.name) then arrowF = nil; return false end
  end
  arrowF.name:SetText(nav.label)
  arrowF:Show()
  pcall(DruidKit_NavUpdate)
  if DruidKit_RefreshMapPins then DruidKit_RefreshMapPins() end
  return true
end

-- Waypoint from a zone name and map numbers (as written in the guide): DruidKit_GoTo("Westfall", 56.2, 47.6, "Gryan")
-- quiet = true: no chat line (the step tracker sets the arrow on every step).
function DruidKit_GoTo(zone, x, y, label, quiet)
  -- zone may be a name ("Loch Modan") or a map id (1432, as recorded in walked paths)
  local mapID = type(zone) == "number" and zone or (zone and findMap(zone))
    or (C_Map.GetBestMapForUnit and C_Map.GetBestMapForUnit("player"))
  if not mapID then
    if not quiet then navSay("can't find the map for " .. tostring(zone) .. ".") end
    return false
  end
  local text = ("%s (%s %.1f, %.1f)"):format(label or "Waypoint", zone or (mapName(mapID) or ""), x, y)
  if C_Map.SetUserWaypoint and UiMapPoint and UiMapPoint.CreateFromCoordinates then
    pcall(C_Map.SetUserWaypoint, UiMapPoint.CreateFromCoordinates(mapID, x / 100, y / 100))
  end
  local ok = DruidKit_NavTo(mapID, x / 100, y / 100, text)
  if quiet then return ok end
  if ok then navSay("heading to " .. text .. ". Right-click the arrow to stop.")
  else navSay(("go to %s, %.1f, %.1f."):format(zone or "", x, y)) end
  return ok
end
DruidKit_FindMap = function(zone) return zone and findMap(zone) end

-- Click anywhere on the world map: on a zone or city map a plain left-click sets a waypoint there;
-- Ctrl+click works on any map. (Plain clicks on the continent map still open zones.)
local function mapClick(canvas, button, cx, cy)
  if button ~= "LeftButton" then return false end
  local map = canvas or WorldMapFrame
  local id = map.GetMapID and map:GetMapID()
  if not id then return false end
  local info = C_Map.GetMapInfo(id)
  local zoneish = info and info.mapType and info.mapType >= 3
  local ctrl = IsControlKeyDown()
  if not (zoneish or ctrl) then return false end
  if not (cx and cy) and map.GetNormalizedCursorPosition then cx, cy = map:GetNormalizedCursorPosition() end
  if not (cx and cy) or cx < 0 or cx > 1 or cy < 0 or cy > 1 then return false end
  if not ctrl and C_Map.GetMapInfoAtPosition then
    -- clicking a city on its zone map (Stormwind on Elwynn) still opens the city
    local ok, under = pcall(C_Map.GetMapInfoAtPosition, id, cx, cy)
    if ok and under and under.mapID and under.mapID ~= id then return false end
  end
  local label = ("%s %.1f, %.1f"):format(info and info.name or "Map", cx * 100, cy * 100)
  if C_Map.SetUserWaypoint and UiMapPoint and UiMapPoint.CreateFromCoordinates then
    pcall(C_Map.SetUserWaypoint, UiMapPoint.CreateFromCoordinates(id, cx, cy))
  end
  if DruidKit_NavTo(id, cx, cy, label) then navSay("heading to " .. label .. ". Right-click the arrow to stop.") end
  return true
end
local hooked = false
local function hookMapClicks()
  if hooked or not WorldMapFrame then return end
  hooked = true
  if WorldMapFrame.AddCanvasClickHandler then
    WorldMapFrame:AddCanvasClickHandler(function(canvas, button, cx, cy)
      local ok, r = pcall(mapClick, canvas, button, cx, cy); return ok and r
    end, 100)
  elseif WorldMapFrame.ScrollContainer then
    WorldMapFrame.ScrollContainer:HookScript("OnMouseUp", function(_, button)
      if IsControlKeyDown() then pcall(mapClick, WorldMapFrame, button) end
    end)
  end
end

-- /way 52.7 53.8   or   /way Westfall 52.7 53.8   or   /way clear
local function wayCommand(msg)
  msg = (msg or ""):gsub("^%s+", ""):gsub("%s+$", "")
  if msg == "" or msg:lower() == "clear" or msg:lower() == "off" then DruidKit_NavClear() return end
  local zone, x, y, rest = msg:match("^(.-)%s*([%d%.]+)[,%s]+([%d%.]+)%s*(.*)$")
  x, y = tonumber(x), tonumber(y)
  if not (x and y) then navSay("try /way 52.7 53.8  or  /way Westfall 52.7 53.8") return end
  if zone == "" then zone = nil end
  DruidKit_GoTo(zone, x, y, rest ~= "" and rest or nil)
end
local function slashTaken(cmd)
  for key in pairs(SlashCmdList or {}) do
    for i = 1, 9 do
      local v = _G["SLASH_" .. key .. i]
      if v == nil then break end
      if type(v) == "string" and v:lower() == cmd then return true end
    end
  end
  return false
end
SLASH_DRUIDKITWAY1 = "/dkway"
if SlashCmdList then SlashCmdList.DRUIDKITWAY = wayCommand end

local navEv = CreateFrame("Frame")
navEv:RegisterEvent("PLAYER_LOGIN")
navEv:SetScript("OnEvent", function()
  -- /way too, unless another addon (TomTom) already has it. Checked once everything has loaded.
  if not slashTaken("/way") then SLASH_DRUIDKITWAY2 = "/way" end
  C_Timer.After(1, function()
    pcall(hookMapClicks)
    local t = DruidKitDB and DruidKitDB.navTarget
    if t then pcall(DruidKit_NavTo, t.mapID, t.x, t.y, t.label) end
  end)
end)
