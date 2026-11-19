-- Druid Kit: shared look for list windows (Bag check, Bank check).
-- Same frame as the guide: portrait frame, Restoration-tree backdrop, green tint, Druid orange accents.

local S = {}
DruidKitStyle = S

S.ORANGE = { 1, 0.49, 0.04 }
S.LEAF = { 0.5, 0.83, 0.36 }

local function newFrame(kind, name, parent, template)
  local ok, f = pcall(CreateFrame, kind, name, parent, template)
  if ok and f then return f end
  return CreateFrame(kind, name, parent, "BasicFrameTemplateWithInset")
end

-- A movable window with a scrolling list area. Returns the frame; f.list is where rows go.
function S.window(name, title, icon, w, h)
  local f = newFrame("Frame", name, UIParent, "PortraitFrameTemplate")
  f:SetSize(w or 400, h or 470)
  f:SetFrameStrata("DIALOG")
  f:SetMovable(true); f:EnableMouse(true); f:SetClampedToScreen(true)
  f:RegisterForDrag("LeftButton")
  f:SetScript("OnDragStart", f.StartMoving)
  f:SetScript("OnDragStop", f.StopMovingOrSizing)
  table.insert(UISpecialFrames, name)
  if f.SetPortraitToAsset then pcall(f.SetPortraitToAsset, f, icon)
  elseif f.portrait and SetPortraitToTexture then pcall(SetPortraitToTexture, f.portrait, icon) end
  if f.SetTitle then pcall(f.SetTitle, f, title)
  else
    local t = f:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    t:SetPoint("TOP", 0, -6); t:SetText(title)
  end

  f.sub = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  f.sub:SetPoint("TOPLEFT", f, "TOPLEFT", 64, -38)
  f.sub:SetPoint("RIGHT", f, "RIGHT", -16, 0)
  f.sub:SetJustifyH("LEFT")

  local inset = CreateFrame("Frame", nil, f, "InsetFrameTemplate")
  inset:SetPoint("TOPLEFT", f, "TOPLEFT", 10, -62)
  inset:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -8, 34)
  local bg = inset:CreateTexture(nil, "BACKGROUND", nil, 1)
  bg:SetPoint("TOPLEFT", 3, -3); bg:SetPoint("BOTTOMRIGHT", -3, 3)
  if bg:SetTexture("Interface\\TalentFrame\\DruidRestoration-TopLeft") == false then bg:Hide() end
  bg:SetAlpha(0.3)
  local tint = inset:CreateTexture(nil, "BACKGROUND", nil, 2)
  tint:SetAllPoints(bg)
  tint:SetColorTexture(0.03, 0.10, 0.04, 0.6)

  local scroll = CreateFrame("ScrollFrame", nil, inset, "UIPanelScrollFrameTemplate")
  scroll:SetPoint("TOPLEFT", inset, "TOPLEFT", 8, -8)
  scroll:SetPoint("BOTTOMRIGHT", inset, "BOTTOMRIGHT", -28, 8)
  local list = CreateFrame("Frame", nil, scroll)
  list:SetSize((w or 400) - 60, 10)
  scroll:SetScrollChild(list)
  f.list, f.scroll = list, scroll

  f.footer = f:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
  f.footer:SetPoint("BOTTOMLEFT", f, "BOTTOMLEFT", 16, 12)
  f.footer:SetPoint("RIGHT", f, "RIGHT", -120, 0)
  f.footer:SetJustifyH("LEFT")

  f.pool = { header = {}, item = {}, note = {} }
  f:Hide()
  return f
end

-- Always-on boxes (step window): dark forest backdrop, a faint Restoration tree, a bark-brown border, a leaf-green
-- line under the header and a Mark of the Wild crest. Text on it stays light with OUTLINE.
S.BARK = { 0.55, 0.42, 0.22 }
function S.druidPanel(f, headerH)
  if f.SetBackdrop then
    f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8x8", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
      edgeSize = 14, insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    f:SetBackdropColor(0.035, 0.065, 0.03, 0.92)
    f:SetBackdropBorderColor(S.BARK[1], S.BARK[2], S.BARK[3], 1)
  end
  local tree = f:CreateTexture(nil, "BACKGROUND", nil, 1)
  tree:SetPoint("TOPLEFT", 4, -4); tree:SetPoint("BOTTOMRIGHT", -4, 4)
  if tree:SetTexture("Interface\\TalentFrame\\DruidRestoration-TopLeft") == false then tree:Hide() end
  tree:SetAlpha(0.22)
  local crest = f:CreateTexture(nil, "ARTWORK")
  crest:SetSize(18, 18); crest:SetPoint("TOPLEFT", 8, -6)
  crest:SetTexture("Interface\\Icons\\Spell_Nature_Regeneration")
  if crest.SetTexCoord then crest:SetTexCoord(0.08, 0.92, 0.08, 0.92) end
  local line = f:CreateTexture(nil, "ARTWORK")
  line:SetHeight(1)
  line:SetPoint("TOPLEFT", 8, -(headerH or 28)); line:SetPoint("TOPRIGHT", -8, -(headerH or 28))
  line:SetColorTexture(S.LEAF[1], S.LEAF[2], S.LEAF[3], 0.55)
  f.tree, f.crest, f.leafLine = tree, crest, line
  return f
end

-- Reading boxes (quest lore): parchment like the game's quest text, dark ink, quest-title font, bark border.
-- Dark ink on parchment has more contrast than light text with an outline, so no OUTLINE here (UI_STYLE).
S.INK = { 0.20, 0.12, 0.05 }
S.INK_HEAD = { 0.36, 0.20, 0.04 }
function S.parchment(f)
  if f.SetBackdrop then
    f:SetBackdrop({ bgFile = "Interface\\Buttons\\WHITE8x8", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
      edgeSize = 14, insets = { left = 3, right = 3, top = 3, bottom = 3 } })
    f:SetBackdropColor(0.86, 0.78, 0.61, 0.97)
    f:SetBackdropBorderColor(S.BARK[1], S.BARK[2], S.BARK[3], 1)
  end
  local paper = f:CreateTexture(nil, "BACKGROUND", nil, 1)
  paper:SetPoint("TOPLEFT", 4, -4); paper:SetPoint("BOTTOMRIGHT", -4, 4)
  if paper:SetTexture("Interface\\QuestFrame\\QuestBG") == false then paper:Hide() end
  if paper.SetTexCoord then paper:SetTexCoord(0, 0.58, 0, 0.66) end
  f.paper = paper
  return f
end
function S.ink(parent, size, title, width)
  local t = parent:CreateFontString(nil, "OVERLAY")
  t:SetFont(title and "Fonts\\MORPHEUS.TTF" or "Fonts\\FRIZQT__.TTF", size, "")
  local c = title and S.INK_HEAD or S.INK
  t:SetTextColor(c[1], c[2], c[3])
  if t.SetShadowColor then t:SetShadowColor(0, 0, 0, 0) end
  t:SetJustifyH("LEFT"); t:SetJustifyV("TOP")
  if width then t:SetWidth(width) end
  if t.SetWordWrap then t:SetWordWrap(true) end
  return t
end

-- Layout helper: call begin(), then header/item/note in order, then finish().
function S.begin(f)
  f.y = -4
  f.used = { header = 0, item = 0, note = 0 }
  f.stripe = false
end

local function take(f, kind, make)
  f.used[kind] = f.used[kind] + 1
  local p = f.pool[kind][f.used[kind]]
  if not p then p = make(); f.pool[kind][f.used[kind]] = p end
  p:ClearAllPoints()
  p:SetPoint("TOPLEFT", f.list, "TOPLEFT", 0, f.y)
  p:SetPoint("RIGHT", f.list, "RIGHT", 0, 0)
  p:Show()
  return p
end

-- Section title with an icon, a count on the right and an orange rule underneath.
function S.header(f, text, icon, count, btnText, onClick)
  if f.used.header > 0 or f.used.item > 0 then f.y = f.y - 10 end
  local h = take(f, "header", function()
    local h = CreateFrame("Frame", nil, f.list)
    h:SetHeight(26)
    h.icon = h:CreateTexture(nil, "ARTWORK"); h.icon:SetSize(18, 18); h.icon:SetPoint("LEFT", 2, 2)
    h.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    h.text = h:CreateFontString(nil, "OVERLAY", "GameFontNormal")
    h.text:SetPoint("LEFT", h.icon, "RIGHT", 8, 0)
    h.count = h:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    h.count:SetPoint("LEFT", h.text, "RIGHT", 6, 0)
    h.rule = h:CreateTexture(nil, "ARTWORK")
    h.rule:SetHeight(1)
    h.rule:SetPoint("BOTTOMLEFT", 0, 0); h.rule:SetPoint("BOTTOMRIGHT", 0, 0)
    h.rule:SetColorTexture(S.ORANGE[1], S.ORANGE[2], S.ORANGE[3], 0.45)
    h.btn = CreateFrame("Button", nil, h, "UIPanelButtonTemplate")
    h.btn:SetSize(72, 20); h.btn:SetPoint("RIGHT", -2, 2)
    return h
  end)
  h.icon:SetTexture(icon)
  h.text:SetText(text)
  h.count:SetText(count and count > 0 and ("(" .. count .. ")") or "")
  if btnText then h.btn:SetText(btnText); h.btn:SetScript("OnClick", onClick); h.btn:Show() else h.btn:Hide() end
  f.y = f.y - 30
  f.stripe = false
  return h
end

-- An item card: icon with quality border, coloured name, a grey reason line, optional button.
function S.item(f, link, icon, quality, title, detail, btnText, onClick)
  local r = take(f, "item", function()
    local r = CreateFrame("Button", nil, f.list)
    r:SetHeight(38)
    r.bg = r:CreateTexture(nil, "BACKGROUND"); r.bg:SetAllPoints()
    r.hl = r:CreateTexture(nil, "HIGHLIGHT"); r.hl:SetAllPoints(); r.hl:SetColorTexture(S.LEAF[1], S.LEAF[2], S.LEAF[3], 0.12)
    r.border = r:CreateTexture(nil, "ARTWORK", nil, 1); r.border:SetSize(30, 30); r.border:SetPoint("LEFT", 6, 0)
    r.icon = r:CreateTexture(nil, "ARTWORK", nil, 2); r.icon:SetSize(28, 28); r.icon:SetPoint("CENTER", r.border)
    r.icon:SetTexCoord(0.08, 0.92, 0.08, 0.92)
    r.name = r:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    r.name:SetPoint("TOPLEFT", r.border, "TOPRIGHT", 10, -1)
    r.name:SetPoint("RIGHT", r, "RIGHT", -84, 0); r.name:SetJustifyH("LEFT"); r.name:SetWordWrap(false)
    r.detail = r:CreateFontString(nil, "OVERLAY", "GameFontDisableSmall")
    r.detail:SetPoint("BOTTOMLEFT", r.border, "BOTTOMRIGHT", 10, 1)
    r.detail:SetPoint("RIGHT", r, "RIGHT", -84, 0); r.detail:SetJustifyH("LEFT"); r.detail:SetWordWrap(false)
    r.btn = CreateFrame("Button", nil, r, "UIPanelButtonTemplate")
    r.btn:SetSize(70, 22); r.btn:SetPoint("RIGHT", -6, 0)
    r:SetScript("OnEnter", function(s)
      if s.link then GameTooltip:SetOwner(s, "ANCHOR_LEFT"); GameTooltip:SetHyperlink(s.link); GameTooltip:Show() end
    end)
    r:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return r
  end)
  f.stripe = not f.stripe
  r.bg:SetColorTexture(1, 1, 1, f.stripe and 0.04 or 0)
  r.link = link
  r.icon:SetTexture(icon or "Interface\\Icons\\INV_Misc_QuestionMark")
  local c = (ITEM_QUALITY_COLORS and ITEM_QUALITY_COLORS[quality or 1]) or { r = 1, g = 1, b = 1 }
  r.border:SetColorTexture(c.r, c.g, c.b, 0.9)
  r.name:SetText(title)
  r.name:SetTextColor(c.r, c.g, c.b)
  r.detail:SetText(detail or "")
  if btnText then r.btn:SetText(btnText); r.btn:SetScript("OnClick", onClick); r.btn:Show() else r.btn:Hide() end
  f.y = f.y - 40
  return r
end

-- A quiet line of text (empty states, tips).
function S.note(f, text)
  local n = take(f, "note", function()
    local n = CreateFrame("Frame", nil, f.list)
    n:SetHeight(20)
    n.text = n:CreateFontString(nil, "OVERLAY", "GameFontDisable")
    n.text:SetPoint("TOPLEFT", 8, -2); n.text:SetPoint("RIGHT", -6, 0)
    n.text:SetJustifyH("LEFT"); n.text:SetWordWrap(true)
    return n
  end)
  n.text:SetText(text)
  local h = math.max(18, (n.text:GetStringHeight() or 14) + 6)
  n:SetHeight(h)
  f.y = f.y - h
  return n
end

function S.finish(f)
  for kind, list in pairs(f.pool) do
    for i = f.used[kind] + 1, #list do list[i]:Hide() end
  end
  f.list:SetHeight(-f.y + 8)
end

-- ---------------------------------------------------------------------------------------------
-- Key map: every key you have, read live from the game (bindings and what sits on each button),
-- per bar: forms, caster, Bear, Cat, Prowl, the two bottom bars, and Druid Kit's own keys.
-- Open with /dk keymap or the Keys button on the step window.
-- ---------------------------------------------------------------------------------------------
local function kmSafe(fn, ...)
  if type(fn) ~= "function" then return end
  local ok, a, b, c, d = pcall(fn, ...)
  if ok then return a, b, c, d end
end

local function keyText(binding)
  local k = GetBindingKey and kmSafe(GetBindingKey, binding)
  if not k then return nil end
  return (k:gsub("META%-", "Cmd+"):gsub("CTRL%-", "Ctrl+"):gsub("ALT%-", "Alt+"):gsub("SHIFT%-", "Shift+"))
end

local function slotAction(slot)
  local has = (C_ActionBar and C_ActionBar.HasAction and kmSafe(C_ActionBar.HasAction, slot))
    or (HasAction and kmSafe(HasAction, slot))
  if not has then return nil end
  local kind, id
  if C_ActionBar and C_ActionBar.GetActionInfo then kind, id = kmSafe(C_ActionBar.GetActionInfo, slot) end
  if not kind and GetActionInfo then kind, id = kmSafe(GetActionInfo, slot) end
  if kind == "spell" and id then
    return (C_Spell and C_Spell.GetSpellName and kmSafe(C_Spell.GetSpellName, id)) or (GetSpellInfo and kmSafe(GetSpellInfo, id))
  elseif kind == "item" and id then
    return (C_Item and C_Item.GetItemNameByID and kmSafe(C_Item.GetItemNameByID, id)) or (GetItemInfo and kmSafe(GetItemInfo, id))
  elseif kind == "macro" and id then
    local name = GetMacroInfo and kmSafe(GetMacroInfo, id)
    if name and name:find("^DK ") then return name:sub(4) .. " (keeps auto attack on)" end
    return name and ("macro " .. name)
  end
  return kind
end

-- Bars: first action slot, binding prefix for its 12 keys, and when it is active.
local KM_BARS = {
  { "Caster (no form)", 1, "ACTIONBUTTON" },
  { "Bear Form", 97, "ACTIONBUTTON" },
  { "Cat Form", 73, "ACTIONBUTTON" },
  { "Cat Form, prowling", 85, "ACTIONBUTTON" },
  { "Bottom left bar", 61, "MULTIACTIONBAR1BUTTON" },
  { "Bottom right bar", 49, "MULTIACTIONBAR2BUTTON" },
}
local KM_ADDON = { "DRUIDKIT_TOGGLEGUIDE", "DRUIDKIT_STEPS", "DRUIDKIT_BAGS", "DRUIDKIT_GOTO", "DRUIDKIT_TOGGLEMODE",
  "DRUIDKIT_TAB1", "TOGGLEAUTORUN" }

-- The key map as plain data (also what the test checks): { {title, { {key, what}, ... }}, ... }
function DruidKit_KeymapData()
  local out = {}
  local forms = {}
  for i = 1, ((GetNumShapeshiftForms and kmSafe(GetNumShapeshiftForms)) or 10) do
    local r = { kmSafe(GetShapeshiftFormInfo, i) }
    local name = type(r[2]) == "string" and r[2] or nil
    if not name and type(r[4]) == "number" then
      name = (C_Spell and C_Spell.GetSpellName and kmSafe(C_Spell.GetSpellName, r[4])) or (GetSpellInfo and kmSafe(GetSpellInfo, r[4]))
    end
    if name then table.insert(forms, { keyText("SHAPESHIFTBUTTON" .. i) or "no key", name, r[1] }) end
  end
  table.insert(out, { "Forms (shapeshift)", forms })
  for _, b in ipairs(KM_BARS) do
    local rows = {}
    for i = 1, 12 do
      local slot = b[2] + i - 1
      local what = slotAction(slot)
      local icon = GetActionTexture and kmSafe(GetActionTexture, slot)
      if what then table.insert(rows, { keyText(b[3] .. i) or "no key (click)", what, icon }) end
    end
    if #rows > 0 then table.insert(out, { b[1], rows }) end
  end
  local addon = {}
  for _, bind in ipairs(KM_ADDON) do
    local label = _G["BINDING_NAME_" .. bind] or (bind == "TOGGLEAUTORUN" and "Autorun") or bind
    if bind == "DRUIDKIT_TAB1" then label = "Guide tabs (Alt+1 to Alt+8)" end
    table.insert(addon, { keyText(bind) or "no key", label, "Interface\\Icons\\INV_Misc_Key_03" })
  end
  table.insert(out, { "Druid Kit and movement", addon })
  return out
end

local keymapWin
function DruidKit_ShowKeymap()
  keymapWin = keymapWin or S.window("DruidKitKeymap", "Your keys", "Interface\\Icons\\INV_Misc_Key_03", 420, 520)
  if keymapWin:IsShown() then keymapWin:Hide(); return end
  S.begin(keymapWin)
  keymapWin.sub:SetText("Read live from your bindings and bars. Form bars use the same keys 1 to = while you're in that form.")
  for _, sec in ipairs(DruidKit_KeymapData()) do
    S.header(keymapWin, sec[1], "Interface\\Icons\\INV_Misc_Key_03", #sec[2])
    for _, row in ipairs(sec[2]) do S.item(keymapWin, nil, row[3], 1, row[1] .. "   " .. row[2], nil) end
  end
  keymapWin.footer:SetText("/dk keymap or the Keys button opens this. /dk newspells fills empty keys.")
  S.finish(keymapWin)
  keymapWin:Show()
end
